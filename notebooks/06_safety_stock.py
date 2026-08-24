# %%
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent

segmentation = pd.read_csv(
    project_root / "data" / "processed" / "segmentation.csv",
    index_col="Product_Category"
)

segmentation.head()
# %%

# %%
from sqlalchemy import create_engine

db_path = project_root / "sql" / "supply_chain.db"
engine = create_engine(f"sqlite:///{db_path}")
weekly = pd.read_sql("SELECT * FROM weekly_demand", engine)

demand_stats = (
    weekly
    .groupby("Product_Category")["Weekly_Demand"]
    .agg(["mean", "std"])
)
demand_stats.columns = ["mean_demand", "std_demand"]

segmentation = segmentation.join(demand_stats)
segmentation.head()
# %%
# %%
z_lookup = {
    "AX": 2.05,
    "BX": 1.65,
    "BY": 1.48,
    "CX": 1.41,
    "CY": 1.18,
    "CZ": 1.04,
}

segmentation["Z"] = segmentation["ABC_XYZ"].map(z_lookup)
segmentation
# %%
# %%
lead_time_days = 37.5  # midpoint of your 30–45 day assumption
lead_time_weeks = lead_time_days / 7

segmentation["safety_stock"] = (
    segmentation["Z"] * segmentation["std_demand"] * (lead_time_weeks ** 0.5)
)

segmentation[["ABC_XYZ", "mean_demand", "std_demand", "Z", "safety_stock"]].sort_values("ABC_XYZ")