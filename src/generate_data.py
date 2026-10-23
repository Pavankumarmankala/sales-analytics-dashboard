"""Generate the synthetic sales dataset.

Produces exactly 5,000 sales orders (seeded, deterministic) and writes them
to ``data/raw/sales_orders_raw.csv``. Field ranges are tuned so total revenue
lands near $8.7M, matching the project description.

Run:
    python src/generate_data.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
NUM_ORDERS = 5_000

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "sales_orders_raw.csv"

# (category, product, unit price in USD, unit cost as a fraction of price)
PRODUCTS = [
    ("Electronics", "Laptop Pro 14", 1299, 0.68),
    ("Electronics", "Smartphone X", 899, 0.66),
    ("Electronics", "Tablet Air", 649, 0.64),
    ("Electronics", "Monitor 27-inch", 449, 0.62),
    ("Electronics", "Wireless Headphones", 249, 0.55),
    ("Electronics", "Smartwatch Series 7", 349, 0.58),
    ("Furniture", "Standing Desk", 899, 0.60),
    ("Furniture", "Ergonomic Chair", 499, 0.58),
    ("Furniture", "Conference Table", 1199, 0.62),
    ("Furniture", "Bookshelf", 329, 0.57),
    ("Appliances", "Espresso Machine", 699, 0.61),
    ("Appliances", "Air Purifier", 399, 0.59),
    ("Appliances", "Robot Vacuum", 599, 0.63),
    ("Office", "Laser Printer", 549, 0.60),
    ("Office", "Shredder", 229, 0.54),
    ("Office", "Desk Lamp", 89, 0.50),
]
PRODUCT_WEIGHTS = [12, 14, 10, 9, 13, 10, 7, 9, 4, 5, 6, 6, 6, 5, 4, 3]

REGIONS = ["North", "South", "East", "West"]
REGION_WEIGHTS = [28, 22, 26, 24]

# Discount behaviour differs by region, which is what later surfaces as the
# regional performance gap and the discount-profitability tradeoff:
# the South discounts more heavily and earns thinner margins.
REGION_DISCOUNTS = {
    "North": ([0.00, 0.05, 0.10, 0.15, 0.20], [45, 28, 17, 7, 3]),
    "South": ([0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30], [22, 22, 24, 16, 9, 5, 2]),
    "East": ([0.00, 0.05, 0.10, 0.15, 0.20], [40, 30, 19, 8, 3]),
    "West": ([0.00, 0.05, 0.10, 0.15], [48, 30, 15, 7]),
}

SEGMENTS = ["Consumer", "Small Business", "Corporate", "Enterprise"]
SEGMENT_WEIGHTS = [38, 27, 22, 13]
SEGMENT_CUSTOMER_POOL = {
    "Consumer": 900,
    "Small Business": 450,
    "Corporate": 220,
    "Enterprise": 80,
}

UNITS = [1, 2, 3, 4, 5]
UNIT_WEIGHTS = [12, 26, 30, 19, 13]

# Mild seasonality: stronger Q4, softer mid-summer.
MONTH_WEIGHTS = [7, 7, 8, 8, 8, 7, 6, 7, 8, 9, 11, 14]
START_DATE = date(2024, 1, 1)
DAYS_IN_YEAR = 366  # 2024 is a leap year


def random_order_date(rng: random.Random) -> date:
    month = rng.choices(range(1, 13), weights=MONTH_WEIGHTS)[0]
    # Pick a random day inside the chosen month.
    first = date(2024, month, 1)
    if month == 12:
        next_month = date(2025, 1, 1)
    else:
        next_month = date(2024, month + 1, 1)
    span = (next_month - first).days
    return first + timedelta(days=rng.randrange(span))


def main() -> None:
    rng = random.Random(SEED)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "order_id",
        "order_date",
        "customer_id",
        "customer_segment",
        "region",
        "product",
        "category",
        "units",
        "unit_price",
        "unit_cost",
        "discount",
    ]

    total_revenue = 0.0
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(1, NUM_ORDERS + 1):
            category, product, unit_price, cost_ratio = rng.choices(
                PRODUCTS, weights=PRODUCT_WEIGHTS
            )[0]
            region = rng.choices(REGIONS, weights=REGION_WEIGHTS)[0]
            segment = rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
            customer_id = (
                f"{segment[:3].upper()}-{rng.randint(1, SEGMENT_CUSTOMER_POOL[segment]):04d}"
            )
            disc_values, disc_weights = REGION_DISCOUNTS[region]
            discount = rng.choices(disc_values, weights=disc_weights)[0]
            units = rng.choices(UNITS, weights=UNIT_WEIGHTS)[0]
            order_date = random_order_date(rng)

            unit_cost = round(unit_price * cost_ratio, 2)
            total_revenue += units * unit_price * (1 - discount)

            writer.writerow(
                {
                    "order_id": f"ORD-{i:05d}",
                    "order_date": order_date.isoformat(),
                    "customer_id": customer_id,
                    "customer_segment": segment,
                    "region": region,
                    "product": product,
                    "category": category,
                    "units": units,
                    "unit_price": f"{unit_price:.2f}",
                    "unit_cost": f"{unit_cost:.2f}",
                    "discount": f"{discount:.2f}",
                }
            )

    print(f"Wrote {NUM_ORDERS:,} orders to {OUTPUT_PATH}")
    print(f"Implied total revenue (before ETL): ${total_revenue:,.2f}")


if __name__ == "__main__":
    main()
