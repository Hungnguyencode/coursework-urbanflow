from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/analytics/urbanflow.duckdb"
)


def get_connection() -> duckdb.DuckDBPyConnection:
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(
        str(DATABASE_PATH)
    )