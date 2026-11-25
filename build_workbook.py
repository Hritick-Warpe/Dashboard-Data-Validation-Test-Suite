import os, sys, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_data as v
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter

BASE = v.BASE
clean = v.run_checks("clean").set_index("test_id")
dfct = v.run_checks("defective").set_index("test_id")
key = pd.read_csv(os.path.join(v.DATA, "_defect_answer_key.csv"))

F = "Arial"
HDR = PatternFill("solid", fgColor="000000"); GREEN = PatternFill("solid", fgColor="86BC25")
thin = Side(style="thin", color="BFBFBF"); BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
def header(ws, row, cols):
    for i, c in enumerate(cols, 1):
        x = ws.cell(row=row, column=i, value=c); x.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        x.fill = HDR; x.alignment = Alignment(wrap_text=True, vertical="center"); x.border = BORDER
def body(ws, r0, r1, c1):
    for r in range(r0, r1+1):
        for c in range(1, c1+1):
            x = ws.cell(row=r, column=c); x.font = Font(name=F, size=10); x.border = BORDER
            x.alignment = Alignment(wrap_text=True, vertical="top")
def widths(ws, w):
    for i, x in enumerate(w, 1): ws.column_dimensions[get_column_letter(i)].width = x
def status_cf(ws, rng):
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"PASS"'], fill=PatternFill("solid", bgColor="C6EFCE"), font=Font(name=F, color="006100", bold=True)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"FAIL"'], fill=PatternFill("solid", bgColor="FFC7CE"), font=Font(name=F, color="9C0006", bold=True)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Not Run"'], fill=PatternFill("solid", bgColor="E7E6E6"), font=Font(name=F, color="595959", bold=True)))

wb = Workbook()

# ---------------- Read Me ----------------
ws = wb.active; ws.title = "Read Me"
lines = [
 ("Sales ETL & Dashboard Data Validation Test Suite", True),
 ("Scenario: an order system (source) feeds a reporting warehouse (target) that powers a Power BI sales dashboard. The tester validates the load and the dashboard.", False),
 ("", False),
 ("Sheets", True),
 ("Requirements - 13 requirements with acceptance criteria (REQ-01 to REQ-13).", False),
 ("Test Cases - 44 test cases. TC-001 to TC-032 were EXECUTED (SQL + Python) on the clean and defective loads. TC-033 to TC-044 are Power BI dashboard tests, 'Not Run' until you execute them in Power BI.", False),
 ("Traceability - requirement to test case coverage matrix.", False),
 ("Data Quality - results by data-quality dimension (completeness, accuracy, consistency, uniqueness, validity, timeliness).", False),
 ("Defect Log - defects found on the defective load, with reproduction steps, severity, business impact and retest status.", False),
 ("Seeded vs Found - compares defects found by the tests with the planted-defect answer key.", False),
 ("Test Summary - totals, pass rate, defects by severity and a release-readiness view (formulas).", False),
 ("", False),
 ("Important notes", True),
 ("All data is synthetic. The defects in target_fact_sales_defective.csv were seeded on purpose to practise the testing process.", False),
 ("'Actual' columns show the number of failing rows (or the variance amount for reconciliation checks). 0 means PASS.", False),
 ("Status values for TC-001 to TC-032 come from real runs of python/validate_data.py; the same checks are in sql/validation_queries.sql.", False),
 ("To complete the dashboard tests: open the Power BI file, run TC-033 to TC-044, then type your Actual result and set Status to PASS or FAIL. Summary formulas update automatically.", False),
]
for i, (t, b) in enumerate(lines, 1):
    c = ws.cell(row=i, column=1, value=t); c.font = Font(name=F, bold=b, size=14 if i == 1 else 10); c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 120

# ---------------- Requirements ----------------
reqs = [
 ("REQ-01","Completeness of load","Every non-cancelled source order is loaded to the target.","Row counts match and 0 source orders are missing in target.","High"),
 ("REQ-02","No unknown orders","Target contains only orders that exist in the source.","0 target orders without a source match.","Medium"),
 ("REQ-03","Uniqueness (R5)","order_id is unique in the target fact table.","0 duplicated order_id values.","High"),
 ("REQ-04","Cancelled orders excluded (R1)","Cancelled orders are not loaded.","0 rows with status = 'Cancelled' in target.","High"),
 ("REQ-05","Calculations (R2)","net_amount = order_amount x (1 - discount_pct/100); order_amount = quantity x unit_price.","0 rows with wrong amounts (1 cent tolerance).","Critical"),
 ("REQ-06","Derived fields (R3)","order_month is YYYY-MM of order_date.","0 mismatches.","Medium"),
 ("REQ-07","Referential integrity (R4)","Every customer, product and region in the target exists in its dimension table.","0 orphan keys.","High"),
 ("REQ-08","Valid, complete values (R6)","Key and measure columns are not NULL; quantity and price > 0; discount in allowed list; dates within range; status in allowed list.","0 invalid rows.","High"),
 ("REQ-09","Values match source (R7)","region, customer, quantity, price, date and amount in the target equal the source for the same order_id.","0 mismatches.","High"),
 ("REQ-10","Timeliness (R8)","Every target row carries the latest batch load_date (2026-01-05).","0 rows with a different load_date.","Medium"),
 ("REQ-11","Reconciliation","Totals reconcile between source and target overall, by region and by month.","Variance = 0 (small rounding tolerance on net total).","Critical"),
 ("REQ-12","Dashboard functionality","Dashboard cards, slicers, drill-downs, export and refresh show values consistent with the database.","Dashboard numbers equal SQL results; filters update all visuals.","High"),
 ("REQ-13","Dashboard usability and performance","Dashboard loads quickly and is readable.","Loads in under 5 seconds; labels and number formats are clear.","Low"),
]
ws = wb.create_sheet("Requirements")
header(ws, 1, ["Req ID","Requirement","Description","Acceptance Criteria","Priority"])
for i, r in enumerate(reqs, 2):
    for j, x in enumerate(r, 1): ws.cell(row=i, column=j, value=x)
body(ws, 2, len(reqs)+1, 5); widths(ws, [10, 30, 62, 50, 10]); ws.freeze_panes = "A2"; ws.auto_filter.ref = f"A1:E{len(reqs)+1}"

# ---------------- Test cases ----------------
sev = {"REQ-01":"High","REQ-02":"Medium","REQ-03":"High","REQ-04":"High","REQ-05":"Critical","REQ-06":"Medium",
       "REQ-07":"High","REQ-08":"High","REQ-09":"High","REQ-10":"Medium","REQ-11":"Critical"}
pbi = [
 ("REQ-12","Total Net Sales card equals SQL total","Functional","Accuracy","1. Open dashboard on clean data. 2. Note Total Net Sales card. 3. Run: SELECT SUM(net_amount) FROM target_fact_sales_clean; 4. Compare.","Card value equals SQL result (variance 0.00).","High"),
 ("REQ-12","Total Orders card equals distinct order count","Functional","Accuracy","1. Note Total Orders card. 2. Run: SELECT COUNT(DISTINCT order_id) FROM target_fact_sales_clean; 3. Compare.","Card value equals SQL count.","High"),
 ("REQ-12","Region slicer filters every visual","Functional","Consistency","1. Select region 'North'. 2. Check all visuals update. 3. Compare net sales with SQL for region N.","All visuals change; value equals SQL for that region.","High"),
 ("REQ-12","Month slicer: first and last month (boundary)","Boundary","Validity","1. Select 2025-01, then 2025-12. 2. Compare totals with SQL for each month.","Totals equal SQL; no missing data in boundary months.","Medium"),
 ("REQ-12","Combined region + segment slicers","Functional","Accuracy","1. Select region 'West' and segment 'Enterprise'. 2. Compare net sales with SQL using JOIN to dim_customer.","Value equals SQL result.","High"),
 ("REQ-12","Drill-down month to day","Functional","Accuracy","1. Drill from month to day on the trend visual. 2. Pick one day and compare with SQL.","Daily value equals SQL.","Medium"),
 ("REQ-12","Empty selection (negative)","Negative","Validity","1. Choose a filter combination with no data. 2. Observe visuals.","Visuals show blank or empty state, no errors.","Low"),
 ("REQ-12","Export data row count","Functional","Completeness","1. Use 'Export data' on a table visual. 2. Count rows in the exported file. 3. Compare with the visual.","Exported rows equal rows shown.","Medium"),
 ("REQ-12","Refresh after loading defective data","Regression","Accuracy","1. Point dashboard at target_fact_sales_defective. 2. Refresh. 3. Compare Total Net Sales with the clean value.","Totals differ from clean, confirming the dashboard exposes the seeded defects (record the variance).","High"),
 ("REQ-12","Dashboard vs SQL on defective load","Reconciliation","Accuracy","1. Compare dashboard totals on the defective load with TC-028/TC-029 variances.","Dashboard variance matches the SQL variance.","High"),
 ("REQ-13","Page load time (performance)","Performance","Timeliness","1. Open dashboard fresh. 2. Time until all visuals render.","Under 5 seconds.","Low"),
 ("REQ-13","Labels, titles and number formats (usability)","Usability","Validity","1. Review titles, axis labels, currency and thousands separators.","Clear titles; amounts formatted consistently.","Low"),
]
ws = wb.create_sheet("Test Cases")
cols = ["Test ID","Req ID","Scenario","Test Type","DQ Dimension","Steps / Query","Expected Result",
        "Actual (Clean)","Status (Clean)","Actual (Defective)","Status (Defective)","Severity","Execution"]
header(ws, 1, cols)
r = 2
for cid, req, name, ttype, dim, exp, tol, sql, fn in v.CHECKS:
    vals = [cid, req, name, ttype, dim, f"Run query {cid} in sql/validation_queries.sql (or python/validate_data.py). failures = result.",
            exp, float(clean.loc[cid,"failures"]), clean.loc[cid,"status"], float(dfct.loc[cid,"failures"]), dfct.loc[cid,"status"], sev[req], "Executed"]
    for j, x in enumerate(vals, 1): ws.cell(row=r, column=j, value=x)
    r += 1
n = len(v.CHECKS)
for i, (req, name, ttype, dim, steps, exp, sv) in enumerate(pbi, n+1):
    vals = [f"TC-{i:03d}", req, name, ttype, dim, steps, exp, None, "Not Run", None, "Not Run", sv, "Pending (Power BI)"]
    for j, x in enumerate(vals, 1): ws.cell(row=r, column=j, value=x)
    r += 1
last_tc = r-1
body(ws, 2, last_tc, len(cols)); widths(ws, [9,9,44,18,14,52,38,12,11,13,12,10,16])
for rr in range(2, last_tc+1):
    for cc in (8, 10): ws.cell(row=rr, column=cc).number_format = "#,##0.00"
status_cf(ws, f"I2:I{last_tc}"); status_cf(ws, f"K2:K{last_tc}")
ws.freeze_panes = "D2"; ws.auto_filter.ref = f"A1:M{last_tc}"

# ---------------- Traceability ----------------
ws = wb.create_sheet("Traceability")
header(ws, 1, ["Req ID","Requirement","Priority","# Test Cases","# Executed","Test IDs"])
for i, q in enumerate(reqs, 2):
    ids = [x for x in [t for t in [ws2 for ws2 in []]]]
    tc_ids = [c[0] for c in v.CHECKS if c[1] == q[0]] + [f"TC-{k:03d}" for k, p in enumerate(pbi, n+1) if p[0] == q[0]]
    ws.cell(row=i, column=1, value=q[0]); ws.cell(row=i, column=2, value=q[1]); ws.cell(row=i, column=3, value=q[4])
    ws.cell(row=i, column=4, value=f"=COUNTIF('Test Cases'!$B$2:$B${last_tc},A{i})")
    ws.cell(row=i, column=5, value=f"=COUNTIFS('Test Cases'!$B$2:$B${last_tc},A{i},'Test Cases'!$M$2:$M${last_tc},\"Executed\")")
    ws.cell(row=i, column=6, value=", ".join(tc_ids))
body(ws, 2, len(reqs)+1, 6); widths(ws, [10, 34, 10, 12, 12, 90]); ws.freeze_panes = "A2"

# ---------------- Defect log ----------------
def f(tid, col="failures", df=dfct):
    x = df.loc[tid, col]; return int(x) if float(x).is_integer() else float(x)
D = [
 ("DEF-01","Duplicate order_id loaded into target","ETL load","TC-004 (also affects TC-001, TC-028)","REQ-03",
  f"Run TC-004 on target_fact_sales_defective.",
  "0 duplicated order_ids", f"{f('TC-004')} order_ids appear more than once", "High","High",
  "Sales and order counts are overstated on the dashboard.",["TC-004"]),
 ("DEF-02","Source orders missing in target","ETL load","TC-002 (also affects TC-001, TC-028, TC-030, TC-031)","REQ-01",
  "Run TC-002 (LEFT JOIN source to target).",
  "0 missing orders", f"{f('TC-002')} non-cancelled source orders are not in target", "Critical","High",
  "Revenue is understated; regional and monthly totals do not reconcile with the source.",["TC-002"]),
 ("DEF-03","net_amount ignores discount","Transformation","TC-010 (also affects TC-029)","REQ-05",
  "Run TC-010; compare net_amount with order_amount x (1 - discount%).",
  "net_amount = order_amount x (1 - discount%)", f"{f('TC-010')} rows have net_amount equal to order_amount; net total variance {f('TC-029'):,.2f}", "Critical","High",
  "Net sales are overstated by about 162 thousand, which misstates revenue and margin.",["TC-010","TC-029"]),
 ("DEF-04","NULL net_amount","ETL load","TC-008","REQ-08",
  "Run TC-008.",
  "0 NULL net_amount", f"{f('TC-008')} rows with NULL net_amount", "High","Medium",
  "Rows drop out of net sales totals and averages.",["TC-008"]),
 ("DEF-05","Cancelled orders loaded to target (rule R1)","Business rule","TC-005","REQ-04",
  "Run TC-005.",
  "0 cancelled orders", f"{f('TC-005')} cancelled orders present", "High","High",
  "Cancelled sales are counted as revenue.",["TC-005"]),
 ("DEF-06","customer_id not found in dim_customer (orphan)","Referential integrity","TC-013, TC-022","REQ-07",
  "Run TC-013 and TC-022.",
  "0 orphan customers", f"{f('TC-013')} rows with customer_id 9999 (does not exist); {f('TC-022')} differ from source", "High","Medium",
  "Rows cannot be attributed to a customer or segment in segment reports.",["TC-013","TC-022"]),
 ("DEF-07","Future-dated orders","Data validity","TC-019, TC-025","REQ-08",
  "Run TC-019 and TC-025.",
  "0 orders after 2026-01-05", f"{f('TC-019')} orders dated 2027-03-15", "Medium","Medium",
  "Creates a phantom month (2027-03) in trend charts.",["TC-019","TC-025"]),
 ("DEF-08","Negative quantity","Data validity","TC-016 (also TC-011, TC-023)","REQ-08",
  "Run TC-016, TC-011 and TC-023.",
  "quantity > 0", f"{f('TC-016')} rows with quantity <= 0", "High","Medium",
  "Quantities and amounts become inconsistent; unit-based KPIs are wrong.",["TC-016","TC-023"]),
 ("DEF-09","region_code differs from source","Source-to-target","TC-021 (also TC-030)","REQ-09",
  "Run TC-021 and TC-030.",
  "Region equals the source region", f"{f('TC-021')} rows have a different region; {f('TC-030')} regions do not reconcile", "High","Medium",
  "Regional sales are shifted to the wrong region.",["TC-021","TC-030"]),
 ("DEF-10","Stale load_date on part of the load","Timeliness","TC-027","REQ-10",
  "Run TC-027.",
  "All rows have load_date 2026-01-05", f"{f('TC-027')} rows have load_date 2025-06-01", "Medium","Low",
  "Part of the data looks stale and refresh monitoring becomes unreliable.",["TC-027"]),
]
ws = wb.create_sheet("Defect Log")
header(ws, 1, ["Defect ID","Title","Area","Linked Tests","Req ID","Steps to Reproduce","Expected","Actual","Severity","Priority","Business Impact","Found In","Status","Retest Evidence"])
for i, d in enumerate(D, 2):
    closed = all(clean.loc[t, "status"] == "PASS" for t in d[11])
    vals = list(d[:11]) + ["target_fact_sales_defective", "Closed" if closed else "Open",
        "Retested on corrected load (target_fact_sales_clean): " + ", ".join(f"{t} PASS" for t in d[11]) if closed else "Retest failed"]
    for j, x in enumerate(vals, 1): ws.cell(row=i, column=j, value=x)
body(ws, 2, len(D)+1, 14); widths(ws, [9,34,16,24,9,34,30,44,10,9,40,26,9,46]); ws.freeze_panes = "C2"; ws.auto_filter.ref = f"A1:N{len(D)+1}"
dl_last = len(D)+1

# ---------------- Seeded vs Found ----------------
ws = wb.create_sheet("Seeded vs Found")
header(ws, 1, ["Defect ID","Seeded defect (answer key)","Quality dimension","Rows seeded","Rows found by tests","Detected?","Note"])
notes = {"DEF-01":"Matches the seeded count.","DEF-02":"Matches the seeded count.",
 "DEF-03":"Found rows can be slightly lower than seeded if a later seeded defect overwrote the same row (e.g. NULL net_amount).",
 "DEF-04":"Matches the seeded count.","DEF-05":"Matches the seeded count.","DEF-06":"Matches the seeded count.","DEF-07":"Matches the seeded count.",
 "DEF-08":"Matches the seeded count.","DEF-09":"Fewer found than seeded: some rows were already in region 'C', so the seeded change did not alter them.",
 "DEF-10":"Matches the seeded count."}
fm = {"DEF-01":"TC-004","DEF-02":"TC-002","DEF-03":"TC-010","DEF-04":"TC-008","DEF-05":"TC-005","DEF-06":"TC-013","DEF-07":"TC-019","DEF-08":"TC-016","DEF-09":"TC-021","DEF-10":"TC-027"}
for i, row in enumerate(key.itertuples(), 2):
    if int(f(fm[row.defect_id])) == int(row.rows_affected): notes[row.defect_id] = "Matches the seeded count."
    ws.cell(row=i, column=1, value=row.defect_id); ws.cell(row=i, column=2, value=row.description)
    ws.cell(row=i, column=3, value=row.quality_dimension); ws.cell(row=i, column=4, value=int(row.rows_affected))
    ws.cell(row=i, column=5, value=int(f(fm[row.defect_id]))); ws.cell(row=i, column=6, value=f'=IF(E{i}>0,"Yes","No")')
    ws.cell(row=i, column=7, value=notes[row.defect_id])
body(ws, 2, len(key)+1, 7); widths(ws, [10, 42, 18, 12, 18, 11, 80])
ws.cell(row=len(key)+3, column=1, value="Defects detected").font = Font(name=F, bold=True, size=10)
ws.cell(row=len(key)+3, column=5, value=f'=COUNTIF(F2:F{len(key)+1},"Yes")&" of "&COUNTA(A2:A{len(key)+1})').font = Font(name=F, bold=True, size=10)

# ---------------- Data quality ----------------
ws = wb.create_sheet("Data Quality")
header(ws, 1, ["Dimension","# Checks","Clean: Pass","Clean: Fail","Defective: Pass","Defective: Fail","Defective pass %"])
dims = ["Completeness","Accuracy","Consistency","Uniqueness","Validity","Timeliness"]
TC = "'Test Cases'"
for i, dm in enumerate(dims, 2):
    ws.cell(row=i, column=1, value=dm)
    ws.cell(row=i, column=2, value=f"=COUNTIF({TC}!$E$2:$E${last_tc},A{i})-COUNTIFS({TC}!$E$2:$E${last_tc},A{i},{TC}!$I$2:$I${last_tc},\"Not Run\")")
    ws.cell(row=i, column=3, value=f"=COUNTIFS({TC}!$E$2:$E${last_tc},A{i},{TC}!$I$2:$I${last_tc},\"PASS\")")
    ws.cell(row=i, column=4, value=f"=COUNTIFS({TC}!$E$2:$E${last_tc},A{i},{TC}!$I$2:$I${last_tc},\"FAIL\")")
    ws.cell(row=i, column=5, value=f"=COUNTIFS({TC}!$E$2:$E${last_tc},A{i},{TC}!$K$2:$K${last_tc},\"PASS\")")
    ws.cell(row=i, column=6, value=f"=COUNTIFS({TC}!$E$2:$E${last_tc},A{i},{TC}!$K$2:$K${last_tc},\"FAIL\")")
    ws.cell(row=i, column=7, value=f"=IF(B{i}=0,0,E{i}/B{i})"); ws.cell(row=i, column=7).number_format = "0%"
t = len(dims)+2
ws.cell(row=t, column=1, value="Total")
for c in range(2, 7):
    L = get_column_letter(c); ws.cell(row=t, column=c, value=f"=SUM({L}2:{L}{t-1})")
ws.cell(row=t, column=7, value=f"=IF(B{t}=0,0,E{t}/B{t})"); ws.cell(row=t, column=7).number_format = "0%"
body(ws, 2, t, 7)
for c in range(1, 8): ws.cell(row=t, column=c).font = Font(name=F, bold=True, size=10)
ws.cell(row=t+2, column=1, value="Counts include only executed tests (TC-001 to TC-032). Dashboard tests are excluded until run.").font = Font(name=F, italic=True, size=9)
widths(ws, [16, 10, 12, 12, 16, 16, 16])

# ---------------- Test summary ----------------
ws = wb.create_sheet("Test Summary")
ws["A1"] = "Test Summary Report"; ws["A1"].font = Font(name=F, bold=True, size=14)
rows = [
 ("Test cases designed", f"=COUNTA({TC}!A2:A{last_tc})"),
 ("Executed (data validation)", f"=COUNTIF({TC}!M2:M{last_tc},\"Executed\")"),
 ("Not yet run (Power BI)", f"=COUNTIF({TC}!I2:I{last_tc},\"Not Run\")"),
 ("", None),
 ("CLEAN load: passed", f"=COUNTIF({TC}!I2:I{last_tc},\"PASS\")"),
 ("CLEAN load: failed", f"=COUNTIF({TC}!I2:I{last_tc},\"FAIL\")"),
 ("CLEAN load: pass rate", "=IF(B3=0,0,B6/B3)"),
 ("", None),
 ("DEFECTIVE load: passed", f"=COUNTIF({TC}!K2:K{last_tc},\"PASS\")"),
 ("DEFECTIVE load: failed", f"=COUNTIF({TC}!K2:K{last_tc},\"FAIL\")"),
 ("DEFECTIVE load: pass rate", "=IF(B3=0,0,B10/B3)"),
 ("", None),
 ("Defects logged", f"=COUNTA('Defect Log'!A2:A{dl_last})"),
 ("Defects closed (retested on corrected load)", f"=COUNTIF('Defect Log'!M2:M{dl_last},\"Closed\")"),
 ("Defects open", f"=COUNTIF('Defect Log'!M2:M{dl_last},\"Open\")"),
 ("", None),
 ("Release readiness: defective load", '=IF(B11>0,"NOT READY - blocking defects found","READY")'),
 ("Release readiness: corrected load (data tests only)", '=IF(B7=0,"READY on data checks; run dashboard tests before sign-off","NOT READY")'),
]
for i, (a, b) in enumerate(rows, 3):
    ws.cell(row=i, column=1, value=a).font = Font(name=F, size=10, bold=bool(a))
    if b is not None:
        c = ws.cell(row=i, column=2, value=b); c.font = Font(name=F, size=10); c.alignment = Alignment(wrap_text=True)
for rr in (9, 13): ws.cell(row=rr, column=2).number_format = "0%"
# fix references: rows are offset (start row 3)
ws["B9"] = "=IF(B4=0,0,B7/B4)"; ws["B13"] = "=IF(B4=0,0,B11/B4)"
ws["B19"] = '=IF(B12>0,"NOT READY - blocking defects found","READY")'
ws["B20"] = '=IF(B8=0,"READY on data checks; run dashboard tests before sign-off","NOT READY")'
ws["A22"] = "Defects by severity"; ws["A22"].font = Font(name=F, bold=True, size=10)
header(ws, 23, ["Severity", "Count"])
for i, s in enumerate(["Critical", "High", "Medium", "Low"], 24):
    ws.cell(row=i, column=1, value=s); ws.cell(row=i, column=2, value=f"=COUNTIF('Defect Log'!I2:I{dl_last},A{i})")
body(ws, 24, 27, 2)
ch = BarChart(); ch.type = "col"; ch.title = "Defects by severity"; ch.roundedCorners = False
ch.y_axis.title = "Defects"; ch.x_axis.title = "Severity"
ch.add_data(Reference(ws, min_col=2, min_row=23, max_row=27), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=24, max_row=27))
ch.legend = None; ch.x_axis.delete = False; ch.y_axis.delete = False; ch.height = 7; ch.width = 12
ws.add_chart(ch, "D22")
widths(ws, [52, 52, 4, 14, 14, 14])

wb.move_sheet("Test Summary", offset=-(len(wb.sheetnames)-2))
out = os.path.join(BASE, "reports", "QA_Test_Suite.xlsx"); wb.save(out); print("saved", out, "last_tc", last_tc)
