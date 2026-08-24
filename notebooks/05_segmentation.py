# %%
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

project_root = Path(__file__).resolve().parent.parent
db_path = project_root / "sql" / "supply_chain.db"
engine = create_engine(f"sqlite:///{db_path}")

weekly = pd.read_sql("SELECT * FROM weekly_demand", engine)

total_demand = (
    weekly
    .groupby("Product_Category")["Weekly_Demand"]
    .sum()
    .sort_values(ascending=False)
)

total_demand

# %%
abc_table = total_demand.to_frame(name="total_demand")
abc_table["pct_of_total"] = abc_table["total_demand"] / abc_table["total_demand"].sum()
abc_table["cumulative_pct"] = abc_table["pct_of_total"].cumsum()

abc_table
# %%

## DROP-OFF POINT

# %%
abc_table["drop_ratio"] = abc_table["pct_of_total"] / abc_table["pct_of_total"].shift(-1)

abc_table.sort_values("drop_ratio", ascending=False).head(10)


# %%
abc_table.head(25).sort_values("drop_ratio", ascending=False)
# %%
def classify_abc(cum_pct):
    if cum_pct <= 0.827:
        return "A"
    elif cum_pct <= 0.995:
        return "B"
    else:
        return "C"

abc_table["ABC_segment"] = abc_table["cumulative_pct"].apply(classify_abc)
abc_table["ABC_segment"].value_counts()


# %%
## XYZ Segmentation

# %%
cv_by_category = (
    weekly
    .groupby("Product_Category")["Weekly_Demand"]
    .agg(["mean", "std"])
)

cv_by_category.columns = ["mean_demand", "std_demand"]
cv_by_category["cv"] = cv_by_category["std_demand"] / cv_by_category["mean_demand"]
cv_by_category = cv_by_category.sort_values("cv")
cv_by_category

# %%
cv_by_category["cv"].describe()

# %%
cv_by_category["cv_diff"] = cv_by_category["cv"].diff()
cv_by_category.sort_values("cv_diff", ascending=False).head(10)
# %%
def classify_xyz(cv):
    if cv < 0.5:
        return "X"
    elif cv < 1.0:
        return "Y"
    else:
        return "Z"

cv_by_category["XYZ_segment"] = cv_by_category["cv"].apply(classify_xyz)
cv_by_category["XYZ_segment"].value_counts()
# %%

## Combine ABC and XYZ segments (3 x 3 matrix)

# %%
segmentation = abc_table[["ABC_segment"]].join(cv_by_category[["cv", "XYZ_segment"]])
segmentation["ABC_XYZ"] = segmentation["ABC_segment"] + segmentation["XYZ_segment"]
segmentation["ABC_XYZ"].value_counts()
# %%

## Save the segmentation results
# %%
output_path = project_root / "data" / "processed" / "segmentation.csv"
segmentation.to_csv(output_path)
print(f"Saved to {output_path}")
# %%
