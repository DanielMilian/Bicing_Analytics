
# Barcelona Bicing Analytics

An end-to-end data engineering pipeline for collecting, processing, and analyzing Barcelona's public bike-sharing availability data.

## Architecture

```text
Bicing GBFS API
      |
      v
Python Producer
      |
      v
Apache Kafka
      |
      v
Python Consumer
      |
      v
PostgreSQL
      |
      v
dbt Transformations
      |
      v
Analytics Marts
      |
      v
Streamlit Dashboard
```

## Technology Stack

- **Python** — API ingestion and Kafka producer/consumer
- **Apache Kafka** — event streaming with three topic partitions
- **PostgreSQL** — raw event storage and analytical queries
- **dbt** — SQL transformations, incremental models, and data quality tests
- **Streamlit** — interactive dashboard
- **Plotly and Pandas** — visualization and data processing
- **Docker Compose** — local infrastructure

## Data Pipeline

### Ingestion

The producer polls the Bicing GBFS station-status endpoint every 60 seconds and publishes station-level events to Kafka.

Source: [Bicing Station Status API](https://barcelona.publicbikesystem.net/customer/gbfs/v3.0/station_status)

### Streaming and storage

Kafka distributes station events through the `bicing_station_status` topic, partitioned by station ID.

The Python consumer persists observations to PostgreSQL. A unique constraint on `(station_id, last_reported)` prevents duplicate observations, while manual Kafka offset commits provide explicit control over message processing.

### Transformation

dbt transforms raw observations into staging, intermediate, and mart models.

| Model | Description |
|---|---|
| `stg_station_status` | Standardizes raw station observations |
| `int_station_availability` | Calculates station capacity and bike/dock availability percentages |
| `mart_station_availability` | Historical station-level availability and status classification |
| `mart_station_availability_incremental` | Incremental processing of station observations |
| `mart_station_latest` | Latest observation for each station |
| `mart_network_summary` | Network-level availability metrics |
| `mart_network_availability_5min` | Network metrics aggregated into five-minute buckets |

Data quality checks include required-field validation and a custom test for negative available-bike counts.

## Dashboard

The Streamlit dashboard queries PostgreSQL analytics marts and provides:

- **Network overview:** reporting stations, available bikes, free docks, empty stations, and low-availability stations.
- **Historical trends:** bike availability, dock availability, and station reporting coverage over time.
- **Station explorer:** searchable and filterable station-level data with CSV export.

Dashboard screenshots can be added here.

## Getting Started

### Prerequisites

Python 3.10+, Docker Compose, and Git.

### 1. Clone the repository

```bash
git clone git@github.com:DanielMilian/Bicing_Analytics.git
cd Bicing_Analytics
```

### 2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure PostgreSQL

Create a root `.env` file containing the local PostgreSQL connection settings:

```env
POSTGRES_DB=bicing
POSTGRES_USER=bicing
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 4. Start infrastructure

```bash
docker compose up -d
```

Create the Kafka topic and initialize the `raw_station_status` table according to the project schema before starting ingestion.

### 5. Start the producer and consumer

Run the producer in one terminal:

```bash
PYTHONPATH=src python3 scripts/producer.py
```

Run the consumer in another terminal:

```bash
PYTHONPATH=src python3 scripts/consumer.py
```

### 6. Run dbt

Configure the `bicing_analytics` profile in `~/.dbt/profiles.yml` to connect to the local PostgreSQL database.

```bash
cd dbt/bicing_analytics
dbt debug
dbt run
dbt test
```

### 7. Launch the dashboard

From the repository root:

```bash
python3 -m streamlit run dashboard/app.py
```

Streamlit serves the dashboard locally at `http://localhost:8501` by default.

## Repository Structure

```text
Bicing_Analytics/
├── dashboard/
│   └── app.py
├── dbt/
│   └── bicing_analytics/
│       ├── models/
│       │   ├── staging/
│       │   ├── intermediate/
│       │   └── marts/
│       └── tests/
├── scripts/
│   ├── producer.py
│   ├── consumer.py
│   ├── consumer_debug.py
│   └── explore_api.py
├── src/
│   └── bicing/
│       ├── api.py
│       ├── config.py
│       ├── db.py
│       └── events.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Future Work

- Deploy the ingestion pipeline and dashboard to cloud infrastructure.
- Schedule dbt transformations.
- Add pipeline monitoring, retries, and failure alerts.
- Improve handling of delayed and out-of-order events.
- Add automated tests and continuous integration.

## Author

[Daniel Milian](https://github.com/DanielMilian)
