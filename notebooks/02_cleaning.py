# %%
import pandas as pd
import numpy as np
from pathlib import Path

# Resolve path relative to this script's location, not the terminal's cwd
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
df = pd.read_csv(DATA_DIR / "Historical Product Demand.csv")

print(df.shape)
print(df.dtypes)
# %%
# %%
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

n_unparseable = df['Date'].isna().sum()
print(f"Unparseable dates: {n_unparseable} ({n_unparseable/len(df)*100:.2f}%)")

# Your decision: what do you do with these rows now that you can see the count?
# df = ___
# %%
# %%
# Look at the ACTUAL raw values behind the rows that failed to parse
unparseable_mask = df['Date'].isna()
raw_dates = pd.read_csv(DATA_DIR / "Historical Product Demand.csv")['Date']
print(raw_dates[unparseable_mask].value_counts().head(20))
# %%
# %%
print(raw_dates[unparseable_mask].value_counts(dropna=False).head(20))
# %%
# %%
print(raw_dates[unparseable_mask].isna().sum())   # how many are truly blank
print(raw_dates[unparseable_mask].head(60))        # eyeball the actual raw values
# %%
# %%
# Do these blank-date rows cluster around specific products or warehouses?
print(df.loc[unparseable_mask, 'Product_Category'].value_counts().head(10))
print(df.loc[unparseable_mask, 'Warehouse'].value_counts())
# %%
# %%
# How much actual demand volume is sitting in these blank-date rows?
print(df.loc[unparseable_mask, 'Order_Demand'].describe())

# Are these the same 3 high-volume products from your Phase 0 finding, or different ones?
print(df.loc[unparseable_mask, 'Product_Code'].value_counts().head(10))

# What % of Category_019's TOTAL demand volume do these blank-date rows represent?
cat19_total_demand = df.loc[df['Product_Category'] == 'Category_019', 'Order_Demand']
cat19_blank_demand = df.loc[unparseable_mask, 'Order_Demand']
# %%
# Check what non-numeric characters are actually in there before converting
sample = df['Order_Demand'].dropna().unique()
print([v for v in sample if not v.strip('-').replace(',', '').isdigit()][:20])
# %%
# %%
demand_vals = df['Order_Demand'].dropna().unique()

has_comma = [v for v in demand_vals if ',' in v]
has_paren = [v for v in demand_vals if '(' in v or ')' in v]
has_leading_trailing_space = [v for v in demand_vals if v != v.strip()]

print(f"Contains commas: {len(has_comma)} — e.g. {has_comma[:5]}")
print(f"Contains parentheses: {len(has_paren)} — e.g. {has_paren[:5]}")
print(f"Has whitespace padding: {len(has_leading_trailing_space)} — e.g. {has_leading_trailing_space[:5]}")
# %%
# %%
has_minus = [v for v in demand_vals if v.strip().startswith('-')]
print(f"Values with plain minus sign: {len(has_minus)} — e.g. {has_minus[:5]}")

# Row counts (not unique values) — this is what actually matters for matching your Phase 0 figure
n_paren_rows = df['Order_Demand'].str.contains(r'\(', na=False).sum()
n_minus_rows = df['Order_Demand'].str.strip().str.startswith('-', na=False).sum()
print(f"Rows with parentheses format: {n_paren_rows}")
print(f"Rows with plain minus format: {n_minus_rows}")
# %%
# %%
def clean_demand(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    
    is_negative = '(' in val
    val = val.strip('()-')  # strips whichever wrapping characters are present
    
    return -float(val) if is_negative else float(val)

df['Order_Demand_clean'] = df['Order_Demand'].apply(clean_demand)
print(df['Order_Demand_clean'].describe())

# %%
# %%
print((df['Order_Demand_clean'] < 0).sum())  # should be 10,469, matching your earlier count
# %%# %%
print(df.nlargest(5, 'Order_Demand_clean')[['Product_Code', 'Product_Category', 'Order_Demand_clean']])
print(df.nsmallest(5, 'Order_Demand_clean')[['Product_Code', 'Product_Category', 'Order_Demand_clean']])

# %%
cat19_total = df.loc[df['Product_Category'] == 'Category_019', 'Order_Demand_clean'].sum()
cat19_blank = df.loc[unparseable_mask, 'Order_Demand_clean'].sum()
pct = cat19_blank / cat19_total * 100
print(f"Category_019 total demand: {cat19_total:,.0f}")
print(f"Demand in blank-date rows: {cat19_blank:,.0f}")
print(f"Percentage: {pct:.2f}%")
# %%
# %%
# Decision: drop rows with unparseable/blank dates.
# Rationale: 11,239 rows (1.07%) — all isolated to Warehouse A, mostly Category_019,
# but confirmed to represent only 0.00% of Category_019's total demand volume.
# Safe to drop with no meaningful loss of signal.
df_clean = df[~unparseable_mask].copy()
print(f"Rows before: {len(df)}, after: {len(df_clean)}")
# %%

## Checking to either include negative demand values or not.

# %%
# Build a mask for negative demand rows, same pattern as unparseable_mask
negative_mask = df_clean['Order_Demand_clean'] < 0

# 1. Do negative rows cluster by Warehouse or Category?
print("--- By Warehouse ---")
print(df_clean.loc[negative_mask, 'Warehouse'].value_counts())
print("\n--- By Category (top 10) ---")
print(df_clean.loc[negative_mask, 'Product_Category'].value_counts().head(10))
# %%
# %%
# 2. Magnitude: how big are returns relative to total gross demand?
positive_sum = df_clean.loc[df_clean['Order_Demand_clean'] > 0, 'Order_Demand_clean'].sum()
negative_sum = df_clean.loc[negative_mask, 'Order_Demand_clean'].sum()  # will be negative
net_sum = df_clean['Order_Demand_clean'].sum()

print(f"Total positive demand: {positive_sum:,.0f}")
print(f"Total negative (returns): {negative_sum:,.0f}")
print(f"Returns as % of gross positive demand: {abs(negative_sum) / positive_sum * 100:.2f}%")
print(f"Net demand (positive + negative): {net_sum:,.0f}")
# %%
# %%
# 3. Do negative rows trace to specific products, or scattered like the blank dates were?
print(df_clean.loc[negative_mask, 'Product_Code'].value_counts().head(10))

# %%
# %%
# 4. Isolate the suspicious round-number outliers you spotted earlier
# (e.g. -999000, -500000) and see if they cluster separately from ordinary returns
large_negative_mask = df_clean['Order_Demand_clean'] <= -100000  # threshold, adjust after seeing the data

print(f"Rows with extreme negative values (<= -100,000): {large_negative_mask.sum()}")
print(df_clean.loc[large_negative_mask, ['Product_Code', 'Product_Category', 'Warehouse', 'Order_Demand_clean']]
      .sort_values('Order_Demand_clean'))

# Compare: distribution of "ordinary" negative returns, excluding the extreme ones
ordinary_returns = df_clean.loc[negative_mask & ~large_negative_mask, 'Order_Demand_clean']
print("\n--- Ordinary returns distribution (extreme outliers excluded) ---")
print(ordinary_returns.describe())
# %%
# %%
# Confirm the overlap directly: how many of the ORIGINAL blank-date rows were also negative?
overlap = df.loc[unparseable_mask, 'Order_Demand_clean'] < 0
print(f"Blank-date rows that were also negative: {overlap.sum()} of {unparseable_mask.sum()}")

# %%
