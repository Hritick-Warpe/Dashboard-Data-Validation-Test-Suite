-- ============================================================
-- validation_summary.sql : ALL 32 checks in ONE result table (MySQL 8)
-- Run once; you get one grid with test_id, failures and PASS/FAIL.
-- Switch the load under test first:
--   CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_defective;
--   CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_clean;
-- ============================================================
USE qa_sales;

SELECT test_id, test_name, failures, CASE WHEN failures <= tolerance THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
SELECT 'TC-001' AS test_id, 'Row count: source (non-cancelled) vs target' AS test_name, (SELECT ABS((SELECT COUNT(*) FROM source_orders WHERE status <> 'Cancelled') - (SELECT COUNT(*) FROM target_fact_sales)) AS failures) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-002' AS test_id, 'Source orders missing in target' AS test_name, (SELECT COUNT(*) AS failures FROM source_orders s LEFT JOIN target_fact_sales t ON s.order_id = t.order_id WHERE s.status <> 'Cancelled' AND t.order_id IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-003' AS test_id, 'Target orders that do not exist in source' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN source_orders s ON t.order_id = s.order_id WHERE s.order_id IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-004' AS test_id, 'Duplicate order_id in target' AS test_name, (SELECT COUNT(*) AS failures FROM (SELECT order_id FROM target_fact_sales GROUP BY order_id HAVING COUNT(*) > 1) x) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-005' AS test_id, 'Cancelled orders present in target (rule R1)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE status = 'Cancelled') AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-006' AS test_id, 'Status values outside the allowed list' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE status IS NULL OR status NOT IN ('Completed','Shipped','Pending','Cancelled')) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-007' AS test_id, 'NULL in key columns (order_id, customer_id, product_id, order_date)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE order_id IS NULL OR customer_id IS NULL OR product_id IS NULL OR order_date IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-008' AS test_id, 'NULL in net_amount' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE net_amount IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-009' AS test_id, 'NULL in quantity / unit_price / order_amount' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE quantity IS NULL OR unit_price IS NULL OR order_amount IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-010' AS test_id, 'net_amount = order_amount x (1 - discount%) (rule R2)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE net_amount IS NOT NULL AND ABS(ROUND(order_amount * (1 - discount_pct / 100.0), 2) - net_amount) > 0.011) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-011' AS test_id, 'order_amount = quantity x unit_price' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE ABS(order_amount - quantity * unit_price) > 0.005) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-012' AS test_id, 'order_month = first 7 characters of order_date (rule R3)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE SUBSTR(order_date, 1, 7) <> order_month) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-013' AS test_id, 'Orphan customer_id (not in dim_customer)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN dim_customer c ON t.customer_id = c.customer_id WHERE c.customer_id IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-014' AS test_id, 'Orphan product_id (not in dim_product)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN dim_product p ON t.product_id = p.product_id WHERE p.product_id IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-015' AS test_id, 'Orphan region_code (not in dim_region)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN dim_region r ON t.region_code = r.region_code WHERE r.region_code IS NULL) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-016' AS test_id, 'Quantity is zero or negative (boundary)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE quantity <= 0) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-017' AS test_id, 'unit_price is zero or negative (boundary)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE unit_price <= 0) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-018' AS test_id, 'discount_pct outside allowed set (0,5,10,15,20)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE discount_pct NOT IN (0,5,10,15,20)) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-019' AS test_id, 'Future-dated orders (order_date after batch date)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE order_date > '2026-01-05') AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-020' AS test_id, 'Orders dated before the data start (2025-01-01)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE order_date < '2025-01-01') AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-021' AS test_id, 'region_code matches source (rule R7)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.region_code <> s.region_code) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-022' AS test_id, 'customer_id matches source' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.customer_id <> s.customer_id) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-023' AS test_id, 'quantity matches source' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.quantity <> s.quantity) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-024' AS test_id, 'unit_price matches source' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE ABS(t.unit_price - s.unit_price) > 0.005) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-025' AS test_id, 'order_date matches source' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.order_date <> s.order_date) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-026' AS test_id, 'order_amount matches source' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE ABS(t.order_amount - s.order_amount) > 0.005) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-027' AS test_id, 'load_date equals the latest batch date (timeliness)' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE load_date <> '2026-01-05') AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-028' AS test_id, 'Total order_amount: source vs target' AS test_name, (SELECT ROUND(ABS((SELECT SUM(order_amount) FROM source_orders WHERE status <> 'Cancelled') - (SELECT SUM(order_amount) FROM target_fact_sales)), 2) AS failures) AS failures, 0.01 AS tolerance
UNION ALL
SELECT 'TC-029' AS test_id, 'Total net_amount: expected from source vs target' AS test_name, (SELECT ROUND(ABS((SELECT SUM(order_amount * (1 - discount_pct / 100.0)) FROM source_orders WHERE status <> 'Cancelled') - (SELECT SUM(net_amount) FROM target_fact_sales)), 2) AS failures) AS failures, 50.0 AS tolerance
UNION ALL
SELECT 'TC-030' AS test_id, 'Region-wise order_amount reconciliation (regions that differ)' AS test_name, (SELECT COUNT(*) AS failures FROM dim_region r LEFT JOIN (SELECT region_code, SUM(order_amount) AS a FROM source_orders WHERE status <> 'Cancelled' GROUP BY region_code) s ON s.region_code = r.region_code LEFT JOIN (SELECT region_code, SUM(order_amount) AS a FROM target_fact_sales GROUP BY region_code) t ON t.region_code = r.region_code WHERE ABS(COALESCE(s.a,0) - COALESCE(t.a,0)) > 0.01) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-031' AS test_id, 'Month-wise order_amount reconciliation (months that differ)' AS test_name, (SELECT COUNT(*) AS failures FROM (SELECT DISTINCT SUBSTR(order_date,1,7) AS m FROM source_orders) mm LEFT JOIN (SELECT SUBSTR(order_date,1,7) AS m, SUM(order_amount) AS a FROM source_orders WHERE status <> 'Cancelled' GROUP BY SUBSTR(order_date,1,7)) s ON s.m = mm.m LEFT JOIN (SELECT SUBSTR(order_date,1,7) AS m, SUM(order_amount) AS a FROM target_fact_sales GROUP BY SUBSTR(order_date,1,7)) t ON t.m = mm.m WHERE ABS(COALESCE(s.a,0) - COALESCE(t.a,0)) > 0.01) AS failures, 0 AS tolerance
UNION ALL
SELECT 'TC-032' AS test_id, 'net_amount has more than 2 decimal places' AS test_name, (SELECT COUNT(*) AS failures FROM target_fact_sales WHERE net_amount IS NOT NULL AND ABS(net_amount * 100 - ROUND(net_amount * 100, 0)) > 0.0001) AS failures, 0 AS tolerance
) x
ORDER BY test_id;
