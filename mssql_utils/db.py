import pandas as pd


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
