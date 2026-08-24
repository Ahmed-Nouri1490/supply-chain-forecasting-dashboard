# %%
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

project_root = Path(__file__).resolve().parent.parent

df_clean = pd.read_csv(project_root / 'data' / 'processed' / 'df_clean.csv')  # if you saved this earlier
weekly_demand_trimmed = pd.read_csv(project_root / 'data' / 'processed' / 'weekly_demand.csv')
# %%
from sqlalchemy import create_engine

# Create the SQLite database file inside sql/ folder
db_path = project_root / 'sql' / 'supply_chain.db'
engine = create_engine(f'sqlite:///{db_path}')

df_clean.to_sql('demand_clean', engine, if_exists='replace', index=False)
weekly_demand_trimmed.to_sql('weekly_demand', engine, if_exists='replace', index=False)

print(f"Database created at: {db_path}")
print(f"Tables: demand_clean ({df_clean.shape[0]} rows), weekly_demand ({weekly_demand_trimmed.shape[0]} rows)")# %%

# %%
# %%
query = """
SELECT
    Week,
    Product_Category,
    Weekly_Demand,
    AVG(Weekly_Demand) OVER (
        PARTITION BY Product_Category
        ORDER BY Week
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS rolling_4wk_avg
FROM weekly_demand
ORDER BY Product_Category, Week
"""

rolling_avg = pd.read_sql(query, engine)
rolling_avg.head(10)
# %%
# %%
print(df_clean.columns.tolist())

## JOIN FUNCTION
# %%
query = """
WITH warehouse_weekly AS (
    SELECT
        Week,
        Warehouse,
        Product_Category,
        SUM(Order_Demand_clean) AS warehouse_weekly_demand
    FROM demand_clean
    GROUP BY Week, Warehouse, Product_Category
)
SELECT
    w.Week,
    w.Product_Category,
    w.Warehouse,
    w.warehouse_weekly_demand,
    wd.Weekly_Demand AS category_weekly_demand,
    ROUND(100.0 * w.warehouse_weekly_demand / wd.Weekly_Demand, 1) AS pct_of_category
FROM warehouse_weekly w
JOIN weekly_demand wd
    ON w.Week = wd.Week AND w.Product_Category = wd.Product_Category
ORDER BY w.Product_Category, w.Week, w.Warehouse
"""
# line 66 shows that we order alphabetically by product category first then chronologically afterwards.
# as we can see that category_001 is sorted first,then category_002 and so on.

warehouse_share = pd.read_sql(query, engine)
warehouse_share.head(15)

# line 72 shows that we are taking only the first 15 rows of 
# %%
## AGGREGATION FUNCTION 

# %%
query_agg = """
SELECT
    Product_Category,
    COUNT(*) AS num_orders,
    SUM(Order_Demand_clean) AS total_demand,
    ROUND(AVG(Order_Demand_clean), 1) AS avg_order_size,
    SUM(CASE WHEN is_outlier = 1 THEN 1 ELSE 0 END) AS num_outliers
FROM demand_clean
GROUP BY Product_Category
ORDER BY total_demand DESC
"""

category_summary = pd.read_sql(query_agg, engine)
category_summary.head(10)

## Ranks all product categories by total demand, from highest to lowest.
# %%
