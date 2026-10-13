import pandas as pd

file_path = "raw_datas/DataCoSupplyChainDataset.csv"
df = pd.read_csv(file_path, encoding="latin1")

print("Shape:")
print(df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Rows:")
print(df.duplicated().sum())

print("\nFirst 5 rows:")
print(df.head())

print("\nShipping Modes:")
print(df["Shipping Mode"].unique())

print("\nDelivery Status:")
print(df["Delivery Status"].unique())

print("\nOrder Status:")
print(df["Order Status"].unique())

print("\nMarkets:")
print(df["Market"].unique())

print("\nCustomer Segments:")
print(df["Customer Segment"].unique())

print("\nUnique Order IDs:")
print(df["Order Id"].nunique())

print("\nUnique Order Item IDs:")
print(df["Order Item Id"].nunique())

print("\nOrders with multiple items:")
print(df.groupby("Order Id").size().sort_values(ascending=False).head(10))

print("\nSample Order Dates:")
print(df["order date (DateOrders)"].head())

print("\nSample Shipping Dates:")
print(df["shipping date (DateOrders)"].head())

print("\nShipping Duration Comparison:")

sample = df[
    ["order date (DateOrders)",
     "shipping date (DateOrders)",
     "Days for shipping (real)"]
].head(10)

print(sample)

# coverting the data type od date from str to datetime

df["order date (DateOrders)"] = pd.to_datetime(df["order date (DateOrders)"])
df["shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"])

print("\n Date Data types:")
print(df[
    ["order date (DateOrders)", "shipping date (DateOrders)"]
].dtypes)

df["calculated_shipping_days"] = (
    df["shipping date (DateOrders)"]
    - df["order date (DateOrders)"]
).dt.days    # extracts the no of days from that time difference (TimeDelta.days - gives complete no of 24 hour periods)

df["calculated_shipping_days"] = (
    df["shipping date (DateOrders)"].dt.date 
    - df["order date (DateOrders)"].dt.date 
).apply(lambda x: x.days) 

print("\nShipping Days Comparison:")
print(
    df[
        ["Days for shipping (real)", "calculated_shipping_days"]
    ].head(10)
)

mismatches = df[
    df["Days for shipping (real)"] != df["calculated_shipping_days"]
]

print("\nNumber of shipping-day mismatches:")
print(len(mismatches))

print("\nSample mismatches:")
print(
    mismatches[
        [
            "order date (DateOrders)",
            "shipping date (DateOrders)",
            "Days for shipping (real)",
            "calculated_shipping_days"
        ]
    ].head(10)
)

print("\nColumn decisions:")
for col in df.columns:
    print(col)

# Drop unnecessary columns
df = df.drop(columns=[
    "Customer Email",
    "Customer Fname",
    "Customer Lname",
    "Customer Password",
    "Customer Street",
    "Order Zipcode",
    "Product Description",
    "Product Image",
    "Latitude",
    "Longitude"
])
# Now that we've validated the source data, we don't need to store this duplicate validation column in our production dataset
df = df.drop(columns=["calculated_shipping_days"])

print("\nNumber of columns after dropping:")
print(len(df.columns))

print("\nRemaining columns:")
print(df.columns.tolist())

# Rename columns
df = df.rename(columns={
    "Type": "order_type",
    "Days for shipping (real)": "actual_shipping_days",
    "Days for shipment (scheduled)": "scheduled_shipping_days",
    "Benefit per order": "benefit_per_order",
    "Sales per customer": "sales_per_customer",
    "Delivery Status": "delivery_status",
    "Late_delivery_risk": "late_delivery_risk",
    "Category Id": "category_id",
    "Category Name": "category_name",
    "Customer City": "customer_city",
    "Customer Country": "customer_country",
    "Customer Id": "customer_id",
    "Customer Segment": "customer_segment",
    "Customer State": "customer_state",
    "Customer Zipcode": "customer_zipcode",
    "Department Id": "department_id",
    "Department Name": "department_name",
    "Market": "market",
    "Order City": "order_city",
    "Order Country": "order_country",
    "Order Customer Id": "order_customer_id",
    "order date (DateOrders)": "order_date",
    "Order Id": "order_id",
    "Order Item Cardprod Id": "order_item_product_id",
    "Order Item Discount": "order_item_discount",
    "Order Item Discount Rate": "order_item_discount_rate",
    "Order Item Id": "order_item_id",
    "Order Item Product Price": "order_item_product_price",
    "Order Item Profit Ratio": "order_item_profit_ratio",
    "Order Item Quantity": "order_item_quantity",
    "Sales": "sales",
    "Order Item Total": "order_item_total",
    "Order Profit Per Order": "order_profit_per_order",
    "Order Region": "order_region",
    "Order State": "order_state",
    "Order Status": "order_status",
    "Product Card Id": "product_id",
    "Product Category Id": "product_category_id",
    "Product Name": "product_name",
    "Product Price": "product_price",
    "Product Status": "product_status",
    "shipping date (DateOrders)": "shipping_date",
    "Shipping Mode": "shipping_mode"
})

print("\nCleaned column names:")
print(df.columns.tolist())


print("\nData types after cleaning:")
print(df.dtypes)

print("\n--- DATA QUALITY CHECKS ---")

# 1. Duplicate order item IDs
print("\nDuplicate order_item_id:")
print(df["order_item_id"].duplicated().sum())

# 2. Missing values
print("\nMissing values:")
print(df.isnull().sum()[df.isnull().sum() > 0])

# 3. Negative quantities
print("\nNegative quantities:")
print((df["order_item_quantity"] < 0).sum())

# 4. Negative shipping days
print("\nNegative actual shipping days:")
print((df["actual_shipping_days"] < 0).sum())

# 5. Date consistency
print("\nShipping date before order date:")
print(
    (df["shipping_date"] < df["order_date"]).sum()
)