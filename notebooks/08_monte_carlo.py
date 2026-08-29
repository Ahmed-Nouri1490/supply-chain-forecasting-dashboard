
#%%
import numpy as np

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
