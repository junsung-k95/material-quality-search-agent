import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS issues (
    id TEXT PRIMARY KEY,
    product TEXT,
    component TEXT,
    issue TEXT,
    cause TEXT,
    solution TEXT,
    material_code TEXT,
    material_class TEXT,
    class_hierarchy TEXT
)
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with get_connection(db_path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()


def insert_issues(db_path: str, issues: list[dict]) -> None:
    with get_connection(db_path) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO issues VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (
                    i["id"],
                    i["product"],
                    i["component"],
                    i["issue"],
                    i["cause"],
                    i["solution"],
                    i["material_code"],
                    i["material_class"],
                    i["class_hierarchy"],
                )
                for i in issues
            ],
        )
        conn.commit()


def query_by_filter(db_path: str, filter_dict: dict) -> list[dict]:
    conditions = []
    params = []
    for k, v in filter_dict.items():
        conditions.append(f"{k} = ?")
        params.append(v)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_connection(db_path) as conn:
        rows = conn.execute(f"SELECT * FROM issues {where}", params).fetchall()
    return [dict(row) for row in rows]


def get_all(db_path: str) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM issues").fetchall()
    return [dict(row) for row in rows]
