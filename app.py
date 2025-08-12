import streamlit as st
import pyodbc
import pandas as pd

from mssql_utils.db import get_tables, get_columns, get_sample_data
from mssql_utils.query_builder import build_query
from mssql_utils.excel import dataframe_to_excel_files

st.set_page_config(page_title="MS SQL Data Builder", layout="wide")
st.title("MS SQL Data Builder")

# --- Connection section ---
with st.sidebar:
    st.header("Connection")
    server = st.text_input("Server")
    database = st.text_input("Database")
    username = st.text_input("User")
    password = st.text_input("Password", type="password")
    use_trusted = st.checkbox("Trusted connection")
    connect_btn = st.button("Connect")

if "conn" not in st.session_state:
    st.session_state.conn = None
if "generated_query" not in st.session_state:
    st.session_state.generated_query = ""
if "query_df" not in st.session_state:
    st.session_state.query_df = None

if connect_btn:
    try:
        base = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};"
        if use_trusted:
            conn_str = base + "Trusted_Connection=yes;"
            if username:
                conn_str += f"UID={username};"
        else:
            conn_str = base + f"UID={username};PWD={password}"
        st.session_state.conn = pyodbc.connect(conn_str)
        st.success("Connected successfully!")
    except Exception as e:
        st.error(f"Connection failed: {e}")

conn = st.session_state.conn


def run_query(query: str):
    return pd.read_sql_query(query, conn)


if conn:
    mode = st.radio("Mode", ["Builder", "Custom SQL"], horizontal=True)

    if mode == "Custom SQL":
        custom_sql = st.text_area("SQL", height=200)
        if st.button("Run Custom Query"):
            try:
                df = run_query(custom_sql)
                st.session_state.query_df = df
                st.dataframe(df)
            except Exception as e:
                st.error(f"Query failed: {e}")
    else:
        tables = get_tables(conn)
        selected_tables = st.multiselect("Tables", tables)
        selected_columns = {}
        joins = {}
        for idx, table in enumerate(selected_tables):
            st.subheader(f"Sample from {table}")
            try:
                sample_df = get_sample_data(conn, table)
                st.dataframe(sample_df)
            except Exception as e:
                st.error(f"Failed to load sample data: {e}")
            cols = get_columns(conn, table)
            selected = st.multiselect(f"Columns from {table}", cols, key=f"cols_{table}")
            selected_columns[table] = selected
            if idx > 0:
                join_with = st.selectbox(
                    f"Join {table} with", selected_tables[:idx], key=f"join_with_{table}"
                )
                join_type = st.selectbox(
                    f"Join type for {table}", ["INNER", "LEFT", "RIGHT"], key=f"join_type_{table}"
                )
                left_col = st.selectbox(
                    "Left column", get_columns(conn, join_with), key=f"left_{table}"
                )
                right_col = st.selectbox(
                    "Right column", cols, key=f"right_{table}"
                )
                joins[table] = {
                    "type": join_type,
                    "left_table": join_with,
                    "left_column": left_col,
                    "right_column": right_col,
                }
        if st.button("Generate SQL"):
            st.session_state.generated_query = build_query(
                selected_tables, selected_columns, joins
            )

if st.session_state.generated_query:
    st.code(st.session_state.generated_query, language="sql")
    if st.button("Run Query") and conn:
        try:
            df = run_query(st.session_state.generated_query)
            st.session_state.query_df = df
            st.dataframe(df)
        except Exception as e:
            st.error(f"Query failed: {e}")

if st.session_state.query_df is not None:
    st.subheader("Export")
    for filename, data in dataframe_to_excel_files(st.session_state.query_df, base_name="results"):
        st.download_button(
            label=f"Download {filename}",
            data=data,
            file_name=filename,
        )
