# Superstore Dataset Documentation

## 1. Overview and Source

This application uses transaction-level sales data from the widely recognized Superstore dataset available on Kaggle:

- **Source URL:** [https://www.kaggle.com/datasets/vivek468/superstore-dataset-final](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
- **Dataset Title:** Superstore Dataset
- **Author / Publisher:** Vivek Singh ([@vivek468](https://www.kaggle.com/vivek468))
- **Original Context:** Derived from sample business intelligence datasets originally created for Tableau and Power BI retail performance analysis.
- **License / Terms of Use:** Shared on Kaggle under standard community/educational use terms. Suitable for learning, portfolio demonstration, and analytical research.

## 2. Dataset Schema (21 Columns)

The dataset contains transaction-level sales data covering orders across multiple years, product categories, and geographical regions:

| Column Name | Type | Description |
|---|---|---|
| `Row ID` | Integer | Unique identifier for each record row |
| `Order ID` | String | Unique identifier for each customer transaction |
| `Order Date` | Date (M/D/YYYY) | Date when the order was placed |
| `Ship Date` | Date (M/D/YYYY) | Date when the items were dispatched |
| `Ship Mode` | String | Shipping class (Standard Class, Second Class, First Class, Same Day) |
| `Customer ID` | String | Unique customer identifier |
| `Customer Name` | String | Customer full name |
| `Segment` | String | Market segment (`Consumer`, `Corporate`, `Home Office`) |
| `Country` | String | Country (`United States`) |
| `City` | String | City of delivery |
| `State` | String | State of delivery |
| `Postal Code` | String / Numeric | Postal delivery code |
| `Region` | String | Geographic sales territory (`Central`, `East`, `South`, `West`) |
| `Product ID` | String | Unique product catalog ID |
| `Category` | String | Top-level product category (`Furniture`, `Office Supplies`, `Technology`) |
| `Sub-Category` | String | Granular product sub-category (e.g., `Chairs`, `Storage`, `Phones`) |
| `Product Name` | String | Full name and model description of the product |
| `Sales` | Float | Transaction gross revenue / sales amount in USD |
| `Quantity` | Integer | Number of units purchased |
| `Discount` | Float | Discount percentage applied (0.00 to 0.80) |
| `Profit` | Float | Net profit or loss for the line item in USD |

## 3. Manual Download Instructions

Per project rules and Kaggle terms, this application **never automatically downloads datasets or accesses Kaggle credentials**.

To use the dataset:

1. Visit [https://www.kaggle.com/datasets/vivek468/superstore-dataset-final](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final).
2. Click **Download** (requires a free Kaggle account).
3. Extract the downloaded ZIP archive.
4. Rename or copy the CSV file to:
   ```
   data/raw/superstore.csv
   ```
5. If you place the CSV under a different name or path, configure the `DATASET_PATH` environment variable in your `.env` file:
   ```dotenv
   DATASET_PATH=data/raw/superstore.csv
   ```

## 4. Analytical Notes & Data Governance

- **Line-Item vs. Order-Level:** An `Order ID` can appear on multiple rows if an order contains multiple line items. The analytics engine groups by `Order ID` when calculating order volume and average order value (AOV) to prevent double-counting orders.
- **Sales Interpretation:** The `Sales` column reflects transaction-level revenue for that line item after applied discounts, not recognized accrual accounting revenue.
- **No Database:** Data is read directly from CSV using Pandas. Analysis results are held in memory during the active session.
