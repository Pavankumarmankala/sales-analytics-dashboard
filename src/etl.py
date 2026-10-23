"""ETL: load the raw synthetic orders, clean them with pandas, derive the
sales measures, and load the result into a local SQLite database so the SQL
in ``sql/sales_queries.sql`` genuinely runs against a real table.

Run after ``src/generate_data.py``:
    python src/etl.py

Outputs:
    data/processed/sales_orders_clean.csv
    data/sales_analytics.db   (table: sales_orders)
"""

import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "sales_orders_raw.csv"
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "sales_orders_clean.csv"
DB_PATH = PROJECT_ROOT / "data" / "sales_analytics.db"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise and validate the raw orders."""
    df = df.copy()

    # Types
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for col in ["region", "product", "category", "customer_segment"]:
        df[col] = df[col].astype(str).str.strip()
    for col in ["units", "unit_price", "unit_cost", "discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Validation / cleaning rules
    df = df.dropna(subset=["order_date", "units", "unit_price"])
    df = df.drop_duplicates(subset=["order_id"])
    df = df[(df["units"] > 0) & (df["unit_price"] > 0)]
    df = df[(df["discount"] >= 0) & (df["discount"] < 1)]

    # Derived measures
    df["gross_amount"] = (df["units"] * df["unit_price"]).round(2)
    df["discount_amount"] = (df["gross_amount"] * df["discount"]).round(2)
    df["revenue"] = (df["gross_amount"] - df["discount_amount"]).round(2)
    df["total_cost"] = (df["units"] * df["unit_cost"]).round(2)
    df["profit"] = (df["revenue"] - df["total_cost"]).round(2)

    # Calendar helpers used by the SQL and the dashboards
    df["order_month"] = df["order_date"].dt.strftime("%Y-%m")
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    return df.sort_values(["order_date", "order_id"]).reset_index(drop=True)


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_PATH} not found — run `python src/generate_data.py` first."
        )

    raw = pd.read_csv(RAW_PATH)
    df = clean(raw)

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("sales_orders", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX idx_sales_region ON sales_orders (region)")
        conn.execute("CREATE INDEX idx_sales_month ON sales_orders (order_month)")

    print(f"Raw rows:      {len(raw):,}")
    print(f"Clean rows:    {len(df):,}")
    print(f"Total revenue: ${df['revenue'].sum():,.2f}")
    print(f"Total profit:  ${df['profit'].sum():,.2f}")
    print(f"Clean CSV:     {CLEAN_PATH}")
    print(f"SQLite DB:     {DB_PATH} (table: sales_orders)")


if __name__ == "__main__":
    main()
