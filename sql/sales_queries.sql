-- Sales Analytics Dashboard — SQL analytics layer (SQLite dialect)
-- =====================================================================
-- Each query below is preceded by an "-- output: <file>.csv" marker.
-- src/run_aggregations.py parses those markers, executes every query
-- against the sales_orders table built by src/etl.py, and writes one
-- aggregated CSV per query into outputs/tables/ (exactly 7 tables).
-- The queries use CTEs, window functions and aggregations throughout.

-- output: revenue_by_region.csv
-- Revenue, orders and profit per region, with share of total revenue and
-- a revenue rank (window functions over the region CTE).
WITH region_totals AS (
    SELECT
        region,
        COUNT(*)              AS orders,
        SUM(units)            AS units_sold,
        SUM(revenue)          AS revenue,
        SUM(profit)           AS profit,
        AVG(revenue)          AS avg_order_value,
        AVG(discount)         AS avg_discount
    FROM sales_orders
    GROUP BY region
)
SELECT
    region,
    orders,
    units_sold,
    ROUND(revenue, 2)                                        AS revenue,
    ROUND(profit, 2)                                         AS profit,
    ROUND(profit / revenue * 100, 2)                         AS profit_margin_pct,
    ROUND(avg_order_value, 2)                                AS avg_order_value,
    ROUND(avg_discount * 100, 2)                             AS avg_discount_pct,
    ROUND(revenue / SUM(revenue) OVER () * 100, 2)           AS revenue_share_pct,
    RANK() OVER (ORDER BY revenue DESC)                      AS revenue_rank
FROM region_totals
ORDER BY revenue DESC;

-- output: revenue_by_category.csv
-- Revenue and profitability per product category, with share of total.
WITH category_totals AS (
    SELECT
        category,
        COUNT(*)       AS orders,
        SUM(units)     AS units_sold,
        SUM(revenue)   AS revenue,
        SUM(profit)    AS profit
    FROM sales_orders
    GROUP BY category
)
SELECT
    category,
    orders,
    units_sold,
    ROUND(revenue, 2)                                AS revenue,
    ROUND(profit, 2)                                 AS profit,
    ROUND(profit / revenue * 100, 2)                 AS profit_margin_pct,
    ROUND(revenue / SUM(revenue) OVER () * 100, 2)   AS revenue_share_pct,
    RANK() OVER (ORDER BY revenue DESC)              AS revenue_rank
FROM category_totals
ORDER BY revenue DESC;

-- output: revenue_by_month.csv
-- Monthly revenue with a running total and month-over-month growth,
-- using SUM() OVER and LAG() window functions.
WITH monthly AS (
    SELECT
        order_month,
        COUNT(*)      AS orders,
        SUM(units)    AS units_sold,
        SUM(revenue)  AS revenue,
        SUM(profit)   AS profit
    FROM sales_orders
    GROUP BY order_month
)
SELECT
    order_month,
    orders,
    units_sold,
    ROUND(revenue, 2)                                                   AS revenue,
    ROUND(profit, 2)                                                    AS profit,
    ROUND(SUM(revenue) OVER (ORDER BY order_month), 2)                  AS running_revenue,
    ROUND(LAG(revenue) OVER (ORDER BY order_month), 2)                  AS prev_month_revenue,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY order_month))
          / LAG(revenue) OVER (ORDER BY order_month) * 100, 2)          AS mom_growth_pct
FROM monthly
ORDER BY order_month;

-- output: top_products.csv
-- Top 3 products by revenue inside each category
-- (RANK() partitioned by category), with each product's share of its
-- category's revenue.
WITH product_totals AS (
    SELECT
        category,
        product,
        COUNT(*)      AS orders,
        SUM(units)    AS units_sold,
        SUM(revenue)  AS revenue,
        SUM(profit)   AS profit
    FROM sales_orders
    GROUP BY category, product
),
ranked AS (
    SELECT
        category,
        product,
        orders,
        units_sold,
        revenue,
        profit,
        ROUND(revenue / SUM(revenue) OVER (PARTITION BY category) * 100, 2)
            AS category_share_pct,
        RANK() OVER (PARTITION BY category ORDER BY revenue DESC)
            AS rank_in_category
    FROM product_totals
)
SELECT
    category,
    product,
    orders,
    units_sold,
    ROUND(revenue, 2)   AS revenue,
    ROUND(profit, 2)    AS profit,
    category_share_pct,
    rank_in_category
FROM ranked
WHERE rank_in_category <= 3
ORDER BY category, rank_in_category;

-- output: discount_bands_profit.csv
-- Discount bands vs profitability: does discounting buy revenue at the
-- cost of profit? Orders are banded with a CASE expression, then
-- aggregated so margin can be compared band to band.
WITH banded AS (
    SELECT
        CASE
            WHEN discount = 0 THEN '0% (none)'
            WHEN discount <= 0.10 THEN '1-10%'
            WHEN discount <= 0.20 THEN '11-20%'
            ELSE '21%+'
        END AS discount_band,
        revenue,
        profit
    FROM sales_orders
)
SELECT
    discount_band,
    COUNT(*)                              AS orders,
    ROUND(SUM(revenue), 2)                AS revenue,
    ROUND(SUM(profit), 2)                 AS profit,
    ROUND(AVG(revenue), 2)                AS avg_order_value,
    ROUND(SUM(profit) / SUM(revenue) * 100, 2) AS profit_margin_pct
FROM banded
GROUP BY discount_band
ORDER BY MIN(CASE discount_band
                 WHEN '0% (none)' THEN 0
                 WHEN '1-10%' THEN 1
                 WHEN '11-20%' THEN 2
                 ELSE 3 END);

-- output: customer_segments.csv
-- Orders, distinct customers, revenue and average order value per
-- customer segment, with share of total revenue.
WITH segment_totals AS (
    SELECT
        customer_segment,
        COUNT(*)                    AS orders,
        COUNT(DISTINCT customer_id) AS customers,
        SUM(revenue)                AS revenue,
        SUM(profit)                 AS profit,
        AVG(revenue)                AS avg_order_value
    FROM sales_orders
    GROUP BY customer_segment
)
SELECT
    customer_segment,
    orders,
    customers,
    ROUND(revenue, 2)                              AS revenue,
    ROUND(profit, 2)                               AS profit,
    ROUND(avg_order_value, 2)                      AS avg_order_value,
    ROUND(revenue / orders, 2)                     AS revenue_per_order,
    ROUND(revenue / SUM(revenue) OVER () * 100, 2) AS revenue_share_pct,
    RANK() OVER (ORDER BY revenue DESC)            AS revenue_rank
FROM segment_totals
ORDER BY revenue DESC;

-- output: daily_sales.csv
-- Daily sales with a running revenue total and a 7-day rolling average
-- of daily revenue (window frame: ROWS BETWEEN 6 PRECEDING AND CURRENT ROW).
WITH daily AS (
    SELECT
        order_date,
        COUNT(*)      AS orders,
        SUM(units)    AS units_sold,
        SUM(revenue)  AS revenue,
        SUM(profit)   AS profit
    FROM sales_orders
    GROUP BY order_date
)
SELECT
    order_date,
    orders,
    units_sold,
    ROUND(revenue, 2)                                                     AS revenue,
    ROUND(profit, 2)                                                      AS profit,
    ROUND(SUM(revenue) OVER (ORDER BY order_date), 2)                     AS running_revenue,
    ROUND(AVG(revenue) OVER (ORDER BY order_date
                             ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)
                                                                          AS revenue_7d_avg
FROM daily
ORDER BY order_date;
