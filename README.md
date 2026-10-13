# Supply Chain Pipeline

An end-to-end data engineering project that processes supply-chain and logistics data using Python, PostgreSQL, and Power BI.

## Architecture

```mermaid
flowchart LR
  A[DataCo Supply Chain CSV] --> B[Python Data Pipeline]
    B --> C[PostgreSQL Raw Table]
    C --> D[Star Schema]
    D --> E[Fact Order Items]
    D --> F[Dimension Tables]
    E --> G[Power BI Dashboard]
    F --> G
    B --> H[Pipeline Metadata]
    B --> I[Pipeline Log]
```

## What I Built

- Python pipeline for CSV ingestion and data validation
- Incremental loading using a watermark
- PostgreSQL raw and analytical layers
- Star schema with fact and dimension tables
- Pipeline logging and duplicate protection
- SQL data-quality and KPI validation
- Power BI dashboard for sales, profitability, shipping performance, and delivery risk
- Environment variables for secure database credentials

<!-- ## Data Model

**Fact:** `fact_order_items`

**Dimensions:** `dim_customer`, `dim_product`, `dim_date`, `dim_location` -->

## Dashboard

![Supply Chain Analytics Dashboard](screenshots/dashboard.png)

## Tech Stack

`Python` • `Pandas` • `PostgreSQL` • `SQL` • `Power BI` • `Git`

## Dataset

DataCo Smart Supply Chain dataset - 180,519 order-item records.

## Project Structure

```text
src/          Python pipeline
sql/          Warehouse schema and validation queries
screenshots/  Power BI dashboard
```
