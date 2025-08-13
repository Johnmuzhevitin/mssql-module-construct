from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import pyodbc

try:
    from core.storage import get_connection
except ImportError:  # pragma: no cover - fallback when running from source
    from ...core.storage import get_connection


class SchemaCache:
    """Cache for database schema information with TTL support."""

    def __init__(self, conn: sqlite3.Connection | None = None, ttl_hours: int = 24) -> None:
        self.conn = conn or get_connection()
        self.ttl = timedelta(hours=ttl_hours)

    # ------------------------------------------------------------------
    def get(self, name: str) -> Dict[str, Any] | None:
        """Return cached schema for ``name`` if it exists and is fresh."""

        cur = self.conn.cursor()
        cur.execute("SELECT schema FROM schema_cache WHERE name=?", (name,))
        row = cur.fetchone()
        if not row:
            return None
        payload = json.loads(row[0])
        ts = payload.get("cached_at")
        if not ts:
            return None
        cached_at = datetime.fromisoformat(ts)
        if datetime.utcnow() - cached_at > self.ttl:
            return None
        return payload.get("data")

    # ------------------------------------------------------------------
    def update(self, name: str, sql_conn: pyodbc.Connection) -> Dict[str, Any]:
        """Collect schema from ``sql_conn`` and cache under ``name``."""

        data = self._collect_schema(sql_conn)
        payload = {"cached_at": datetime.utcnow().isoformat(), "data": data}
        cur = self.conn.cursor()
        cur.execute("DELETE FROM schema_cache WHERE name=?", (name,))
        cur.execute(
            "INSERT INTO schema_cache (name, schema) VALUES (?, ?)",
            (name, json.dumps(payload)),
        )
        self.conn.commit()
        return data

    # ------------------------------------------------------------------
    def _collect_schema(self, sql_conn: pyodbc.Connection) -> Dict[str, Any]:
        """Gather tables, columns, keys and indexes from MSSQL."""

        cursor = sql_conn.cursor()

        # Tables and views
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES"
        )
        tables = [
            {
                "schema": row.TABLE_SCHEMA,
                "name": row.TABLE_NAME,
                "type": row.TABLE_TYPE,
            }
            for row in cursor.fetchall()
        ]

        # Columns
        cursor.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            """
        )
        columns = [
            {
                "schema": row.TABLE_SCHEMA,
                "table": row.TABLE_NAME,
                "name": row.COLUMN_NAME,
                "type": row.DATA_TYPE,
                "nullable": row.IS_NULLABLE == "YES",
            }
            for row in cursor.fetchall()
        ]

        # Primary keys
        cursor.execute(
            """
            SELECT KU.TABLE_SCHEMA, KU.TABLE_NAME, KU.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KU
              ON TC.CONSTRAINT_NAME = KU.CONSTRAINT_NAME
            WHERE TC.CONSTRAINT_TYPE = 'PRIMARY KEY'
            """
        )
        primary_keys = [
            {
                "schema": row.TABLE_SCHEMA,
                "table": row.TABLE_NAME,
                "column": row.COLUMN_NAME,
            }
            for row in cursor.fetchall()
        ]

        # Foreign keys
        cursor.execute(
            """
            SELECT
                sch_p.name AS parent_schema,
                tp.name AS table_name,
                cp.name AS column_name,
                sch_r.name AS ref_schema,
                tr.name AS ref_table,
                cr.name AS ref_column
            FROM sys.foreign_key_columns fkc
            INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.schemas sch_p ON tp.schema_id = sch_p.schema_id
            INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id
                AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.schemas sch_r ON tr.schema_id = sch_r.schema_id
            INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id
                AND fkc.referenced_column_id = cr.column_id
            """
        )
        foreign_keys = [
            {
                "schema": row.parent_schema,
                "table": row.table_name,
                "column": row.column_name,
                "ref_schema": row.ref_schema,
                "ref_table": row.ref_table,
                "ref_column": row.ref_column,
            }
            for row in cursor.fetchall()
        ]

        # Indexes
        cursor.execute(
            """
            SELECT s.name AS schema_name, t.name AS table_name, ind.name AS index_name, col.name AS column_name
            FROM sys.indexes ind
            INNER JOIN sys.index_columns ic ON ind.object_id = ic.object_id AND ind.index_id = ic.index_id
            INNER JOIN sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
            INNER JOIN sys.tables t ON ind.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE t.is_ms_shipped = 0 AND ind.is_hypothetical = 0
            ORDER BY s.name, t.name, ind.name, ic.key_ordinal
            """
        )
        idx_rows = cursor.fetchall()
        idx_map: Dict[Tuple[str, str, str], List[str]] = {}
        for row in idx_rows:
            key = (row.schema_name, row.table_name, row.index_name)
            idx_map.setdefault(key, []).append(row.column_name)
        indexes = [
            {
                "schema": k[0],
                "table": k[1],
                "name": k[2],
                "columns": v,
            }
            for k, v in idx_map.items()
        ]

        return {
            "tables": tables,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        }
