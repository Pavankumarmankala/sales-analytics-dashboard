"""Exploratory data analysis: produce exactly 6 charts with matplotlib.

Reads the cleaned sales_orders table from the SQLite database built by
``src/etl.py`` and saves PNGs to ``outputs/charts/``:

    1. revenue_trend.png        monthly revenue trend (line)
    2. region_comparison.png    revenue by region (bar)
    3. category_share.png       revenue share by category (donut)
    4. discount_vs_profit.png   discount vs order profit (scatter)
    5. monthly_seasonality.png  orders by month (bar)
    6. top_products.png         top 10 products by revenue (horizontal bar)

Run after ``src/etl.py``:
    python src/eda_visualizations.py
"""

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "sales_analytics.db"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"

COLORS = ["#2563eb", "#0ea5e9", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]


def save(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path.name}")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"{DB_PATH} not found — run `python src/etl.py` first."
        )
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM sales_orders", conn)

    # 1. Monthly revenue trend
    monthly = df.groupby("order_month")["revenue"].sum()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(monthly.index, monthly.values, marker="o", color=COLORS[0], linewidth=2)
    ax.fill_between(monthly.index, monthly.values, alpha=0.15, color=COLORS[0])
    ax.set_title("Monthly Revenue Trend (2024)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue ($)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3)
    save(fig, "revenue_trend.png")

    # 2. Revenue by region
    region = df.groupby("region")["revenue"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(region.index, region.values, color=COLORS[: len(region)])
    ax.set_title("Revenue by Region")
    ax.set_ylabel("Revenue ($)")
    for i, v in enumerate(region.values):
        ax.text(i, v, f"${v:,.0f}", ha="center", va="bottom", fontsize=9)
    save(fig, "region_comparison.png")

    # 3. Revenue share by category
    category = df.groupby("category")["revenue"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        category.values,
        labels=category.index,
        autopct="%1.1f%%",
        colors=COLORS[: len(category)],
        wedgeprops={"width": 0.45, "edgecolor": "white"},
        textprops={"fontsize": 10},
    )
    ax.set_title("Revenue Share by Category")
    save(fig, "category_share.png")

    # 4. Discount vs order profit
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df["discount"] * 100, df["profit"], alpha=0.25, s=12, color=COLORS[0])
    ax.axhline(0, color=COLORS[4], linewidth=1)
    ax.set_title("Discount vs Order Profit")
    ax.set_xlabel("Discount (%)")
    ax.set_ylabel("Profit ($)")
    ax.grid(alpha=0.3)
    save(fig, "discount_vs_profit.png")

    # 5. Monthly seasonality (order volume)
    orders_by_month = df.groupby("order_month").size()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(orders_by_month.index, orders_by_month.values, color=COLORS[1])
    ax.set_title("Orders by Month — Seasonality (2024)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Orders")
    ax.tick_params(axis="x", rotation=45)
    save(fig, "monthly_seasonality.png")

    # 6. Top 10 products by revenue
    top = (
        df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(10)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top.index[::-1], top.values[::-1], color=COLORS[3])
    ax.set_title("Top 10 Products by Revenue")
    ax.set_xlabel("Revenue ($)")
    save(fig, "top_products.png")

    print(f"\nWrote 6 charts to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
