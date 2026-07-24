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
# %%
# Full detail on all 23 extreme outliers, sorted most negative first
extreme_rows = df_clean.loc[large_negative_mask].sort_values('Order_Demand_clean')
print(extreme_rows[['Product_Code', 'Product_Category', 'Warehouse', 'Date', 'Order_Demand_clean']].to_string())
# %%
# %%
# For each outlier, check if there's a matching large POSITIVE order for the
# same product within ~90 days — a -999000 return makes more sense if a
# +999000 order happened recently (suggests a cancelled/returned bulk order)
for idx, row in extreme_rows.iterrows():
    product = row['Product_Code']
    ret_date = row['Date']
    amount = abs(row['Order_Demand_clean'])

    window = df_clean[
        (df_clean['Product_Code'] == product) &
        (df_clean['Date'].between(ret_date - pd.Timedelta(days=90), ret_date + pd.Timedelta(days=90))) &
        (df_clean['Order_Demand_clean'] > 0)
    ]
    matching = window[np.isclose(window['Order_Demand_clean'], amount, rtol=0.1)]

    print(f"{product} | return: {row['Order_Demand_clean']:>10.0f} | date: {ret_date.date()} | matching positive orders nearby: {len(matching)}")
# %%
# Is this scale normal for the product, or wildly out of character?
# Compares the outlier return size to that product's own typical positive order size
for idx, row in extreme_rows.iterrows():
    product = row['Product_Code']
    product_orders = df_clean.loc[
        (df_clean['Product_Code'] == product) & (df_clean['Order_Demand_clean'] > 0),
        'Order_Demand_clean'
    ]
    if len(product_orders) > 0:
        print(f"{product}: return={row['Order_Demand_clean']:>10.0f} | "
              f"this product's typical order median={product_orders.median():>8.0f}, max={product_orders.max():>10.0f}")
# %%

# %%
# Decision: of the 23 extreme negative outliers, 21 are plausible (within the
# product's own historical order range, most matched to a recent bulk order).
# 2 are not: Product_0366 and Product_1250 both have returns that EXCEED
# their product's largest-ever recorded order — a red flag for a data error
# rather than a genuine return.

suspect_products = ['Product_0366', 'Product_1250']

suspect_mask = df_clean['Product_Code'].isin(suspect_products) & large_negative_mask

print(f"Rows being corrected: {suspect_mask.sum()}")
print(df_clean.loc[suspect_mask, ['Product_Code', 'Date', 'Order_Demand_clean']])
# %%
# %%
# Cap each suspect row at its product's own historical max positive order,
# rather than dropping the row entirely — preserves the fact a return happened,
# removes the implausible magnitude.

for product in suspect_products:
    product_max = df_clean.loc[
        (df_clean['Product_Code'] == product) & (df_clean['Order_Demand_clean'] > 0),
        'Order_Demand_clean'
    ].max()

    row_mask = (df_clean['Product_Code'] == product) & large_negative_mask
    df_clean.loc[row_mask, 'Order_Demand_clean'] = -product_max

    print(f"{product}: capped return to -{product_max:,.0f}")

# Confirm the fix
print(df_clean.loc[df_clean['Product_Code'].isin(suspect_products) & large_negative_mask,
                    ['Product_Code', 'Order_Demand_clean']])
# %%

## Checking for duplicates

# %%
# Duplicate rows — are there any exact repeats in the cleaned data?
n_duplicates = df_clean.duplicated().sum()
print(f"Exact duplicate rows: {n_duplicates}")

# If any exist, look at a few before deciding what to do
if n_duplicates > 0:
    print(df_clean[df_clean.duplicated(keep=False)].sort_values('Product_Code').head(10))
# %%
# %%
# Missing values in the other columns (not just Date, which you've already handled)
print(df_clean[['Product_Code', 'Warehouse', 'Product_Category', 'Order_Demand_clean']].isna().sum())
# %%
# %%
# How many TIMES does each duplicated combination repeat? 
# (2 repeats = plausible coincidence; 5+ repeats of the same exact row is more suspicious)
dup_counts = df_clean[df_clean.duplicated(keep=False)].groupby(
    ['Product_Code', 'Warehouse', 'Product_Category', 'Date', 'Order_Demand_clean']
).size()
print(dup_counts.value_counts().sort_index())
# %%
# %%
# What volume is actually at stake if you drop them?
# (i.e. if you keep only the FIRST of each duplicate group, how much demand disappears?)
total_before = df_clean['Order_Demand_clean'].sum()
df_deduped_test = df_clean.drop_duplicates()
total_after = df_deduped_test['Order_Demand_clean'].sum()
print(f"Rows: {len(df_clean):,} → {len(df_deduped_test):,}")
print(f"Demand volume: {total_before:,.0f} → {total_after:,.0f} "
      f"({(total_before - total_after) / total_before * 100:.1f}% removed)")
# %%

# %%
# How many distinct (Product_Code, Warehouse, Product_Category, Date) combinations
# exist in total, vs how many actually have more than one Order_Demand value logged?
# This tells you how "crowded" a single day/product/warehouse slot typically is.
n_unique_slots = df_clean.groupby(
    ['Product_Code', 'Warehouse', 'Product_Category', 'Date']
).size()
print(n_unique_slots.value_counts().head(10))

# %%
# %%
# Threshold-based dedup: only remove groups whose repeat count is implausible
# as coincidence, given that same-day multi-order slots are common in this
# dataset. Low-repeat duplicates (2-4x) are left alone as plausible genuine
# separate orders; high-repeat groups are treated as export/logging artifacts.

THRESHOLD = 5  # adjust based on where you judge coincidence becomes implausible

dup_group_sizes = df_clean.groupby(
    ['Product_Code', 'Warehouse', 'Product_Category', 'Date', 'Order_Demand_clean']
).size()

suspicious_groups = dup_group_sizes[dup_group_sizes >= THRESHOLD].index

idx = df_clean.set_index(
    ['Product_Code', 'Warehouse', 'Product_Category', 'Date', 'Order_Demand_clean']
).index

mask_to_dedupe = idx.isin(suspicious_groups)

df_clean = pd.concat([
    df_clean[~mask_to_dedupe],
    df_clean[mask_to_dedupe].drop_duplicates(subset=[
        'Product_Code', 'Warehouse', 'Product_Category', 'Date', 'Order_Demand_clean'
    ])
]).reset_index(drop=True)

print(f"Rows after threshold-based dedup: {len(df_clean):,}")
# %%
# %%
total_before = 5_104_149_931  # from your earlier full-dataset check
total_after = df_clean['Order_Demand_clean'].sum()
pct_removed = (total_before - total_after) / total_before * 100

print(f"Rows: 1,037,336 → {len(df_clean):,} ({(1037336 - len(df_clean))/1037336*100:.2f}% removed)")
print(f"Demand volume: {total_before:,.0f} → {total_after:,.0f} ({pct_removed:.2f}% removed)")
# %%
# %%
# Step 1: per-product mean, std, and count (on positive demand only —
# mixing in the capped negative returns would distort the "normal order size" baseline)
product_stats = df_clean[df_clean['Order_Demand_clean'] > 0].groupby('Product_Code')['Order_Demand_clean'].agg(
    ['mean', 'std', 'count']
).reset_index()

print(product_stats['count'].describe())
print(f"\nProducts with fewer than 10 orders: {(product_stats['count'] < 10).sum()} of {len(product_stats)}")
# %%
# %%
MIN_ORDERS = 10  # your call, based on what the count distribution above showed

product_stats['upper_bound'] = product_stats['mean'] + 3 * product_stats['std']
product_stats['lower_bound'] = product_stats['mean'] - 3 * product_stats['std']

df_clean = df_clean.merge(
    product_stats[['Product_Code', 'upper_bound', 'lower_bound', 'count']],
    on='Product_Code', how='left'
)

# Only flag as an outlier if the product has enough history to trust the bound
df_clean['is_outlier'] = (
    (df_clean['count'] >= MIN_ORDERS) &
    (df_clean['Order_Demand_clean'] > 0) &
    (
        (df_clean['Order_Demand_clean'] > df_clean['upper_bound']) |
        (df_clean['Order_Demand_clean'] < df_clean['lower_bound'])
    )
)

print(f"Rows flagged as outliers: {df_clean['is_outlier'].sum()}")
print(f"As % of total: {df_clean['is_outlier'].mean() * 100:.2f}%")
# %%
# %%
# What does the flagged set look like? Same instinct as always — inspect before deciding.
outliers = df_clean[df_clean['is_outlier']]

print("--- Top 10 largest flagged outliers ---")
print(outliers.nlargest(10, 'Order_Demand_clean')[
    ['Product_Code', 'Product_Category', 'Warehouse', 'Date', 'Order_Demand_clean']
])

print("\n--- Are outliers concentrated in specific categories? ---")
print(outliers['Product_Category'].value_counts().head(10))

print("\n--- Are outliers concentrated in specific products, or widespread? ---")
print(outliers['Product_Code'].value_counts().head(10))

print("\n--- How many UNIQUE products have at least one outlier flagged? ---")
print(f"{outliers['Product_Code'].nunique()} of {df_clean['Product_Code'].nunique()} products")
# %%
# %%
# Decision: outliers are NOT removed or capped. 92% of products (1,985/2,160)
# have at least one flagged row, and the pattern is broad-based across many
# categories rather than concentrated — consistent with genuine demand
# variability (bulk orders, seasonal spikes) rather than a data quality issue.
# The is_outlier flag is retained as metadata for later reference during
# forecasting and safety-stock analysis, not used to filter the dataset.

print(f"Final df_clean shape: {df_clean.shape}")
print(f"Columns: {df_clean.columns.tolist()}")
# %%
# %%
# Aggregate to weekly demand per category
df_clean['Week'] = df_clean['Date'].dt.to_period('W').dt.start_time

weekly_demand = (
    df_clean.groupby(['Week', 'Product_Category'])['Order_Demand_clean']
    .sum()
    .reset_index()
    .rename(columns={'Order_Demand_clean': 'Weekly_Demand'})
)

print(weekly_demand.shape)
weekly_demand.head()
# %%
# %%
# Check yearly totals and exact date range before trimming
weekly_demand['Year'] = weekly_demand['Week'].dt.year
print(weekly_demand.groupby('Year')['Weekly_Demand'].agg(['sum', 'count']))
print(f"\nFull date range: {weekly_demand['Week'].min()} to {weekly_demand['Week'].max()}")
# %%
# %%
# Trim to full calendar years only: 2012-2016 (2011 and 2017 are partial-year artifacts)
weekly_demand_trimmed = weekly_demand[
    (weekly_demand['Week'] >= '2012-01-01') & (weekly_demand['Week'] <= '2016-12-31')
].drop(columns='Year').reset_index(drop=True)

print(f"Before: {weekly_demand.shape} → After: {weekly_demand_trimmed.shape}")
print(f"Rows dropped: {weekly_demand.shape[0] - weekly_demand_trimmed.shape[0]}")
print(f"\nNew date range: {weekly_demand_trimmed['Week'].min()} to {weekly_demand_trimmed['Week'].max()}")
# %%
# %%
from pathlib import Path

# Build an absolute path anchored to the project root, same pattern as your raw-data loading
project_root = Path(__file__).resolve().parent.parent
output_path = project_root / 'data' / 'processed' / 'weekly_demand.csv'

weekly_demand_trimmed.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")
# %%
# %%
# Save the full row-level cleaned dataset too, for SQL loading in the next phase
df_clean.to_csv(project_root / 'data' / 'processed' / 'df_clean.csv', index=False)
print(f"Saved df_clean: {df_clean.shape}")
# %%
