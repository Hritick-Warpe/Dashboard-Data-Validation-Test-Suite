"""
Generates an enterprise-style Sales & Billing analytics dataset for QA practice.
Source system (OLTP-like) -> ETL rules -> Target warehouse (fact + dimensions).
Also creates a DEFECTIVE target with seeded defects and an answer-key manifest.
All data is synthetic. Seed fixed so results are reproducible.
"""
import numpy as np, pandas as pd, os
rng = np.random.default_rng(42)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"); os.makedirs(out, exist_ok=True)

# ---------- Dimensions ----------
regions = pd.DataFrame({
  "region_code":["N","S","E","W","C","NE","SW","NW"],
  "region_name":["North","South","East","West","Central","North-East","South-West","North-West"]})
n_cust, n_prod = 500, 60
segments = ["Enterprise","SMB","Retail","Government"]
cust = pd.DataFrame({
  "customer_id": np.arange(1001, 1001+n_cust),
  "customer_name": [f"Customer_{i:04d}" for i in range(n_cust)],
  "segment": rng.choice(segments, n_cust, p=[.25,.35,.3,.1]),
  "region_code": rng.choice(regions.region_code, n_cust),
  "is_active": rng.choice([1,0], n_cust, p=[.92,.08])})
cats = ["Software","Hardware","Services","Support","Training"]
prod = pd.DataFrame({
  "product_id": np.arange(2001, 2001+n_prod),
  "product_name": [f"Product_{i:03d}" for i in range(n_prod)],
  "category": rng.choice(cats, n_prod),
  "list_price": np.round(rng.uniform(20, 900, n_prod), 2)})

# ---------- Source orders ----------
N = 50000
oid = np.arange(500001, 500001+N)
c = rng.choice(cust.customer_id, N)
p = rng.choice(prod.product_id, N)
dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D")
qty = rng.integers(1, 21, N)
price = prod.set_index("product_id").loc[p, "list_price"].values
disc = rng.choice([0,5,10,15,20], N, p=[.4,.25,.2,.1,.05])
status = rng.choice(["Completed","Shipped","Pending","Cancelled"], N, p=[.55,.2,.1,.15])
reg = cust.set_index("customer_id").loc[c, "region_code"].values
src = pd.DataFrame({
  "order_id": oid, "customer_id": c, "product_id": p,
  "order_date": dates.strftime("%Y-%m-%d"), "quantity": qty,
  "unit_price": price, "discount_pct": disc,
  "order_amount": np.round(qty*price, 2), "status": status,
  "region_code": reg})
src["created_ts"] = (dates + pd.to_timedelta(rng.integers(0, 86400, N), unit="s")).strftime("%Y-%m-%d %H:%M:%S")

# ---------- ETL rules (the 'requirements' you test against) ----------
# R1 Cancelled orders are NOT loaded to target.
# R2 net_amount = order_amount * (1 - discount_pct/100), rounded to 2 decimals.
# R3 order_month = YYYY-MM of order_date.
# R4 Every target row must have a valid customer, product, region.
# R5 order_id is unique in target.
tgt = src[src.status != "Cancelled"].copy()
# integer-cent arithmetic with ROUND-HALF-UP so results match SQL DECIMAL rounding exactly
_oc = np.round(tgt.order_amount*100).astype("int64")
tgt["net_amount"] = ((_oc*(100-tgt.discount_pct)+50)//100)/100
tgt["order_month"] = tgt.order_date.str[:7]
tgt["load_date"] = "2026-01-05"
tgt = tgt[["order_id","customer_id","product_id","order_date","order_month","quantity",
           "unit_price","discount_pct","order_amount","net_amount","status","region_code","load_date"]]

# ---------- Defective copy with seeded defects + answer key ----------
d = tgt.copy().reset_index(drop=True); log = []
def pick(n): return rng.choice(d.index, n, replace=False)
# D1 duplicates
i = pick(25); dup = d.loc[i]; d = pd.concat([d, dup], ignore_index=True)
log += [("DEF-01","Duplicate order_id loaded","Uniqueness",len(i),"order_id: "+",".join(map(str,dup.order_id.head(5)))+"...")]
# D2 missing rows (dropped in ETL)
i = pick(40); log += [("DEF-02","Rows missing in target (dropped by ETL)","Completeness",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
d = d.drop(i).reset_index(drop=True)
# D3 wrong net_amount (discount ignored)
i = rng.choice(d.index[d.discount_pct>0], 60, replace=False); d.loc[i,"net_amount"] = d.loc[i,"order_amount"]
log += [("DEF-03","net_amount ignores discount","Accuracy",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D4 null amounts
i = pick(30); d.loc[i,"net_amount"] = np.nan
log += [("DEF-04","NULL net_amount","Completeness",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D5 cancelled order leaked into target
i = pick(35); d.loc[i,"status"] = "Cancelled"
log += [("DEF-05","Cancelled orders present in target (rule R1)","Validity",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D6 orphan customer ids
i = pick(20); d.loc[i,"customer_id"] = 9999
log += [("DEF-06","customer_id not in dim_customer (orphan)","Consistency",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D7 future date
i = pick(15); d.loc[i,"order_date"] = "2027-03-15"; d.loc[i,"order_month"] = "2027-03"
log += [("DEF-07","Future-dated orders","Validity",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D8 negative quantity
i = pick(12); d.loc[i,"quantity"] = -d.loc[i,"quantity"]
log += [("DEF-08","Negative quantity","Validity",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D9 region mismatch
i = pick(45); d.loc[i,"region_code"] = "C"
log += [("DEF-09","region_code differs from source","Consistency",len(i),"order_id: "+",".join(map(str,d.loc[i].order_id.head(5)))+"...")]
# D10 stale load date (timeliness)
i = pick(500); d.loc[i,"load_date"] = "2025-06-01"
log += [("DEF-10","Stale load_date (timeliness)","Timeliness",len(i),"500 random rows")]
manifest = pd.DataFrame(log, columns=["defect_id","description","quality_dimension","rows_affected","sample_ids"])

# ---------- Save ----------
regions.to_csv(f"{out}/dim_region.csv", index=False)
cust.to_csv(f"{out}/dim_customer.csv", index=False)
prod.to_csv(f"{out}/dim_product.csv", index=False)
src.to_csv(f"{out}/source_orders.csv", index=False)
tgt.to_csv(f"{out}/target_fact_sales_clean.csv", index=False)
d.to_csv(f"{out}/target_fact_sales_defective.csv", index=False)
manifest.to_csv(f"{out}/_defect_answer_key.csv", index=False)
print(len(src), len(tgt), len(d)); print(manifest[["defect_id","rows_affected"]])
