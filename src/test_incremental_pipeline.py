
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "database": "logistics_db",
    "user": "postgres",
    "password": "resh@postgresql1510",
}

PIPELINE_NAME = "logistics_incremental_test"
START_ID = 180519
NEW_ID = 180520


def run_test():
    connection = None
    start_time = datetime.now()
    rows_processed = 0

    try:
        connection = psycopg2.connect(**DB_CONFIG)

        with connection:
            with connection.cursor() as cursor:
                # Create an isolated watermark for this test.
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS incremental_test_metadata (
                        pipeline_name VARCHAR(100) PRIMARY KEY,
                        last_loaded_id INTEGER NOT NULL,
                        last_run_timestamp TIMESTAMP
                    )
                """)

                cursor.execute("""
                    INSERT INTO incremental_test_metadata
                        (pipeline_name, last_loaded_id)
                    VALUES (%s, %s)
                    ON CONFLICT (pipeline_name) DO NOTHING
                """, (PIPELINE_NAME, START_ID))

                cursor.execute("""
                    SELECT last_loaded_id
                    FROM incremental_test_metadata
                    WHERE pipeline_name = %s
                    FOR UPDATE
                """, (PIPELINE_NAME,))
                last_id = cursor.fetchone()[0]

                # Simulate an incoming batch with one new record.
                # Copy an existing row but give it a new test ID.
                cursor.execute("""
                    INSERT INTO logistics_incremental_batch_test
                    SELECT
                        (jsonb_populate_record(
                            NULL::logistics_raw,
                            to_jsonb(source_row)
                            || jsonb_build_object('order_item_id', %s)
                        )).*
                    FROM logistics_raw AS source_row
                    WHERE source_row.order_item_id = %s
                      AND %s > %s
                    ON CONFLICT (order_item_id) DO NOTHING
                    RETURNING order_item_id
                """, (NEW_ID, START_ID, NEW_ID, last_id))

                inserted = cursor.fetchall()
                rows_processed = len(inserted)

                # Update the watermark only if a row was inserted.
                if inserted:
                    last_id = max(row[0] for row in inserted)

                cursor.execute("""
                    UPDATE incremental_test_metadata
                    SET last_loaded_id = %s,
                        last_run_timestamp = CURRENT_TIMESTAMP
                    WHERE pipeline_name = %s
                """, (last_id, PIPELINE_NAME))

                print("Rows inserted this run:", rows_processed)
                print("Watermark:", last_id)

        print("Test completed successfully.")

    except Exception as error:
        if connection is not None:
            connection.rollback()
        print("Test failed:", error)
        raise

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    run_test()