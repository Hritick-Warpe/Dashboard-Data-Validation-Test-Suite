"""
validate_data.py - automated data validation for the Sales ETL test suite.

Runs 32 checks (each has a matching SQL query in sql/validation_queries.sql)
on a target table and prints a PASS/FAIL table.

Usage:
    python python/validate_data.py                      # runs on clean AND defective target
    python python/validate_data.py clean                # only the clean load
    python python/validate_data.py defective            # only the defective load
    python python/validate_data.py --export-sql         # regenerate sql/validation_queries.sql

Each check returns a "failures" number: 0 = PASS (variance checks allow a small tolerance).
"""
import os, sys
import numpy as np, pandas as pd

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(BASE, "data")
BATCH_DATE = "2026-01-05"
STATUSES = ("Completed", "Shipped", "Pending", "Cancelled")

def load(target_name):
    rd = lambda f: pd.read_csv(os.path.join(DATA, f), dtype={"order_date": str, "load_date": str,
                                                            "order_month": str, "region_code": str})
    return dict(src=rd("source_orders.csv"), tgt=rd(f"target_fact_sales_{target_name}.csv"),
                cust=rd("dim_customer.csv"), prod=rd("dim_product.csv"), reg=rd("dim_region.csv"))

def _expected_net(df):
    oc = np.round(df.order_amount.fillna(0) * 100).astype("int64")
    return ((oc * (100 - df.discount_pct.fillna(0).astype("int64")) + 50) // 100) / 100

def _merged(d):
    cols = ["order_id", "customer_id", "region_code", "quantity", "unit_price", "order_date", "order_amount"]
    return d["tgt"].merge(d["src"][cols], on="order_id", how="inner", suffixes=("", "_s"))

# ---------------------------------------------------------------------------
# CHECK REGISTRY: (id, req, name, test_type, dimension, expected, tolerance, sql, pandas_fn)
# SQL uses the view `target_fact_sales`; every SQL returns ONE number called failures.
# ---------------------------------------------------------------------------
T = "target_fact_sales"
CHECKS = [
 ("TC-001","REQ-01","Row count: source (non-cancelled) vs target","Reconciliation","Completeness",
  "Difference in row count = 0",0,
  f"SELECT ABS((SELECT COUNT(*) FROM source_orders WHERE status <> 'Cancelled') - (SELECT COUNT(*) FROM {T})) AS failures",
  lambda d: abs(int((d['src'].status!='Cancelled').sum()) - len(d['tgt']))),
 ("TC-002","REQ-01","Source orders missing in target","Source-to-target","Completeness",
  "0 missing orders",0,
  f"SELECT COUNT(*) AS failures FROM source_orders s LEFT JOIN {T} t ON s.order_id = t.order_id WHERE s.status <> 'Cancelled' AND t.order_id IS NULL",
  lambda d: len(set(d['src'][d['src'].status!='Cancelled'].order_id) - set(d['tgt'].order_id))),
 ("TC-003","REQ-02","Target orders that do not exist in source","Source-to-target","Consistency",
  "0 unknown orders",0,
  f"SELECT COUNT(*) AS failures FROM {T} t LEFT JOIN source_orders s ON t.order_id = s.order_id WHERE s.order_id IS NULL",
  lambda d: int((~d['tgt'].order_id.isin(d['src'].order_id)).sum())),
 ("TC-004","REQ-03","Duplicate order_id in target","Data quality","Uniqueness",
  "0 duplicated order_ids",0,
  f"SELECT COUNT(*) AS failures FROM (SELECT order_id FROM {T} GROUP BY order_id HAVING COUNT(*) > 1) x",
  lambda d: int((d['tgt'].order_id.value_counts()>1).sum())),
 ("TC-005","REQ-04","Cancelled orders present in target (rule R1)","Business rule","Validity",
  "0 cancelled orders",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE status = 'Cancelled'",
  lambda d: int((d['tgt'].status=='Cancelled').sum())),
 ("TC-006","REQ-08","Status values outside the allowed list","Data quality","Validity",
  "0 rows with unknown or NULL status",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE status IS NULL OR status NOT IN ('Completed','Shipped','Pending','Cancelled')",
  lambda d: int((~d['tgt'].status.isin(STATUSES)).sum())),
 ("TC-007","REQ-08","NULL in key columns (order_id, customer_id, product_id, order_date)","Data quality","Completeness",
  "0 rows with NULL keys",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE order_id IS NULL OR customer_id IS NULL OR product_id IS NULL OR order_date IS NULL",
  lambda d: int(d['tgt'][['order_id','customer_id','product_id','order_date']].isna().any(axis=1).sum())),
 ("TC-008","REQ-08","NULL in net_amount","Data quality","Completeness",
  "0 NULL net_amount",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE net_amount IS NULL",
  lambda d: int(d['tgt'].net_amount.isna().sum())),
 ("TC-009","REQ-08","NULL in quantity / unit_price / order_amount","Data quality","Completeness",
  "0 rows with NULL measures",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE quantity IS NULL OR unit_price IS NULL OR order_amount IS NULL",
  lambda d: int(d['tgt'][['quantity','unit_price','order_amount']].isna().any(axis=1).sum())),
 ("TC-010","REQ-05","net_amount = order_amount x (1 - discount%) (rule R2)","Calculation","Accuracy",
  "0 rows where net_amount is wrong (1 cent tolerance)",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE net_amount IS NOT NULL AND ABS(ROUND(order_amount * (1 - discount_pct / 100.0), 2) - net_amount) > 0.011",
  lambda d: int(((d['tgt'].net_amount.notna()) & ((_expected_net(d['tgt']) - d['tgt'].net_amount).abs() > 0.011)).sum())),
 ("TC-011","REQ-05","order_amount = quantity x unit_price","Calculation","Accuracy",
  "0 rows where amount is wrong",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE ABS(order_amount - quantity * unit_price) > 0.005",
  lambda d: int(((d['tgt'].order_amount - d['tgt'].quantity*d['tgt'].unit_price).abs() > 0.005).sum())),
 ("TC-012","REQ-06","order_month = first 7 characters of order_date (rule R3)","Transformation","Accuracy",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE SUBSTR(order_date, 1, 7) <> order_month",
  lambda d: int((d['tgt'].order_date.str[:7] != d['tgt'].order_month).sum())),
 ("TC-013","REQ-07","Orphan customer_id (not in dim_customer)","Referential integrity","Consistency",
  "0 orphan customers",0,
  f"SELECT COUNT(*) AS failures FROM {T} t LEFT JOIN dim_customer c ON t.customer_id = c.customer_id WHERE c.customer_id IS NULL",
  lambda d: int((~d['tgt'].customer_id.isin(d['cust'].customer_id)).sum())),
 ("TC-014","REQ-07","Orphan product_id (not in dim_product)","Referential integrity","Consistency",
  "0 orphan products",0,
  f"SELECT COUNT(*) AS failures FROM {T} t LEFT JOIN dim_product p ON t.product_id = p.product_id WHERE p.product_id IS NULL",
  lambda d: int((~d['tgt'].product_id.isin(d['prod'].product_id)).sum())),
 ("TC-015","REQ-07","Orphan region_code (not in dim_region)","Referential integrity","Consistency",
  "0 orphan regions",0,
  f"SELECT COUNT(*) AS failures FROM {T} t LEFT JOIN dim_region r ON t.region_code = r.region_code WHERE r.region_code IS NULL",
  lambda d: int((~d['tgt'].region_code.isin(d['reg'].region_code)).sum())),
 ("TC-016","REQ-08","Quantity is zero or negative (boundary)","Boundary","Validity",
  "0 rows with quantity <= 0",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE quantity <= 0",
  lambda d: int((d['tgt'].quantity <= 0).sum())),
 ("TC-017","REQ-08","unit_price is zero or negative (boundary)","Boundary","Validity",
  "0 rows with unit_price <= 0",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE unit_price <= 0",
  lambda d: int((d['tgt'].unit_price <= 0).sum())),
 ("TC-018","REQ-08","discount_pct outside allowed set (0,5,10,15,20)","Negative","Validity",
  "0 rows with other discount values",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE discount_pct NOT IN (0,5,10,15,20)",
  lambda d: int((~d['tgt'].discount_pct.isin([0,5,10,15,20])).sum())),
 ("TC-019","REQ-08","Future-dated orders (order_date after batch date)","Boundary","Validity",
  f"0 rows with order_date > {BATCH_DATE}",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE order_date > '{BATCH_DATE}'",
  lambda d: int((d['tgt'].order_date > BATCH_DATE).sum())),
 ("TC-020","REQ-08","Orders dated before the data start (2025-01-01)","Boundary","Validity",
  "0 rows earlier than 2025-01-01",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE order_date < '2025-01-01'",
  lambda d: int((d['tgt'].order_date < '2025-01-01').sum())),
 ("TC-021","REQ-09","region_code matches source (rule R7)","Source-to-target","Consistency",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} t JOIN source_orders s ON t.order_id = s.order_id WHERE t.region_code <> s.region_code",
  lambda d: int((_merged(d).region_code != _merged(d).region_code_s).sum())),
 ("TC-022","REQ-09","customer_id matches source","Source-to-target","Consistency",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} t JOIN source_orders s ON t.order_id = s.order_id WHERE t.customer_id <> s.customer_id",
  lambda d: int((_merged(d).customer_id != _merged(d).customer_id_s).sum())),
 ("TC-023","REQ-09","quantity matches source","Source-to-target","Consistency",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} t JOIN source_orders s ON t.order_id = s.order_id WHERE t.quantity <> s.quantity",
  lambda d: int((_merged(d).quantity != _merged(d).quantity_s).sum())),
 ("TC-024","REQ-09","unit_price matches source","Source-to-target","Consistency",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} t JOIN source_orders s ON t.order_id = s.order_id WHERE ABS(t.unit_price - s.unit_price) > 0.005",
  lambda d: int(((_merged(d).unit_price - _merged(d).unit_price_s).abs() > 0.005).sum())),
 ("TC-025","REQ-09","order_date matches source","Source-to-target","Consistency",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} t JOIN source_orders s ON t.order_id = s.order_id WHERE t.order_date <> s.order_date",
  lambda d: int((_merged(d).order_date != _merged(d).order_date_s).sum())),
 ("TC-026","REQ-09","order_amount matches source","Source-to-target","Accuracy",
  "0 mismatches",0,
  f"SELECT COUNT(*) AS failures FROM {T} t JOIN source_orders s ON t.order_id = s.order_id WHERE ABS(t.order_amount - s.order_amount) > 0.005",
  lambda d: int(((_merged(d).order_amount - _merged(d).order_amount_s).abs() > 0.005).sum())),
 ("TC-027","REQ-10","load_date equals the latest batch date (timeliness)","Timeliness","Timeliness",
  f"0 rows with load_date <> {BATCH_DATE}",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE load_date <> '{BATCH_DATE}'",
  lambda d: int((d['tgt'].load_date != BATCH_DATE).sum())),
 ("TC-028","REQ-11","Total order_amount: source vs target","Reconciliation","Accuracy",
  "Variance = 0.00 (tolerance 0.01)",0.01,
  f"SELECT ROUND(ABS((SELECT SUM(order_amount) FROM source_orders WHERE status <> 'Cancelled') - (SELECT SUM(order_amount) FROM {T})), 2) AS failures",
  lambda d: round(abs(d['src'][d['src'].status!='Cancelled'].order_amount.sum() - d['tgt'].order_amount.sum()), 2)),
 ("TC-029","REQ-11","Total net_amount: expected from source vs target","Reconciliation","Accuracy",
  "Variance within 50.00 (allows per-row cent rounding across ~42k rows)",50.0,
  f"SELECT ROUND(ABS((SELECT SUM(order_amount * (1 - discount_pct / 100.0)) FROM source_orders WHERE status <> 'Cancelled') - (SELECT SUM(net_amount) FROM {T})), 2) AS failures",
  lambda d: round(abs((lambda x: (x.order_amount*(1-x.discount_pct/100.0)).sum())(d['src'][d['src'].status!='Cancelled']) - d['tgt'].net_amount.sum()), 2)),
 ("TC-030","REQ-11","Region-wise order_amount reconciliation (regions that differ)","Reconciliation","Accuracy",
  "0 regions with a difference",0,
  f"SELECT COUNT(*) AS failures FROM dim_region r LEFT JOIN (SELECT region_code, SUM(order_amount) AS a FROM source_orders WHERE status <> 'Cancelled' GROUP BY region_code) s ON s.region_code = r.region_code LEFT JOIN (SELECT region_code, SUM(order_amount) AS a FROM {T} GROUP BY region_code) t ON t.region_code = r.region_code WHERE ABS(COALESCE(s.a,0) - COALESCE(t.a,0)) > 0.01",
  lambda d: int((lambda s,t,r: sum(abs(s.get(x,0)-t.get(x,0))>0.01 for x in r.region_code))(
      d['src'][d['src'].status!='Cancelled'].groupby('region_code').order_amount.sum().to_dict(),
      d['tgt'].groupby('region_code').order_amount.sum().to_dict(), d['reg']))),
 ("TC-031","REQ-11","Month-wise order_amount reconciliation (months that differ)","Reconciliation","Accuracy",
  "0 months with a difference",0,
  f"SELECT COUNT(*) AS failures FROM (SELECT DISTINCT SUBSTR(order_date,1,7) AS m FROM source_orders) mm LEFT JOIN (SELECT SUBSTR(order_date,1,7) AS m, SUM(order_amount) AS a FROM source_orders WHERE status <> 'Cancelled' GROUP BY SUBSTR(order_date,1,7)) s ON s.m = mm.m LEFT JOIN (SELECT SUBSTR(order_date,1,7) AS m, SUM(order_amount) AS a FROM {T} GROUP BY SUBSTR(order_date,1,7)) t ON t.m = mm.m WHERE ABS(COALESCE(s.a,0) - COALESCE(t.a,0)) > 0.01",
  lambda d: int((lambda s,t,ms: sum(abs(s.get(x,0)-t.get(x,0))>0.01 for x in ms))(
      d['src'][d['src'].status!='Cancelled'].assign(m=lambda x: x.order_date.str[:7]).groupby('m').order_amount.sum().to_dict(),
      d['tgt'].assign(m=lambda x: x.order_date.str[:7]).groupby('m').order_amount.sum().to_dict(),
      set(d['src'].order_date.str[:7])))),
 ("TC-032","REQ-08","net_amount has more than 2 decimal places","Data quality","Validity",
  "0 rows with extra decimals",0,
  f"SELECT COUNT(*) AS failures FROM {T} WHERE net_amount IS NOT NULL AND ABS(net_amount * 100 - ROUND(net_amount * 100, 0)) > 0.0001",
  lambda d: int(((d['tgt'].net_amount.dropna()*100 - np.round(d['tgt'].net_amount.dropna()*100)).abs() > 0.0001).sum())),
]

def run_checks(target_name):
    d = load(target_name); rows = []
    for cid, req, name, ttype, dim, expected, tol, sql, fn in CHECKS:
        val = fn(d)
        rows.append(dict(test_id=cid, req_id=req, check=name, test_type=ttype, dimension=dim,
                         expected=expected, failures=val, status="PASS" if val <= tol else "FAIL"))
    return pd.DataFrame(rows)

def export_sql(path=None):
    path = path or os.path.join(BASE, "sql", "validation_queries.sql")
    out = ["-- ============================================================",
           "-- validation_queries.sql  (MySQL 8 compatible)",
           "-- One query per test case. Every query returns ONE number: failures.",
           "-- failures = 0  -> PASS  (variance checks allow a tiny tolerance, see 'Expected')",
           "-- Switch the target under test by re-pointing the view:",
           "--   CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_clean;",
           "--   CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_defective;",
           "-- ============================================================",
           "USE qa_sales;",
           "CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_defective;", ""]
    for cid, req, name, ttype, dim, expected, tol, sql, fn in CHECKS:
        out += [f"-- {cid} | {req} | {dim} | {name}", f"-- Expected: {expected}", sql + ";", ""]
    open(path, "w").write("\n".join(out)); return path

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--export-sql" in args:
        print("written", export_sql()); sys.exit()
    targets = [a for a in args if a in ("clean", "defective")] or ["clean", "defective"]
    for tname in targets:
        res = run_checks(tname)
        print(f"\n=== Target: {tname} ===")
        print(res[["test_id","check","failures","status"]].to_string(index=False))
        print(f"PASS {int((res.status=='PASS').sum())} / FAIL {int((res.status=='FAIL').sum())}")
        res.to_csv(os.path.join(BASE, "evidence", f"results_{tname}.csv"), index=False)
