## Phase 0

GOALS:
1. Download the dataset
2. Confirm what's actually in it
3. Spot anything broken or unusual early (malformed dates, weird outliers, missing fields)

Raw Columns:
- Product_Code – which specific product this row is about
- Warehouse – which of the 4 regional warehouses this demand went through (Whse_J, Whse_S, Whse_C, Whse_A)
- Product_Category – the broader group the product belongs to (e.g. Category_019) – 33 of these in total
- Date – the day this order/demand happened
- Order_Demand – how many units were ordered (was stored as messy text, cleaned it)

Each row = "this product, at this warehouse, on this date, had this much demand."

Size and scope: 1 million rows, 2,160 different products, 33 different categories,
4 warehouses covering Jan 2011 to Jan 2017.

Data sourced from a manufacturing warehouse. Category_019 seems to disproportionately dominate.

## Phase 1

Data cleaning, SQL loading & demand pattern analysis

1. Clean the raw dataset - handle the unparseable dates, decide how to treat the
negative order demand values, address the zero-demand rows. Exclude partial year
dates from any time series/seasonal work

unparseable dates:
its checking whether a raw string can be interpreted as a date at all.
it usually becomes NaT when the value is:
1. Blank/missing (empty string or a literal Nan)
2. Malformed (e.g. 00/00/0000), stray placeholder, mixed date formats pandas can't reconcile
3. Genuinely impossible as a calendar date (day 32, month 13 - rare but possible in messy exports)
(this doesn't include dates outside our expected order timeline - we correct that later)

For some reason the unparseable dates seem to be grouped in continuous blocks.
Likely an export issue rather than random data loss.

For negative rows:
1. Do negative rows cluster?
2. What's the magnitude?
3. Do they trace to specific products?
4. Revisit any suspicious numbers

Checking for duplicates - 113,064 rows that are duplicates, ~10.8% of the entire
dataset. Kept low-repeat duplicates and removed high-repeat duplicates since
multiple orders in a day is common in the dataset.

Looking at positive demand outliers, 1,985 of 2,160 products (92%) have at least
one outlier flagged. This represents real demand behaviour — broad-based across
many categories rather than concentrated in a few — consistent with genuine
demand variability (bulk orders, seasonal spikes) rather than a data quality
issue. Not removed/capped, kept as is_outlier metadata for later phases.

Duplicate threshold: THRESHOLD = 5. Groups repeating 5+ times on
(Product_Code, Warehouse, Product_Category, Date, Order_Demand_clean) treated
as export/logging artifacts and removed; 2-4x repeats kept as plausible genuine
separate orders. Investigated group repeat-count distribution first before
picking this cutoff — a judgement call, not a derived statistic.

Missing values checked across Product_Code, Warehouse, Product_Category,
Order_Demand_clean — none found.

## Phase 2

Python -> SQLAlchemy -> SQLite

SQLite - the database, saved as sql/supplychain.db. Understands how to execute
SQL queries against it.

SQLAlchemy - python library that acts as a translator/connector between your
python script and the database.

Python - where you write the actual code, using SQLAlchemy as the bridge.

Load into SQLite via SQLAlchemy, write at least three non-trivial SQL queries.

Two tables in SQLite: 
1. demand_clean (1M+ rows, daily-level, fully cleaned)
2. weekly_demand (7,082 rows, aggregated)

Calculated a 4-week average as this is roughly a month.

1. Window function - functions that perform calculations across a set of rows
2. A join - combines information across tables (categories/warehouses) within one table
3. An aggregation - grouping and summarising (e.g. total demand by warehouse, or which categories have the most volatile demand)


## Phase 3 - Demand Pattern Analysis

- helps figure out the reorder point (expected demand during lead time)

Analyse demand patterns - seasonal decomposition per category, coefficient of
variation per category

1. CV per category - measures how erratic each category's weekly demand is.
Feeds directly into XYZ segmentation next phase (low CV = 'X'/predictable,
high CV = 'Z'/erratic)

We can see Category_019 has the lowest CV (0.205) despite having the highest
product demand - most stable/predictable of all 33 categories. Strong
candidate for high volume, low safety stock policy later on.

Compare to categories like 017/027/016 - will likely need higher safety
stock relative to their volume, precisely because they're so unpredictable.

2. Seasonal decomposition - checks whether demand shows repeating yearly or
monthly patterns (trend, seasonality, residual noise), using the weekly
demand table.

Split into three components:
1. Trend - long term direction
2. Seasonal - repeating pattern at fixed interval
3. Residual - whatever's left once trend and seasonality removed ("noise")

[image.png] - 4 graphs: weekly demand / trend / seasonal / residual

1. Weekly Demand - noisy, averaging around 1-2.5 x10^7
2. Trend - rises 2012-2015 (peak), declines through 2016
3. Seasonal - consistent repeating wave, so seasonality present
4. Residual - scattered near centreline 0, good sign - trend/seasonal
   captured the structured part of the signal

As Cat_019 has highest demand (10x next category), ran decomposition just for
this category.

[image-1.png] - near identical to aggregate graph - confirms pattern largely
driven by Category_019.

Also checked Category_017 (high CV):

[image-2.png]

Weekly demand - scale is low thousands (0-4000) vs Cat_019's tens of millions.
Spikier/choppier relative to its own scale.

Trend - rises from 2012, peaks 2013-2014 (earlier than Cat_019's 2014-2015),
sharper narrower peak, declines to lower level by 2016 than where it started.

Seasonal - repeating wave present too, but given small scale, some of what's
"seasonal" here may really be volatility (CV 2.59) rather than clean
calendar cycle.

Residual - noticeably larger relative to signal than Cat_019's (spikes up to
~2000 against series peaking ~4000) - proportionally much noisier.

Cat_019 (low CV) decomposes cleanly, Cat_017 (high CV) shows different
trend timing/shape + much larger residual. Solid justification for why flat
uniform policy would poorly serve both extremes at once.

3. Discount/promo effect - not applicable, no discount field. Legitimate
scope gap.

## Phase 4 - ABC/XYZ segmentation

ABC segmentation here uses order volume (units) as the value proxy, since no
price/cost field exists in this dataset. Simplification of standard
value-based ABC analysis (typically revenue = volume × unit price); relative
ranking may differ if true monetary value were available.

From Phase 3 - two separate lenses (volume and predictability/CV). Used for
Phase 4 decision framework.

1. ABC segmentation - classify each category by value/volume (A = few
categories driving most of the business, C = many low-volume ones)

Dataset does not follow a clean 80/15/5 curve - Category_19 alone holds
82.6% of total demand, so standard Pareto heuristic doesn't map cleanly.
Followed a natural breakpoint approach instead.

2. XYZ segmentation - classify each category by CV (X = predictable, Z =
erratic)

Different from ABC (80/15/5 convention). Data far more concentrated so
cutoffs derived from actual cliffs there. XYZ is closer to the opposite - CV
doesn't show a cliff structure, forcing artificial cliffs would mean picking
a boundary in the middle of a smooth, gradual slope.

3. Combine into a 3x3 ABC-XYZ matrix - e.g. "AX" categories (high volume and
high predictability)


## Phase 4 - Safety stock formula

Calculate a data-driven buffer stock level per segment rather than one flat
rule for everything.

Concept: safety stock is a buffer held in addition to average demand, sized
to absorb demand uncertainty during lead time.

LEAD TIME - time between placing the reorder and that replenishment stock
arriving (logistics/supplier characteristic).

Z should vary by segment - e.g. the one AX category (high volume, highly
predictable, and per Query 2, carries real single-warehouse concentration
risk) might reasonably get a higher service level target than a CZ category,
since a stockout there is more costly to the business.

Decided it makes more sense to accept the volatility and low volume
together, as the majority of revenue was from Cat_019, not the low
categories - high safety stock for those would be a waste of money.

SERVICE LEVEL EXPLAINED: not "keep 85% of something in stock" - it's "accept
this category will stock out in roughly 1 of every ~7 lead-time cycles
(15%), because that's a cheap trade-off given how small/unpredictable it is;
but for Category_019, only accept a stockout in roughly 1 of every 50 cycles
(2%), because that one actually matters."

REORDER POINT = expected demand during lead time + safety stock. The
trigger level - once stock drops to this number, place a new order. Covers
both expected sales during the wait AND unexpected spikes above average.

Safety stock only protects against normal, expected demand (captured by std
dev). Doesn't protect from genuine shocks (supplier collapse, huge
unexpected bulk order, black swan). Covered in Phase 5 Monte Carlo.


## Phase 4 - Forecasting

Build a simple forecast and compare it against a naive baseline.

Split dataset timeline into two sections:
1. train (2012-2015, 209 weeks) to build forecast from
2. test (all of 2016, 52 weeks) - unseen data to judge the forecast fairly

naive_forecast - for each week in 2016, predicts the same number as exactly
one year earlier. No modelling, just a placeholder guess to serve as
baseline (predicting 2016 to look like 2015).

MAE (Mean Absolute Error) - doesn't tell you whether you over- or
under-forecasted (strips direction via abs), just magnitude of how far off
you were.

MAE naive_forecast = 3,519,694 (benchmark on how bad a zero-effort guess is)

HOLT-WINTERS (triple exponential smoothing) - explicitly models level,
trend, and seasonal at once. Uses training data to learn how strong each
effect is, then projects all three forward together.

[image.png] - forecast comparison chart

## Phase 5 - Monte Carlo Simulation (Supplier delay/disruption modelling)

Monte Carlo - strategy where questions too complex to solve with a clean
formula instead use a simulation with random inputs, repeated thousands of
times, looking at the spread of outcomes.

e.g. "Given randomness in both demand AND lead time, how often would our
stock run out?"

One Monte Carlo trial = one imagined version of "a single time you had to
reorder stock." Not real - one hypothetical draw from everything that could
happen.

Part 1 (bootstrap) generates the demand piece
Part 2 (disruption) generates the lead-time piece
Part 3 (replication loop) is the "repeat thousands of times" step

Bootstrap sanity-checked against weekly_mean × 5.36 - matched within 0.005%.

## Phase 5 - Disruption model

How we simulate the supplier sometimes taking longer than 5.36 weeks (the
scenario where something goes wrong - a shipment delay, a customs hold, a
factory issue).

No disruption/delay field exists in the dataset, so this uses documented
judgement-call assumptions (same approach as the 37.5-day lead time
assumption):
- 20% probability a given lead-time cycle experiences a disruption
- When disrupted, extra delay drawn from exponential distribution, mean 2
  extra weeks - chosen over uniform because real-world disruptions tend to
  be right-skewed (most short, a few severe)

Not validated against real disruption data - a reasonable modelling choice,
not an evidenced one.


## Phase 5 - Replication loop + policy comparison

Run both pieces thousands of times per category, under both segmented
policy and a flat policy, compare stockout rates vs. holding cost.

Found stockout rate for segmented was higher on basically all categories
except AX, BX - expected since we prioritised the stocks with largest
impact on demand (AX).

1. Total stock held under each policy - holding cost side of the story
2. Volume-weighting - a stockout on Category_019 matters far more than one
on a category that's 3 units total (like Category_027, mean_demand under
100). Calculated by weighted average: (rate_1 × weight_1) + (rate_2 ×
weight_2) + ... + (rate_33 × weight_33)

## Phase 6 - Power BI dashboard build

Built as ONE focused page, not multi-page - per decision that PBI is for
final summary only, deeper analysis stays in README.

category_profile built via Power Query merge of segmentation_with_policy.csv
+ monte_carlo_results.csv. monte_carlo_results staging query has "Enable
Load" unticked (not deleted - category_profile has a live reference to it).

Colours: blue #2A78D6 / orange #EB6834 (slots 1 & 2 of validated categorical
palette, CVD-safe).

Edit Interactions used to disable cross-filtering between charts and KPI
cards (set to "None" against each other) so clicking a bar doesn't distort
card totals.

Page canvas resized (Format page → Canvas settings → Custom, reduced Height)
to remove empty white-space band left by default 16:9 canvas.