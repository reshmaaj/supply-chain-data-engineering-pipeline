
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

CSV_PATH = "raw_datas/DataCoSupplyChainDataset.csv"

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

PIPELINE_NAME = "logistics_pipeline"


# --------------------------------------------------
# 2. READ AND CLEAN SOURCE DATA
# --------------------------------------------------

def read_and_clean_data():
    print("Reading source CSV...")

    df = pd.read_csv(CSV_PATH, encoding="latin1")

    # Convert dates
    df["order date (DateOrders)"] = pd.to_datetime(
        df["order date (DateOrders)"], errors="raise"
    )
    df["shipping date (DateOrders)"] = pd.to_datetime(
        df["shipping date (DateOrders)"], errors="raise"
    )

    # Remove unnecessary and sensitive columns
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
        "Longitude",
    ])

    # Standardize column names
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
        "Shipping Mode": "shipping_mode",
    })

    # Validate source records
    if df["order_item_id"].isna().any():
        raise ValueError("Source contains missing order_item_id values.")

    df["order_item_id"] = pd.to_numeric(
        df["order_item_id"], errors="raise"
    ).astype("int64")

    if df["order_item_id"].duplicated().any():
        raise ValueError("Source contains duplicate order_item_id values.")

    if (df["order_item_id"] <= 0).any():
        raise ValueError("Source contains invalid order_item_id values.")

    if df["order_date"].isna().any() or df["shipping_date"].isna().any():
        raise ValueError("Source contains invalid dates.")

    print(f"Source rows validated: {len(df)}")

    return df


# --------------------------------------------------
# 3. INCREMENTAL LOAD
# --------------------------------------------------

def run_pipeline():
    start_time = datetime.now()
    rows_processed = 0
    connection = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)
        print("Connected to PostgreSQL!")

        # All data changes, checkpoint updates, and success
        # logging commit together.
        with connection:
            with connection.cursor() as cursor:

                # Read the last successful checkpoint.
                cursor.execute("""
                    SELECT last_loaded_order_item_id
                    FROM pipeline_metadata
                    WHERE pipeline_name = %s
                    FOR UPDATE
                """, (PIPELINE_NAME,))

                metadata = cursor.fetchone()

                if metadata is None:
                    raise ValueError(
                        f"Missing pipeline metadata for {PIPELINE_NAME}"
                    )

                last_loaded_id = metadata[0]
                print(f"Current watermark: {last_loaded_id}")

                # Read and validate the incoming source.
                df = read_and_clean_data()

                # Select only records beyond the watermark.
                new_df = df[
                    df["order_item_id"] > last_loaded_id
                ].copy()

                print(f"New source rows: {len(new_df)}")

                if not new_df.empty:

                    # Convert pandas missing values to SQL NULLs.
                    new_df = new_df.astype(object).where(
                        pd.notna(new_df), None
                    )

                    columns = list(new_df.columns)
                    column_sql = ", ".join(
                        f'"{column}"' for column in columns
                    )

                    # Temporary staging table: automatically dropped
                    # when the transaction commits or rolls back.
                    cursor.execute("""
                        CREATE TEMP TABLE logistics_raw_stage
                        (LIKE logistics_raw INCLUDING DEFAULTS)
                        ON COMMIT DROP
                    """)

                    values = list(
                        new_df.itertuples(index=False, name=None)
                    )

                    stage_query = f"""
                        INSERT INTO logistics_raw_stage
                        ({column_sql})
                        VALUES %s
                    """

                    execute_values(
                        cursor,
                        stage_query,
                        values,
                        page_size=5000,
                    )

                    # Insert new records, protecting against duplicates.
                    insert_query = f"""
                        INSERT INTO logistics_raw ({column_sql})
                        SELECT {column_sql}
                        FROM logistics_raw_stage
                        ON CONFLICT (order_item_id) DO NOTHING
                        RETURNING order_item_id
                    """

                    cursor.execute(insert_query)
                    inserted_ids = cursor.fetchall()
                    rows_processed = len(inserted_ids)

                    # Advance the checkpoint only after the inserts
                    # have succeeded within this transaction.
                    new_watermark = int(
                        new_df["order_item_id"].max()
                    )

                    cursor.execute("""
                        UPDATE pipeline_metadata
                        SET last_loaded_order_item_id = %s,
                            last_run_timestamp = CURRENT_TIMESTAMP
                        WHERE pipeline_name = %s
                    """, (new_watermark, PIPELINE_NAME))

                    print(f"Rows inserted: {rows_processed}")
                    print(f"New watermark: {new_watermark}")

                else:
                    print("No new rows to load.")

                    cursor.execute("""
                        UPDATE pipeline_metadata
                        SET last_run_timestamp = CURRENT_TIMESTAMP
                        WHERE pipeline_name = %s
                    """, (PIPELINE_NAME,))

                # Record successful execution in the same transaction.
                cursor.execute("""
                    INSERT INTO pipeline_log (
                        pipeline_name,
                        start_time,
                        end_time,
                        status,
                        rows_processed,
                        error_message
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    PIPELINE_NAME,
                    start_time,
                    datetime.now(),
                    "SUCCESS",
                    rows_processed,
                    None,
                ))

        print("Pipeline completed successfully.")

    except Exception as error:
        # Undo partial data changes before recording the failure.
        if connection is not None:
            connection.rollback()

            try:
                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO pipeline_log (
                                pipeline_name,
                                start_time,
                                end_time,
                                status,
                                rows_processed,
                                error_message
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            PIPELINE_NAME,
                            start_time,
                            datetime.now(),
                            "FAILED",
                            0,
                            str(error)[:4000],
                        ))
            except Exception as log_error:
                print(f"Could not save failure log: {log_error}")

        print(f"Pipeline failed: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()
            print("Database connection closed.")


# --------------------------------------------------
# 4. ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    run_pipeline()