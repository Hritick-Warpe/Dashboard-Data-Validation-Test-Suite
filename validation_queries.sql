-- ============================================================
-- validation_queries.sql  (MySQL 8 compatible)
-- One query per test case. Every query returns ONE number: failures.
-- failures = 0  -> PASS  (variance checks allow a tiny tolerance, see 'Expected')
-- Switch the target under test by re-pointing the view:
--   CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_clean;
--   CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_defective;
-- ============================================================
USE qa_sales;
CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_defective;

-- TC-001 | REQ-01 | Completeness | Row count: source (non-cancelled) vs target
-- Expected: Difference in row count = 0
SELECT ABS((SELECT COUNT(*) FROM source_orders WHERE status <> 'Cancelled') - (SELECT COUNT(*) FROM target_fact_sales)) AS failures;

-- TC-002 | REQ-01 | Completeness | Source orders missing in target
-- Expected: 0 missing orders
SELECT COUNT(*) AS failures FROM source_orders s LEFT JOIN target_fact_sales t ON s.order_id = t.order_id WHERE s.status <> 'Cancelled' AND t.order_id IS NULL;

-- TC-003 | REQ-02 | Consistency | Target orders that do not exist in source
-- Expected: 0 unknown orders
SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN source_orders s ON t.order_id = s.order_id WHERE s.order_id IS NULL;

-- TC-004 | REQ-03 | Uniqueness | Duplicate order_id in target
-- Expected: 0 duplicated order_ids
SELECT COUNT(*) AS failures FROM (SELECT order_id FROM target_fact_sales GROUP BY order_id HAVING COUNT(*) > 1) x;

-- TC-005 | REQ-04 | Validity | Cancelled orders present in target (rule R1)
-- Expected: 0 cancelled orders
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE status = 'Cancelled';

-- TC-006 | REQ-08 | Validity | Status values outside the allowed list
-- Expected: 0 rows with unknown or NULL status
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE status IS NULL OR status NOT IN ('Completed','Shipped','Pending','Cancelled');

-- TC-007 | REQ-08 | Completeness | NULL in key columns (order_id, customer_id, product_id, order_date)
-- Expected: 0 rows with NULL keys
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE order_id IS NULL OR customer_id IS NULL OR product_id IS NULL OR order_date IS NULL;

-- TC-008 | REQ-08 | Completeness | NULL in net_amount
-- Expected: 0 NULL net_amount
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE net_amount IS NULL;

-- TC-009 | REQ-08 | Completeness | NULL in quantity / unit_price / order_amount
-- Expected: 0 rows with NULL measures
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE quantity IS NULL OR unit_price IS NULL OR order_amount IS NULL;

-- TC-010 | REQ-05 | Accuracy | net_amount = order_amount x (1 - discount%) (rule R2)
-- Expected: 0 rows where net_amount is wrong (1 cent tolerance)
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE net_amount IS NOT NULL AND ABS(ROUND(order_amount * (1 - discount_pct / 100.0), 2) - net_amount) > 0.011;

-- TC-011 | REQ-05 | Accuracy | order_amount = quantity x unit_price
-- Expected: 0 rows where amount is wrong
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE ABS(order_amount - quantity * unit_price) > 0.005;

-- TC-012 | REQ-06 | Accuracy | order_month = first 7 characters of order_date (rule R3)
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE SUBSTR(order_date, 1, 7) <> order_month;

-- TC-013 | REQ-07 | Consistency | Orphan customer_id (not in dim_customer)
-- Expected: 0 orphan customers
SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN dim_customer c ON t.customer_id = c.customer_id WHERE c.customer_id IS NULL;

-- TC-014 | REQ-07 | Consistency | Orphan product_id (not in dim_product)
-- Expected: 0 orphan products
SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN dim_product p ON t.product_id = p.product_id WHERE p.product_id IS NULL;

-- TC-015 | REQ-07 | Consistency | Orphan region_code (not in dim_region)
-- Expected: 0 orphan regions
SELECT COUNT(*) AS failures FROM target_fact_sales t LEFT JOIN dim_region r ON t.region_code = r.region_code WHERE r.region_code IS NULL;

-- TC-016 | REQ-08 | Validity | Quantity is zero or negative (boundary)
-- Expected: 0 rows with quantity <= 0
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE quantity <= 0;

-- TC-017 | REQ-08 | Validity | unit_price is zero or negative (boundary)
-- Expected: 0 rows with unit_price <= 0
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE unit_price <= 0;

-- TC-018 | REQ-08 | Validity | discount_pct outside allowed set (0,5,10,15,20)
-- Expected: 0 rows with other discount values
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE discount_pct NOT IN (0,5,10,15,20);

-- TC-019 | REQ-08 | Validity | Future-dated orders (order_date after batch date)
-- Expected: 0 rows with order_date > 2026-01-05
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE order_date > '2026-01-05';

-- TC-020 | REQ-08 | Validity | Orders dated before the data start (2025-01-01)
-- Expected: 0 rows earlier than 2025-01-01
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE order_date < '2025-01-01';

-- TC-021 | REQ-09 | Consistency | region_code matches source (rule R7)
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.region_code <> s.region_code;

-- TC-022 | REQ-09 | Consistency | customer_id matches source
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.customer_id <> s.customer_id;

-- TC-023 | REQ-09 | Consistency | quantity matches source
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.quantity <> s.quantity;

-- TC-024 | REQ-09 | Consistency | unit_price matches source
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE ABS(t.unit_price - s.unit_price) > 0.005;

-- TC-025 | REQ-09 | Consistency | order_date matches source
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE t.order_date <> s.order_date;

-- TC-026 | REQ-09 | Accuracy | order_amount matches source
-- Expected: 0 mismatches
SELECT COUNT(*) AS failures FROM target_fact_sales t JOIN source_orders s ON t.order_id = s.order_id WHERE ABS(t.order_amount - s.order_amount) > 0.005;

-- TC-027 | REQ-10 | Timeliness | load_date equals the latest batch date (timeliness)
-- Expected: 0 rows with load_date <> 2026-01-05
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE load_date <> '2026-01-05';

-- TC-028 | REQ-11 | Accuracy | Total order_amount: source vs target
-- Expected: Variance = 0.00 (tolerance 0.01)
SELECT ROUND(ABS((SELECT SUM(order_amount) FROM source_orders WHERE status <> 'Cancelled') - (SELECT SUM(order_amount) FROM target_fact_sales)), 2) AS failures;

-- TC-029 | REQ-11 | Accuracy | Total net_amount: expected from source vs target
-- Expected: Variance within 50.00 (allows per-row cent rounding across ~42k rows)
SELECT ROUND(ABS((SELECT SUM(order_amount * (1 - discount_pct / 100.0)) FROM source_orders WHERE status <> 'Cancelled') - (SELECT SUM(net_amount) FROM target_fact_sales)), 2) AS failures;

-- TC-030 | REQ-11 | Accuracy | Region-wise order_amount reconciliation (regions that differ)
-- Expected: 0 regions with a difference
SELECT COUNT(*) AS failures FROM dim_region r LEFT JOIN (SELECT region_code, SUM(order_amount) AS a FROM source_orders WHERE status <> 'Cancelled' GROUP BY region_code) s ON s.region_code = r.region_code LEFT JOIN (SELECT region_code, SUM(order_amount) AS a FROM target_fact_sales GROUP BY region_code) t ON t.region_code = r.region_code WHERE ABS(COALESCE(s.a,0) - COALESCE(t.a,0)) > 0.01;

-- TC-031 | REQ-11 | Accuracy | Month-wise order_amount reconciliation (months that differ)
-- Expected: 0 months with a difference
SELECT COUNT(*) AS failures FROM (SELECT DISTINCT SUBSTR(order_date,1,7) AS m FROM source_orders) mm LEFT JOIN (SELECT SUBSTR(order_date,1,7) AS m, SUM(order_amount) AS a FROM source_orders WHERE status <> 'Cancelled' GROUP BY SUBSTR(order_date,1,7)) s ON s.m = mm.m LEFT JOIN (SELECT SUBSTR(order_date,1,7) AS m, SUM(order_amount) AS a FROM target_fact_sales GROUP BY SUBSTR(order_date,1,7)) t ON t.m = mm.m WHERE ABS(COALESCE(s.a,0) - COALESCE(t.a,0)) > 0.01;

-- TC-032 | REQ-08 | Validity | net_amount has more than 2 decimal places
-- Expected: 0 rows with extra decimals
SELECT COUNT(*) AS failures FROM target_fact_sales WHERE net_amount IS NOT NULL AND ABS(net_amount * 100 - ROUND(net_amount * 100, 0)) > 0.0001;
