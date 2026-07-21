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
