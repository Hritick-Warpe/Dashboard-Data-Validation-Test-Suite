# Sales ETL and Dashboard Data Validation Test Suite

A quality-engineering project that validates an order-system to warehouse load and the Power BI dashboard built on it. It follows the work described in an entry-level Quality Engineer role: requirements, test cases, source-to-target SQL validation, data-quality checks, defect logging and retesting, light test automation and test reporting.

All data is synthetic. Ten defects were seeded on purpose to practise the testing process.

## Folder guide
| Path | What it is |
|---|---|
| `data/` | Source orders, dimension tables, clean target, defective target, and the answer key for seeded defects |
| `sql/00_load_to_mysql.sql` | Creates MySQL tables, loads the CSVs, creates the `target_fact_sales` test view |
| `sql/validation_queries.sql` | 32 validation queries, one per test case (TC-001 to TC-032) |
| `python/validate_data.py` | Runs the same 32 checks with Pandas and prints a PASS/FAIL table |
| `python/generate_dataset.py` | Regenerates the dataset |
| `python/build_workbook.py` | Rebuilds the Excel test suite from the live results |
| `reports/QA_Test_Suite.xlsx` | Requirements, test cases, traceability, data-quality results, defect log, seeded-vs-found, summary |
| `reports/Test_Summary_Report.md` | One-page test summary |
| `evidence/` | `results_clean.csv`, `results_defective.csv` from the Python run |
| `docs/PowerBI_Test_Guide.md` | How to build the dashboard and run tests TC-033 to TC-044 |

## How to run
1. `pip install pandas numpy openpyxl`
2. `python python/validate_data.py` to run all checks on both loads.
3. In MySQL, run `sql/00_load_to_mysql.sql` (edit the file paths), then `sql/validation_queries.sql`. Switch the `target_fact_sales` view between `_clean` and `_defective`.
4. Open `reports/QA_Test_Suite.xlsx`.

## Results
- 44 test cases designed. 32 data-validation tests executed; 12 Power BI tests written, to be run in Power BI.
- Clean load: 32 of 32 pass. Defective load: 13 pass, 19 fail.
- 10 defects logged (2 Critical, 6 High, 2 Medium), all closed after retest on the corrected load. 10 of 10 seeded defects detected.
- The SQL queries and the Python checks were cross-checked and give the same results.

## Method
- Requirements and acceptance criteria are written first (REQ-01 to REQ-13) and traced to test cases.
- Test types: source-to-target, reconciliation, calculation, referential integrity, boundary, negative, timeliness and data-quality checks across six dimensions.
- Defects are logged with steps to reproduce, expected and actual results, severity, priority and business impact, then retested.

## Resume line (adjust the numbers if you add more)
Built a data-validation test suite for a sales ETL and Power BI dashboard on a synthetic 50,000-row dataset: wrote 44 test cases (32 executed with SQL and Python, 12 for the dashboard), found and logged 10 seeded defects with retesting, and reported results in a test summary.

Author
Hritick Warpe | 
Linkedin : https://www.linkedin.com/in/hritickwarpe
Email : hritickwarpe@gmail.com