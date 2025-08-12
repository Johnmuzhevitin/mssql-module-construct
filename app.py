import streamlit as st
import pyodbc
import pandas as pd
from collections import defaultdict, deque

st.set_page_config(page_title='MS SQL Data Builder', layout='wide')
st.title('MS SQL Data Builder')

# --- Connection section ---
with st.sidebar:
    st.header('Connection')
    server = st.text_input('Server')
    database = st.text_input('Database')
    username = st.text_input('User')
    password = st.text_input('Password', type='password')
    use_trusted = st.checkbox('Trusted connection')
    connect_btn = st.button('Connect')

if 'conn' not in st.session_state:
    st.session_state.conn = None

if connect_btn:
    try:
        base = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};'
        if use_trusted:
            conn_str = base + 'Trusted_Connection=yes;'
            if username:
                conn_str += f'UID={username};'
        else:
            conn_str = base + f'UID={username};PWD={password}'
        st.session_state.conn = pyodbc.connect(conn_str)
        st.success('Connected successfully!')
    except Exception as e:
        st.error(f'Connection failed: {e}')

conn = st.session_state.conn

def _format_table(table: str) -> str:
    """Return table name quoted with schema if present."""
    return "[" + "].[".join(table.split(".")) + "]"


def _format_column(table: str, column: str) -> str:
    """Return fully qualified column name."""
    return f"{_format_table(table)}.[{column}]"


def get_tables(connection):
    query = (
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE='BASE TABLE'"
    )
    cursor = connection.cursor()
    cursor.execute(query)
    return sorted(f"{row[0]}.{row[1]}" for row in cursor.fetchall())


def get_columns(connection, table):
    if "." in table:
        schema, table_name = table.split(".", 1)
        query = (
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA=? AND TABLE_NAME=?"
        )
        params = (schema, table_name)
    else:
        query = (
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME=?"
        )
        params = (table,)
    cursor = connection.cursor()
    cursor.execute(query, params)
    return [row[0] for row in cursor.fetchall()]


def get_sample_data(connection, table, limit=5):
    if "." in table:
        schema, table_name = table.split(".", 1)
        query = f"SELECT TOP {limit} * FROM [{schema}].[{table_name}]"
    else:
        query = f"SELECT TOP {limit} * FROM [{table}]"
    return pd.read_sql_query(query, connection)


def get_foreign_key_map(connection):
    query = """
        SELECT
            s1.name AS parent_schema,
            tp.name AS parent_table,
            cp.name AS parent_column,
            s2.name AS referenced_schema,
            tr.name AS referenced_table,
            cr.name AS referenced_column
        FROM sys.foreign_key_columns fkc
        INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
        INNER JOIN sys.schemas s1 ON tp.schema_id = s1.schema_id
        INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.schemas s2 ON tr.schema_id = s2.schema_id
        INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
    """
    cursor = connection.cursor()
    cursor.execute(query)
    relations = defaultdict(list)
    for row in cursor.fetchall():
        (
            parent_schema,
            parent_table,
            parent_column,
            ref_schema,
            ref_table,
            ref_column,
        ) = row
        parent = f"{parent_schema}.{parent_table}"
        ref = f"{ref_schema}.{ref_table}"
        relations[parent].append((ref, parent_column, ref_column))
        relations[ref].append((parent, ref_column, parent_column))
    return relations

def find_join_path(start, end, relations):
    queue = deque([(start, [])])
    visited = set()
    while queue:
        table, path = queue.popleft()
        if table == end:
            return path
        visited.add(table)
        for neighbour, left_col, right_col in relations.get(table, []):
            if neighbour not in visited:
                queue.append((neighbour, path + [(table, left_col, neighbour, right_col)]))
    return []

def build_query(selected_tables, selected_columns, relations):
    if not selected_tables:
        return ""
    start = selected_tables[0]
    select_parts = [_format_column(start, col) for col in selected_columns[start]]
    join_clauses = []
    used_tables = {start}
    for table in selected_tables[1:]:
        path = find_join_path(start, table, relations)
        if not path:
            join_clauses.append(f"CROSS JOIN {_format_table(table)}")
        else:
            for lt, lcol, rt, rcol in path:
                if rt not in used_tables:
                    join_clauses.append(
                        f"LEFT JOIN {_format_table(rt)} ON {_format_column(lt, lcol)} = {_format_column(rt, rcol)}"
                    )
                    used_tables.add(rt)
                elif lt not in used_tables:
                    join_clauses.append(
                        f"LEFT JOIN {_format_table(lt)} ON {_format_column(rt, rcol)} = {_format_column(lt, lcol)}"
                    )
                    used_tables.add(lt)
        select_parts.extend(_format_column(table, col) for col in selected_columns[table])
    return (
        "SELECT "
        + ", ".join(select_parts)
        + " FROM "
        + _format_table(start)
        + (" " + " ".join(join_clauses) if join_clauses else "")
    )

if 'generated_query' not in st.session_state:
    st.session_state.generated_query = ''

if conn:
    tables = get_tables(conn)
    selected_tables = st.multiselect('Tables', tables)
    selected_columns = {}
    for table in selected_tables:
        st.subheader(f'Sample from {table}')
        try:
            sample_df = get_sample_data(conn, table)
            st.dataframe(sample_df)
        except Exception as e:
            st.error(f'Failed to load sample data: {e}')
        cols = get_columns(conn, table)
        selected = st.multiselect(f'Columns from {table}', cols, key=f'cols_{table}')
        selected_columns[table] = selected

    if st.button('Generate SQL'):
        relations = get_foreign_key_map(conn)
        st.session_state.generated_query = build_query(selected_tables, selected_columns, relations)

if st.session_state.generated_query:
    st.code(st.session_state.generated_query, language='sql')
    if st.button('Run Query') and conn:
        try:
            df = pd.read_sql_query(st.session_state.generated_query, conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f'Query failed: {e}')
