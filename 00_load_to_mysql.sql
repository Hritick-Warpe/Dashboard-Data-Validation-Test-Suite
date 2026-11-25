-- Run in MySQL Workbench. Enable: SET GLOBAL local_infile = 1;
CREATE DATABASE IF NOT EXISTS qa_sales; USE qa_sales;

CREATE TABLE dim_region (region_code VARCHAR(3) PRIMARY KEY, region_name VARCHAR(30));
CREATE TABLE dim_customer (customer_id INT PRIMARY KEY, customer_name VARCHAR(40), segment VARCHAR(20), region_code VARCHAR(3), is_active TINYINT);
CREATE TABLE dim_product (product_id INT PRIMARY KEY, product_name VARCHAR(40), category VARCHAR(20), list_price DECIMAL(10,2));
CREATE TABLE source_orders (order_id INT, customer_id INT, product_id INT, order_date DATE, quantity INT, unit_price DECIMAL(10,2), discount_pct INT, order_amount DECIMAL(12,2), status VARCHAR(15), region_code VARCHAR(3), created_ts DATETIME);
CREATE TABLE target_fact_sales_clean (order_id INT, customer_id INT, product_id INT, order_date DATE, order_month CHAR(7), quantity INT, unit_price DECIMAL(10,2), discount_pct INT, order_amount DECIMAL(12,2), net_amount DECIMAL(12,2), status VARCHAR(15), region_code VARCHAR(3), load_date DATE);
CREATE TABLE target_fact_sales_defective LIKE target_fact_sales_clean;

-- Change the path to where you saved the CSVs. Repeat for each table.
LOAD DATA LOCAL INFILE 'C:/path/data/dim_region.csv' INTO TABLE dim_region FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'C:/path/data/dim_customer.csv' INTO TABLE dim_customer FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'C:/path/data/dim_product.csv' INTO TABLE dim_product FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'C:/path/data/source_orders.csv' INTO TABLE source_orders FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'C:/path/data/target_fact_sales_clean.csv' INTO TABLE target_fact_sales_clean FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'C:/path/data/target_fact_sales_defective.csv' INTO TABLE target_fact_sales_defective FIELDS TERMINATED BY ',' IGNORE 1 LINES (order_id,customer_id,product_id,order_date,order_month,quantity,unit_price,discount_pct,order_amount,@net,status,region_code,load_date)
  SET net_amount = NULLIF(@net,'');

-- After loading, point the test view at the load you want to test:
CREATE OR REPLACE VIEW target_fact_sales AS SELECT * FROM target_fact_sales_defective;
-- then run sql/validation_queries.sql (switch the view to _clean for the corrected load)
