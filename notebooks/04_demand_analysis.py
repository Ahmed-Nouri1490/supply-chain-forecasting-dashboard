# %%
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

project_root = Path(__file__).resolve().parent.parent
db_path = project_root / "sql" / "supply_chain.db"
engine = create_engine(f"sqlite:///{db_path}")

weekly = pd.read_sql("SELECT * FROM weekly_demand", engine)
weekly.head()
# %%

#so weekly is the database of 7082 rows per category-week
# group by - splits the data into groups based on the named critea so 33 groups for each product category

cv_by_category = (
    weekly
    .groupby("Product_Category")["Weekly_Demand"]
    .agg(["mean", "std"]) # computes the mean and standard deviation of weekly demand for each product category
)

cv_by_category.columns = ["mean_demand", "std_demand"]
cv_by_category["cv"] = cv_by_category["std_demand"] / cv_by_category["mean_demand"]

cv_by_category = cv_by_category.sort_values("cv")
cv_by_category
# %%

## SEASONAL DECOMPOSTIION


from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

total_weekly = (
    weekly
    .groupby("Week")["Weekly_Demand"]
    .sum()
)

total_weekly.index = pd.to_datetime(total_weekly.index)

decomposition = seasonal_decompose(total_weekly, model="additive", period=52)
decomposition.plot()
plt.show()
# %%

# Category 019 seasonal decomposition

category_019 = (
    weekly[weekly["Product_Category"] == "Category_019"]
    .set_index("Week")["Weekly_Demand"]
)

category_019.index = pd.to_datetime(category_019.index)

decomposition_019 = seasonal_decompose(category_019, model="additive", period=52)
decomposition_019.plot()
plt.show()

# %%
## Category 017 seasonal decomposition

category_017 = (
    weekly[weekly["Product_Category"] == "Category_017"]
    .set_index("Week")["Weekly_Demand"]
)

category_017.index = pd.to_datetime(category_017.index)

decomposition_017 = seasonal_decompose(category_017, model="additive", period=52)
decomposition_017.plot()
plt.show()
# %%
