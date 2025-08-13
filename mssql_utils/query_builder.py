
def _format_table(table: str) -> str:
    return "[" + "].[".join(table.split(".")) + "]"


def _format_column(table: str, column: str) -> str:
    return f"{_format_table(table)}.[{column}]"


def build_query(selected_tables, selected_columns, joins):
    if not selected_tables:
        return ""
    select_parts = []
    for table in selected_tables:
        select_parts.extend(
            _format_column(table, col) for col in selected_columns.get(table, [])
        )
    query = f"SELECT {', '.join(select_parts)} FROM {_format_table(selected_tables[0])}"
    for table in selected_tables[1:]:
        join = joins.get(table)
        if join:
            jt = join.get('type', 'LEFT').upper()
            lt = join.get('left_table')
            conditions = join.get('conditions', [])
            if conditions:
                cond_str = " AND ".join(
                    f"{_format_column(lt, c['left_column'])} = {_format_column(table, c['right_column'])}"
                    for c in conditions
                )
                query += f" {jt} JOIN {_format_table(table)} ON {cond_str}"
            else:
                query += f" {jt} JOIN {_format_table(table)}"
        else:
            query += f" CROSS JOIN {_format_table(table)}"
    return query
