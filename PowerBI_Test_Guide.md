# Power BI: build and test guide (TC-033 to TC-044)

I could not create a .pbix file in this environment, so build the dashboard yourself (about 1-2 hours) and run the 12 dashboard tests.

## 1. Connect data
1. Power BI Desktop > Get Data > MySQL database (or Text/CSV if you skip MySQL).
2. Load `target_fact_sales_clean`, `dim_customer`, `dim_product`, `dim_region`.
3. Model view: relate fact.customer_id to dim_customer, fact.product_id to dim_product, fact.region_code to dim_region (many-to-one).

## 2. Measures
```
Total Net Sales = SUM(target_fact_sales_clean[net_amount])
Total Orders    = DISTINCTCOUNT(target_fact_sales_clean[order_id])
Total Quantity  = SUM(target_fact_sales_clean[quantity])
```

## 3. Visuals (one page)
- Cards: Total Net Sales, Total Orders.
- Line chart: Total Net Sales by order_month, with drill-down to order_date.
- Bar chart: Total Net Sales by region_name.
- Table: order_id, order_date, region_name, net_amount (for the export test).
- Slicers: region_name, segment, order_month.

## 4. Run the tests
Open the Test Cases sheet, filter Execution = "Pending (Power BI)". For each test: follow the steps, type what you saw in "Actual (Clean)", and set Status to PASS or FAIL. For TC-041 and TC-042, repoint the data to `target_fact_sales_defective`, refresh, and fill the "Actual (Defective)" column. Compare with SQL using the queries in `sql/`. Screenshot each result into a `screenshots/` folder.

## 5. After running
The Test Summary sheet updates by itself. If a test fails, add a row to the Defect Log.
