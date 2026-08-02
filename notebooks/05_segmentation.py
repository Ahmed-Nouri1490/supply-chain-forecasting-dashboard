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
