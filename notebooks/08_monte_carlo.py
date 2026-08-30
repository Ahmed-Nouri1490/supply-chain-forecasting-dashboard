
#%%
import numpy as np
# %%
segmentation = pd.read_csv(
    project_root / "data" / "processed" / "segmentation_with_policy.csv",
    index_col="Product_Category"
)
segmentation.head()

def simulate_lead_time_demand(weekly_demand_values, lead_time_weeks, n_simulations=10000):
    """
    Bootstrap-simulate demand during the lead time for one category.
    
    weekly_demand_values: array of that category's historical weekly demand
    lead_time_weeks: e.g. 5.36
    n_simulations: number of Monte Carlo trials
    """
    whole_weeks = int(lead_time_weeks)          # e.g. 5
    fractional_week = lead_time_weeks - whole_weeks  # e.g. 0.36

    # --- BLANK 1 ---
    # Draw a (n_simulations, whole_weeks) matrix of random samples from
    # weekly_demand_values, WITH replacement, then sum each row (axis=1)
    # to get one total per trial.
    # Hint: np.random.choice(values, size=(rows, cols), replace=True)
    whole_week_sums = np.random.choice(
    weekly_demand_values,
    size=(n_simulations, whole_weeks),
    replace=True
).sum(axis=1)

    # --- BLANK 2 ---
    # Draw ONE more sample per trial (shape = n_simulations), multiply
    # each by fractional_week, to represent the partial week's contribution.
    partial_week_contribution = np.random.choice(weekly_demand_values, size=n_simulations, replace=True) * fractional_week

    # Combine into final lead-time-demand totals
    lead_time_demand_samples = whole_week_sums + partial_week_contribution

    return lead_time_demand_samples

# %%
import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
df_weekly = pd.read_csv(project_root / 'data' / 'processed' / 'weekly_demand.csv')

df_weekly.head()


# %%
## SANITY CHECK: simulate lead-time demand for one category
test_values = df_weekly[df_weekly['Product_Category'] == 'Category_019']['Weekly_Demand'].values

samples = simulate_lead_time_demand(test_values, lead_time_weeks=5.36, n_simulations=10000)

print(f"Mean simulated lead-time demand: {samples.mean():,.0f}")
print(f"Category weekly mean × 5.36:     {test_values.mean() * 5.36:,.0f}")
# %%
 # %%
def simulate_disruption(n_simulations=10000, disruption_prob=0.2, mean_extra_delay=2):
    """
    Simulate whether a disruption occurs and, if so, the extra delay in weeks.

    n_simulations: number of Monte Carlo trials (should match Part 1)
    disruption_prob: probability a given cycle is disrupted
    mean_extra_delay: mean extra weeks of delay, if disrupted (exponential distribution)
    """

    # --- BLANK 1 ---
    # For each trial, decide True/False whether a disruption occurs.
    # Hint: np.random.random(n_simulations) < disruption_prob
    disruption_occurs = np.random.random(n_simulations) < disruption_prob
    # --- BLANK 2 ---
    # Draw an extra-delay value per trial from an exponential distribution
    # Hint: np.random.exponential(scale=mean_extra_delay, size=n_simulations)
    extra_delay_if_disrupted = np.random.exponential(scale=mean_extra_delay, size=n_simulations)

    # Combine: use the exponential draw where disrupted, else 0
    extra_delay_weeks = np.where(disruption_occurs, extra_delay_if_disrupted, 0)

    return extra_delay_weeks


# %%
disruption_test = simulate_disruption(n_simulations=10000, disruption_prob=0.2, mean_extra_delay=2)

pct_disrupted = (disruption_test > 0).mean() * 100
avg_delay_when_disrupted = disruption_test[disruption_test > 0].mean()

print(f"% of trials disrupted: {pct_disrupted:.1f}%  (expect ~20%)")
print(f"Avg delay when disrupted: {avg_delay_when_disrupted:.2f} weeks  (expect ~2.0)")
# %%

## REPLICATION LOOP

# %%
def run_monte_carlo_for_category(weekly_demand_values, base_lead_time_weeks,
                                   reorder_point, flat_reorder_point,
                                   n_simulations=10000, disruption_prob=0.2, mean_extra_delay=2):
    """
    Run the combined Monte Carlo simulation for one category.
    Returns the stockout rate under the segmented policy and the flat policy.
    """
    extra_delays = simulate_disruption(n_simulations, disruption_prob, mean_extra_delay)

    demand_samples = np.zeros(n_simulations)  # empty array to fill in, one value per trial

    for i in range(n_simulations):
        # --- BLANK 1 ---
        # This trial's actual lead time = base lead time + this trial's extra delay
        actual_lead_time = base_lead_time_weeks + extra_delays[i]

        # --- BLANK 2 ---
        # Call simulate_lead_time_demand for JUST this trial (n_simulations=1),
        # using actual_lead_time. The function returns an array of 1 value —
        # use [0] to pull that single number out.
        demand_samples[i] = simulate_lead_time_demand(weekly_demand_values, actual_lead_time, n_simulations=1)[0]

    # Compare simulated demand against each policy's reorder point
    stockout_rate_segmented = (demand_samples > reorder_point).mean()
    stockout_rate_flat = (demand_samples > flat_reorder_point).mean()

    return stockout_rate_segmented, stockout_rate_flat


# %%
test_row = segmentation.loc["Category_019"]

stockout_seg, stockout_flat = run_monte_carlo_for_category(
    weekly_demand_values=test_values,  # from your earlier sanity check, Category_019's weekly demand
    base_lead_time_weeks=5.36,
    reorder_point=test_row["reorder_point"],
    flat_reorder_point=test_row["flat_reorder_point"],
)

print(f"Segmented policy stockout rate: {stockout_seg:.2%}")
print(f"Flat policy stockout rate: {stockout_flat:.2%}")


# %%
