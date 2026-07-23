# supply-chain-forecasting-dashboard

## Phase 0


GOALS:

1. Download the dataset

2. confirm what's actually in it

3. Spot anything broken or unusual early (malformed dates,weird outliers,missing fields) 



Raw Columns:

Product_Code - which specific product this row is about 

Warehouse - which of the 4 regional warehouses this demand went through (Whse_J, Whse_S , Whse_C , Whse_A)

Product_Category - the broader group the product belongs to (e.g. Category_019) - 33 of theses in total

Date - the day this order/demand happened

Order_Demand - how many units were orderd (was stored as messy test but cleaned it)

each row = "this product, at this warehouse, on this date, had this much demand."

Size and scope - 1 million row, 2,160 different products, 33 different catageories and 4 warehouses covering Jan 2011 to Jan 2017



Data sourced from a manufacturing warehouse 

Category_019 seems too disproportionately dominate


## Phase 1

Data cleaning, SQL Loading & Demand Pattern Analysis


1. Clean the raw dataset - handle the unparseable dates, decide how to treat the negative order demand values, address the zero-demand rows. Exclude partial year dates from any time series/seasonal work

unpareseale dates:

- its checking whether a raw string can be interpreted as a date at all.
it usually becomes NaT when the values is:

1. Blank/missing (empty string or a literal Nan)
2. Malformed (e.g. 00/00/0000 ), as stray placeholder, mixed date formats pandas can't reconcile
3. Genuinely impossible as a calendar date (day 32,month 13 rare but possible in messy exports)

(this doesnt include dates outside our expected order timeline we will correct that later on)

for some reason the unparesable dates seem to be grouped in continuous blocks. Likely an export issue rather than random data loss

Seems that all the unparesable dates came from Warehouse A and over 90% of the product category affected was cat019. However the product demand was extremely low of 10,090 units and compared to total demand of 4.22 billion this contributes to 0.00% so we can ignore the blank dates rows. (11,239 blank date rows)

Also order demand values that contained () was the only sign for negative orders essentially product returns


Rows before: 1048575, after: 1037336 (after decision to remove unparseable dates)




For negative rows:

1. Do negative rows cluster?
2. What's the magnitude 
3. Do they trace to specific products?
4. Revisit any suspicious numbers 



we found 10,469 negative rows and of that 4570 rows were inside the balnk date rows that I dropped. This means 41% of the blank date rows were negative demand rows. Therefore there is a correlation between theses in the same subset of records so this was likely from the same export/logging process in Warehouse A rather than two different unreleated issues.



2. Document the high volume SKU pattern - Cate 019 80% demand concentration from three products 

3. Aggregate demand data - roll up cleanned transactions to weekly demand per product category

4. Load into SQLite - via SQLAlchemy and write at least three non trivial SQL queries.

5. Analyse demand patterns - seasonal decompostion per category, cofficient of variation per category