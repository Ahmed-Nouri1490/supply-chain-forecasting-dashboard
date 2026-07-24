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
