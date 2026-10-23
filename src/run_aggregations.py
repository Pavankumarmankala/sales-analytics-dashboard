"""Run the SQL analytics layer and write the 7 aggregated data tables.

Parses ``sql/sales_queries.sql``: every query is preceded by an
``-- output: <file>.csv`` marker. Each query is executed against the
SQLite database built by ``src/etl.py`` and its result is written to
``outputs/tables/<file>.csv`` — exactly 7 aggregated tables.

Run after ``src/etl.py``:
    python src/run_aggregations.py
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "sales_analytics.db"
SQL_PATH = PROJECT_ROOT / "sql" / "sales_queries.sql"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"

OUTPUT_MARKER = re.compile(r"^--\s*output:\s*(\S+\.csv)\s*$", re.MULTILINE)


def parse_queries(sql_text: str) -> list[tuple[str, str]]:
    """Split the .sql file into (output filename, query) pairs."""
    parts = OUTPUT_MARKER.split(sql_text)
    # parts = [preamble, filename1, body1, filename2, body2, ...]
    pairs = []
    for i in range(1, len(parts), 2):
        filename = parts[i]
        body = parts[i + 1]
        # The query is the first statement in the body; the following
        # "-- output:" block belongs to the next query and has already
        # been split off, so take everything up to the first semicolon.
        query = body.split(";")[0].strip()
        # Drop leading comment lines so sqlite gets a clean statement.
        lines = [ln for ln in query.splitlines() if not ln.strip().startswith("--")]
        pairs.append((filename, "\n".join(lines).strip()))
    return pairs


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"{DB_PATH} not found — run `python src/etl.py` first."
        )

    queries = parse_queries(SQL_PATH.read_text(encoding="utf-8"))
    if len(queries) != 7:
        raise ValueError(f"Expected 7 queries in {SQL_PATH}, found {len(queries)}")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for filename, query in queries:
            df = pd.read_sql_query(query, conn)
            out_path = TABLES_DIR / filename
            df.to_csv(out_path, index=False)
            print(f"{filename:<28} {len(df):>4} rows")

    print(f"\nWrote {len(queries)} aggregated tables to {TABLES_DIR}")


if __name__ == "__main__":
    main()
