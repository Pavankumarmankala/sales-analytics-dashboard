# Sales Analytics Dashboard

End-to-end sales analytics pipeline built with **Python, SQL, and Power BI**: a Python ETL loads 5,000 sales orders into SQLite, a SQL analytics layer (window functions, CTEs, aggregations) produces 7 aggregated data tables, Python EDA produces 6 visualizations, and a Power BI layer (DAX measures over a star-schema model) presents the results across 4 report pages, topped by an executive KPI summary.

## Key results

- **5,000 orders** processed, totalling **$8.7M revenue**
- **7 aggregated data tables** produced from SQL (`outputs/tables/`)
- **6 EDA visualizations** produced with matplotlib (`outputs/charts/`)
- **4 Power BI report pages** driven by the DAX measures in `dax/measures.dax`
- Executive KPI summary (`outputs/kpi_summary.md`) revealing **regional performance gaps** and **discount–profitability tradeoffs** — heavily discounted orders run at a much thinner profit margin than undiscounted orders, and the weakest region is also the one that discounts most aggressively

## Architecture

```
Synthetic data generator (seeded)
        │  data/raw/sales_orders_raw.csv  (5,000 orders)
        ▼
Python ETL (pandas)  ── clean, validate, derive revenue / cost / profit
        │  data/processed/sales_orders_clean.csv
        │  data/sales_analytics.db  (SQLite, table: sales_orders)
        ▼
SQL analytics layer  ── sql/sales_queries.sql
   (CTEs, window functions: RANK, LAG, running SUM, rolling AVG)
        │  outputs/tables/*.csv  (7 aggregated tables)
        ▼
EDA (matplotlib)  ── outputs/charts/*.png  (6 charts)
Executive KPI summary  ── outputs/kpi_summary.md
        ▼
Power BI layer  ── dax/measures.dax + model described below
   (4 report pages, DAX measures, star schema)
```

## Power BI report (4 pages)

> **Note:** No `.pbix` file is included in this repository. The Power BI layer is represented by [`dax/measures.dax`](dax/measures.dax) — the full set of DAX measures the report uses — together with the data-model description below. The measures can be pasted into Power BI Desktop over a model built from the cleaned `sales_orders` table / aggregated CSVs.

**Data model (star schema):**

- `FactSales` — one row per order line: `order_id`, `order_date`, `customer_id`, `customer_segment`, `region`, `product`, `category`, `units`, `unit_price`, `unit_cost`, `discount`, `gross_amount`, `discount_amount`, `revenue`, `total_cost`, `profit`, `order_month`
- `DimDate` — calendar table keyed on `order_date`, marked as the date table for the time-intelligence measures (`Revenue YTD`, `Revenue MoM Growth %`)
- Relationship: `FactSales[order_date]` → `DimDate[Date]` (many-to-one). Region, category and segment are attributes on `FactSales` in this model.

**Report pages:**

1. **Executive Summary** — KPI cards (Total Revenue, Total Orders, Average Order Value, Profit Margin %), monthly revenue trend, and the headline findings: regional performance gap and discount–profitability tradeoff.
2. **Regional Performance** — revenue, margin and average discount by region (North / South / East / West), revenue share, and region ranking, exposing the gap between the strongest and weakest regions.
3. **Product & Category Analysis** — revenue share by category, top products overall and top 3 products per category, units sold and category margins.
4. **Discount & Profitability** — discount bands vs profit margin, discount vs order profit scatter, segment breakdown (Consumer / Small Business / Corporate / Enterprise) and month-over-month revenue growth.

## The 7 aggregated tables

| Table | Contents |
|---|---|
| `revenue_by_region.csv` | Revenue, profit, margin, revenue share and rank per region |
| `revenue_by_category.csv` | Revenue, profit, margin and share per category |
| `revenue_by_month.csv` | Monthly revenue, running total, MoM growth % (LAG window) |
| `top_products.csv` | Top 3 products per category (RANK partitioned by category) |
| `discount_bands_profit.csv` | Orders, revenue and margin by discount band |
| `customer_segments.csv` | Orders, customers, revenue and AOV per customer segment |
| `daily_sales.csv` | Daily revenue with running total and 7-day rolling average |

## The 6 EDA visualizations

1. `revenue_trend.png` — monthly revenue trend
2. `region_comparison.png` — revenue by region
3. `category_share.png` — revenue share by category (donut)
4. `discount_vs_profit.png` — discount vs order profit (scatter)
5. `monthly_seasonality.png` — orders by month (seasonality)
6. `top_products.png` — top 10 products by revenue

## Tech stack

- **Python** (pandas) — data generation and ETL
- **SQL (SQLite)** — analytics layer: CTEs, window functions, aggregations
- **matplotlib** — EDA visualizations
- **Power BI / DAX** — report layer (measures in `dax/measures.dax`; see note above)

## Setup & run

```bash
pip install -r requirements.txt

python src/generate_data.py     # 5,000 synthetic orders -> data/raw/
python src/etl.py               # clean + load into SQLite -> data/sales_analytics.db
python src/run_aggregations.py  # run sql/sales_queries.sql -> outputs/tables/ (7 CSVs)
python src/eda_visualizations.py  # -> outputs/charts/ (6 PNGs)
python src/kpi_summary.py       # -> outputs/kpi_summary.md
```

The data generator is seeded (`seed = 42`), so every run reproduces the same 5,000 orders and the same results. Generated raw/processed data and the SQLite database are git-ignored and can be rebuilt at any time with the commands above.

## Project structure

```
sales-analytics-dashboard/
├── README.md
├── requirements.txt
├── src/
│   ├── generate_data.py        # seeded synthetic data (5,000 orders)
│   ├── etl.py                  # pandas ETL -> SQLite
│   ├── run_aggregations.py     # executes the SQL file -> 7 tables
│   ├── eda_visualizations.py   # matplotlib -> 6 charts
│   └── kpi_summary.py          # executive KPI summary
├── sql/
│   └── sales_queries.sql       # CTEs, window functions, aggregations
├── dax/
│   └── measures.dax            # Power BI DAX measures
├── data/                       # generated (git-ignored)
└── outputs/
    ├── tables/                 # 7 aggregated CSVs
    ├── charts/                 # 6 PNG charts
    └── kpi_summary.md          # executive KPI summary
```
