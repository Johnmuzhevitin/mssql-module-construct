from io import BytesIO
import pandas as pd

MAX_ROWS_PER_FILE = 1000000


def dataframe_to_excel_files(df: pd.DataFrame, base_name: str = "data", max_rows: int = MAX_ROWS_PER_FILE):
    files = []
    total_rows = len(df)
    for i in range(0, total_rows, max_rows):
        chunk = df.iloc[i:i + max_rows]
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            chunk.to_excel(writer, index=False)
        buffer.seek(0)
        suffix = "" if total_rows <= max_rows else f"_{i // max_rows + 1}"
        files.append((f"{base_name}{suffix}.xlsx", buffer.getvalue()))
    return files
