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
    connect_btn = st.button('Connect')

if 'conn' not in st.session_state:
    st.session_state.conn = None

if connect_btn:
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        st.session_state.conn = pyodbc.connect(conn_str)
        st.success('Connected successfully!')
    except Exception as e:
        st.error(f'Connection failed: {e}')

conn = st.session_state.conn

def get_tables(connection):
    query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
    cursor = connection.cursor()
    cursor.execute(query)
    return sorted(row[0] for row in cursor.fetchall())

def get_columns(connection, table):
    query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}'"
    cursor = connection.cursor()
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]

def get_foreign_key_map(connection):
    query = """
        SELECT
            tp.name AS parent_table,
            cp.name AS parent_column,
            tr.name AS referenced_table,
            cr.name AS referenced_column
        FROM sys.foreign_key_columns fkc
        INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
        INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
    """
    cursor = connection.cursor()
    cursor.execute(query)
    relations = defaultdict(list)
    for row in cursor.fetchall():
        parent_table, parent_column, ref_table, ref_column = row
        relations[parent_table].append((ref_table, parent_column, ref_column))
        relations[ref_table].append((parent_table, ref_column, parent_column))
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
        return ''
    start = selected_tables[0]
    select_parts = [f"{start}.{col}" for col in selected_columns[start]]
    join_clauses = []
    used_tables = {start}
    for table in selected_tables[1:]:
        path = find_join_path(start, table, relations)
        if not path:
            join_clauses.append(f"CROSS JOIN {table}")
        else:
            for lt, lcol, rt, rcol in path:
                if rt not in used_tables:
                    join_clauses.append(f"LEFT JOIN {rt} ON {lt}.{lcol} = {rt}.{rcol}")
                    used_tables.add(rt)
                elif lt not in used_tables:
                    join_clauses.append(f"LEFT JOIN {lt} ON {rt}.{rcol} = {lt}.{lcol}")
                    used_tables.add(lt)
        select_parts.extend(f"{table}.{col}" for col in selected_columns[table])
    return "SELECT " + ", ".join(select_parts) + " FROM " + start + (" " + " ".join(join_clauses) if join_clauses else '')

if conn:
    tables = get_tables(conn)
    selected_tables = st.multiselect('Tables', tables)
    selected_columns = {}
    for table in selected_tables:
        st.subheader(f'Table: {table}')
        try:
            preview_df = pd.read_sql_query(f'SELECT TOP 5 * FROM {table}', conn)
            st.dataframe(preview_df)
        except Exception as e:
            st.error(f'Preview failed: {e}')
            preview_df = pd.DataFrame()
        cols = get_columns(conn, table)
        default_selection = preview_df.columns.tolist() if not preview_df.empty else None
        selected = st.multiselect(
            f'Columns from {table}',
            cols,
            default=default_selection,
            key=f'cols_{table}'
        )
        selected_columns[table] = selected

    if st.button('Generate SQL'):
        relations = get_foreign_key_map(conn)
        query = build_query(selected_tables, selected_columns, relations)
        st.code(query, language='sql')
        if st.button('Run Query'):
            try:
                df = pd.read_sql_query(query, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f'Query failed: {e}')
