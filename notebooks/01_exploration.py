# %% [markdown]
# # Phase 0: First-Pass Exploration — Historical Product Demand (Manufacturing)
#
# Real product demand data for a global manufacturing company: thousands of
# products, dozens of categories, 4 regional warehouses, ~7 years of history.
#
# No shipping/lead-time fields in this dataset — lead time will be an assumed
# distribution in Phase 4, not something pulled from a column. Note that here.

# %%
import pandas as pd
import numpy as np

pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 160)

# %%
from pathlib import Path
path = Path(__file__).resolve().parent.parent / "data" / "raw" / "Historical Product Demand.csv"


df = pd.read_csv(path)
df.shape

# %%
df.columns.tolist()

# %%
df.dtypes

# %%
df.head(10)

# %% [markdown]
# ## Known gotcha #1: Order_Demand is text, negatives are wrapped in parentheses
# e.g. "(1000)" instead of "-1000". Clean this before anything numeric.

# %%
df["Order_Demand"].astype(str).str.contains(r"\(").sum()

# %%
df["Order_Demand_clean"] = (
    df["Order_Demand"]
    .astype(str)
    .str.replace(r"[()]", "", regex=True)
    .astype(float)
)
# Restore the negative sign for parenthesized (returned) values
was_negative = df["Order_Demand"].astype(str).str.contains(r"\(")
df.loc[was_negative, "Order_Demand_clean"] = -df.loc[was_negative, "Order_Demand_clean"]

df["Order_Demand_clean"].describe()

# %%
print("Negative (return) rows:", (df["Order_Demand_clean"] < 0).sum())
print("Zero-demand rows:", (df["Order_Demand_clean"] == 0).sum())

# %% [markdown]
# ## Known gotcha #2: some dates are malformed / out of expected range

# %%
df["Date_parsed"] = pd.to_datetime(df["Date"], errors="coerce")
print("Unparseable dates:", df["Date_parsed"].isna().sum(), "out of", len(df))

# %%
valid = df.dropna(subset=["Date_parsed"]).copy()
print("Date range:", valid["Date_parsed"].min(), "to", valid["Date_parsed"].max())

# %%
# Sanity check: rows per year - flag anything before ~2011 or after Jan 2017 as suspect
valid["Date_parsed"].dt.year.value_counts().sort_index()

# %% [markdown]
# ## Product / warehouse / category granularity

# %%
print("Warehouses:", df["Warehouse"].nunique(), df["Warehouse"].unique())
print("Product categories:", df["Product_Category"].nunique())
print("Products:", df["Product_Code"].nunique())

# %%
df.groupby("Product_Category")["Product_Code"].nunique().sort_values(ascending=False).head(15)

# %%
# Rows per product - some products will have far more history than others
df.groupby("Product_Code").size().describe()

# %% [markdown]
# ## Demand concentration by warehouse and category
# (early look — this feeds ABC/XYZ segmentation later)

# %%
valid.groupby("Warehouse")["Order_Demand_clean"].sum().sort_values(ascending=False)

# %%
valid.groupby("Product_Category")["Order_Demand_clean"].sum().sort_values(ascending=False).head(15)

# %% [markdown]
# ## Missing values

# %%
df.isna().sum().sort_values(ascending=False)

# %% [markdown]
# ## No lead-time / shipping fields — flag for Phase 4
#
# This dataset has no order-to-delivery data. Per the dataset's own description,
# products ship via ocean from global manufacturing sites to 4 regional
# warehouses, "normally taking more than one month." Phase 4 (safety stock,
# reorder points, disruption sim) will use an assumed lead-time distribution
# (e.g. ~30-45 days, with variance) rather than a data-derived one — document
# this assumption explicitly in the README.

# %% [markdown]
# ## Notes (fill in after running)
#
# - Date range (valid rows):
# - % of rows with unparseable dates:
# - # products / categories / warehouses:
# - Any single warehouse or category dominating demand:
# - Anything unexpected in missing values:
# %%


df.nlargest(10, "Order_Demand_clean")[["Product_Code", "Warehouse", "Product_Category", "Date", "Order_Demand_clean"]]
# %%
