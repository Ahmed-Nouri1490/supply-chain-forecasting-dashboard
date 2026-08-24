# %%
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

project_root = Path(__file__).resolve().parent.parent
db_path = project_root / "sql" / "supply_chain.db"
engine = create_engine(f"sqlite:///{db_path}")

weekly = pd.read_sql("SELECT * FROM weekly_demand", engine)

total_weekly = (
    weekly
    .groupby("Week")["Weekly_Demand"]
    .sum()
)

total_weekly.index = pd.to_datetime(total_weekly.index)
total_weekly = total_weekly.sort_index()
total_weekly = total_weekly.asfreq("W-MON")
total_weekly.tail()
# %%
test_weeks = 52
train = total_weekly[:-test_weeks]
test = total_weekly[-test_weeks:]

print(f"Train: {train.index.min()} to {train.index.max()} ({len(train)} weeks)")
print(f"Test: {test.index.min()} to {test.index.max()} ({len(test)} weeks)")
# %%
# %%
naive_forecast = total_weekly.shift(52)[-test_weeks:]
naive_forecast

# %%
naive_error = (test - naive_forecast).abs()
naive_mae = naive_error.mean()
print(f"Naive baseline MAE: {naive_mae:,.0f}")

### HOLT-Winters Seasonal Model
# %%
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(
    train,
    trend="add",
    seasonal="add",
    seasonal_periods= 52,
)
fitted_model = model.fit()
hw_forecast = fitted_model.forecast(test_weeks)
hw_forecast
hw_error = (test - hw_forecast).abs()
hw_mae = hw_error.mean()
print(f"Holt-Winters MAE: {hw_mae:,.0f}")
print(f"Naive baseline MAE: {naive_mae:,.0f}")
print(f"Improvement: {(1 - hw_mae/naive_mae) * 100:.1f}%")

## GRAPH PLOTTING 
# %%
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))
plt.plot(test.index, test.values, label="Actual", linewidth=2)
plt.plot(test.index, naive_forecast.values, label="Naive baseline", linestyle="--")
plt.plot(test.index, hw_forecast.values, label="Holt-Winters", linestyle="--")
plt.legend()
plt.title("2016 Demand Forecast: Actual vs Naive vs Holt-Winters")
plt.show()


# %%
