# %%
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

project_root = Path(__file__).resolve().parent.parent

df_clean = pd.read_csv(project_root / 'data' / 'processed' / 'df_clean.csv')  # if you saved this earlier
weekly_demand_trimmed = pd.read_csv(project_root / 'data' / 'processed' / 'weekly_demand.csv')
# %%
