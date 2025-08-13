import streamlit as st
import pyodbc
import pandas as pd
import json
from pathlib import Path

from mssql_utils.db import get_tables, get_columns, get_sample_data
from mssql_utils.query_builder import build_query
from mssql_utils.excel import dataframe_to_excel_files


STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)
LAST_CONN_FILE = STORAGE_DIR / "last_connection.json"
SAVED_QUERIES_FILE = STORAGE_DIR / "saved_queries.json"


def load_last_connection():
    if LAST_CONN_FILE.exists():
        return json.loads(LAST_CONN_FILE.read_text())
    return None


def save_last_connection(data):
    LAST_CONN_FILE.write_text(json.dumps(data))


def load_saved_queries():
    if SAVED_QUERIES_FILE.exists():
        return json.loads(SAVED_QUERIES_FILE.read_text())
    return {}


def save_query(name, query):
    queries = load_saved_queries()
    queries[name] = query
    SAVED_QUERIES_FILE.write_text(json.dumps(queries, ensure_ascii=False, indent=2))


st.set_page_config(page_title="Конструктор данных MS SQL", layout="wide")
st.title("Конструктор данных MS SQL")

# --- Connection section ---
last_conn = load_last_connection()
with st.sidebar:
    st.header("Подключение")
    server = st.text_input("Сервер", value=(last_conn.get("server") if last_conn else ""))
    database = st.text_input("База данных", value=(last_conn.get("database") if last_conn else ""))
    username = st.text_input("Пользователь", value=(last_conn.get("username") if last_conn else ""))
    password = st.text_input("Пароль", type="password", value=(last_conn.get("password") if last_conn else ""))
    use_trusted = st.checkbox(
        "Доверенное соединение", value=(last_conn.get("use_trusted") if last_conn else False)
    )
    connect_btn = st.button("Подключиться")
    connect_last_btn = False
    if last_conn:
        connect_last_btn = st.button("Подключиться к последнему")

if "conn" not in st.session_state:
    st.session_state.conn = None
if "generated_query" not in st.session_state:
    st.session_state.generated_query = ""
if "query_df" not in st.session_state:
    st.session_state.query_df = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


def make_connection(params):
    base = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={params['server']};DATABASE={params['database']};"
    if params["use_trusted"]:
        conn_str = base + "Trusted_Connection=yes;"
        if params.get("username"):
            conn_str += f"UID={params['username']};"
    else:
        conn_str = base + f"UID={params['username']};PWD={params['password']}"
    return pyodbc.connect(conn_str)


if connect_btn:
    params = {
        "server": server,
        "database": database,
        "username": username,
        "password": password,
        "use_trusted": use_trusted,
    }
    try:
        st.session_state.conn = make_connection(params)
        st.success("Подключение успешно!")
        save_last_connection(params)
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")
elif connect_last_btn and last_conn:
    try:
        st.session_state.conn = make_connection(last_conn)
        st.success("Подключено к последнему соединению!")
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")

conn = st.session_state.conn


def run_query(query: str):
    return pd.read_sql_query(query, conn)


if conn:
    mode = st.radio(
        "Режим", ["Конструктор", "Произвольный SQL", "Личный кабинет"], horizontal=True
    )

    if mode == "Произвольный SQL":
        custom_sql = st.text_area("SQL", height=200)
        if st.button("Выполнить произвольный запрос"):
            try:
                df = run_query(custom_sql)
                st.session_state.query_df = df
                st.session_state.last_query = custom_sql
                st.dataframe(df)
            except Exception as e:
                st.error(f"Ошибка выполнения: {e}")
    elif mode == "Личный кабинет":
        saved_queries = load_saved_queries()
        if saved_queries:
            query_name = st.selectbox("Сохраненные запросы", list(saved_queries.keys()))
            if st.button("Выполнить выбранный запрос"):
                try:
                    query = saved_queries[query_name]
                    df = run_query(query)
                    st.session_state.query_df = df
                    st.session_state.last_query = query
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Ошибка выполнения: {e}")
        else:
            st.info("Нет сохраненных запросов")
    else:
        tables = get_tables(conn)
        selected_tables = st.multiselect("Таблицы", tables)
        selected_columns = {}
        joins = {}
        for idx, table in enumerate(selected_tables):
            st.subheader(f"Образец данных {table}")
            try:
                sample_df = get_sample_data(conn, table)
                st.dataframe(sample_df)
            except Exception as e:
                st.error(f"Не удалось загрузить данные: {e}")
            cols = get_columns(conn, table)
            selected = st.multiselect(
                f"Поля из {table}", cols, key=f"cols_{table}"
            )
            selected_columns[table] = selected
            if idx > 0:
                join_with = st.selectbox(
                    f"Соединить {table} с", selected_tables[:idx], key=f"join_with_{table}"
                )
                join_type = st.selectbox(
                    f"Тип соединения для {table}", ["INNER", "LEFT", "RIGHT"], key=f"join_type_{table}"
                )
                if f"cond_count_{table}" not in st.session_state:
                    st.session_state[f"cond_count_{table}"] = 1
                if st.button("Добавить условие", key=f"add_cond_{table}"):
                    st.session_state[f"cond_count_{table}"] += 1
                left_cols = get_columns(conn, join_with)
                conds = []
                for c_idx in range(st.session_state[f"cond_count_{table}"]):
                    left_col = st.selectbox(
                        f"Левая колонка {c_idx + 1}", left_cols, key=f"left_{table}_{c_idx}"
                    )
                    right_col = st.selectbox(
                        f"Правая колонка {c_idx + 1}", cols, key=f"right_{table}_{c_idx}"
                    )
                    conds.append(
                        {
                            "left_column": left_col,
                            "right_column": right_col,
                        }
                    )
                joins[table] = {
                    "type": join_type,
                    "left_table": join_with,
                    "conditions": conds,
                }
        if st.button("Сгенерировать SQL"):
            st.session_state.generated_query = build_query(
                selected_tables, selected_columns, joins
            )

if st.session_state.generated_query:
    st.code(st.session_state.generated_query, language="sql")
    if st.button("Выполнить запрос") and conn:
        try:
            df = run_query(st.session_state.generated_query)
            st.session_state.query_df = df
            st.session_state.last_query = st.session_state.generated_query
            st.dataframe(df)
        except Exception as e:
            st.error(f"Ошибка выполнения: {e}")

if st.session_state.query_df is not None:
    st.subheader("Экспорт")
    for filename, data in dataframe_to_excel_files(
        st.session_state.query_df, base_name="results"
    ):
        st.download_button(
            label=f"Скачать {filename}",
            data=data,
            file_name=filename,
        )
    if st.session_state.last_query:
        st.subheader("Сохранить запрос")
        save_name = st.text_input("Название запроса")
        if st.button("Сохранить запрос") and save_name:
            save_query(save_name, st.session_state.last_query)
            st.success("Запрос сохранен")

