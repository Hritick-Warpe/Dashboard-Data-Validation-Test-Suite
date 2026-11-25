# Test Summary Report: Sales ETL and Dashboard Validation

**Scope:** validation of the order-system to warehouse load (`source_orders` to `target_fact_sales`) and the Power BI sales dashboard built on it.
**Data:** synthetic. 50,000 source orders; 42,474 expected target rows. Defects in the "defective" load were seeded on purpose.
**Tools:** MySQL (SQL checks), Python/Pandas (automated checks), Excel (test cases, defect log), Power BI (dashboard tests).

## Results
| Item | Count |
|---|---|
| Test cases designed | 44 |
| Data-validation tests executed (TC-001 to TC-032) | 32 |
| Dashboard tests not yet run (TC-033 to TC-044) | 12 |
| Clean load: passed / failed | 32 / 0 |
| Defective load: passed / failed | 13 / 19 |
| Defects logged | 10 (2 Critical, 6 High, 2 Medium) |
| Defects closed after retest on the corrected load | 10 |
| Seeded defects detected | 10 of 10 |

## Defects found on the defective load
| ID | Defect | Severity | Rows / variance |
|---|---|---|---|
| DEF-01 | Duplicate order_id | High | 25 order_ids |
| DEF-02 | Source orders missing in target | Critical | 40 orders |
| DEF-03 | net_amount ignores discount | Critical | 60 rows; net total off by about 161,975 |
| DEF-04 | NULL net_amount | High | 30 rows |
| DEF-05 | Cancelled orders loaded | High | 35 rows |
| DEF-06 | Orphan customer_id | High | 20 rows |
| DEF-07 | Future-dated orders | Medium | 15 rows |
| DEF-08 | Negative quantity | High | 12 rows |
| DEF-09 | Region differs from source | High | 38 rows |
| DEF-10 | Stale load_date | Medium | 500 rows |

## Observations
- Row counts alone are misleading: the defective load is only 15 rows short (25 duplicates added, 40 orders missing), so a count check hides two separate defects. Key-level checks (TC-002, TC-004) catch them.
- The overall order_amount total is off by about 77,448 on the defective load, and 8 regions (of 8) and 12 months (of 12) differ from the source, so the dashboard would show wrong numbers.

## Release readiness
- **Defective load: NOT READY.** Two critical and six high-severity defects.
- **Corrected load: READY on data checks.** All 32 executed tests pass. Dashboard tests (TC-033 to TC-044) must be run in Power BI before final sign-off.

## Limitations
- Synthetic data and seeded defects, used to demonstrate the testing process.
- Dashboard tests are written but not executed in this deliverable.
