# Barcelona Bicing Analytics 

An end-to-end data engineering project that collects, processes, transforms, and visualizes Barcelona's public bike-sharing availability data.

I built this project to gain hands-on experience with **Apache Kafka and event streaming**, while developing a complete pipeline from API ingestion to analytics and a publicly deployed dashboard.

Live Dashboard: https://barcelona-bicinganalytics.streamlit.app/

GitHub Repository: https://github.com/DanielMilian/Bicing_Analytics

## Architecture

```text
Barcelona Bicing GBFS API
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
   Local PostgreSQL
          |
          v
    dbt Transformations
          |
          v
     Analytics Marts
          |
          v
        Supabase
          |
          v
   Streamlit Dashboard
```

The ingestion pipeline runs in a local Docker-based development environment. The raw observations were migrated to Supabase, where dbt builds the analytical models queried by the deployed Streamlit dashboard.

## Technology Stack

- **Python** — API ingestion, event production and consumption, and database connectivity
- **Apache Kafka** — event streaming and message distribution
- **PostgreSQL** — raw event storage and SQL querying
- **dbt** — data transformations, incremental models, and data quality tests
- **Supabase** — hosted PostgreSQL database for the deployed analytics application
- **Streamlit** — interactive analytics dashboard
- **Pandas and Plotly** — data processing and visualizations
- **Docker Compose** — local infrastructure and development environment
- **Git and GitHub** — version control and project hosting

## Data Pipeline

### 1. Data ingestion

A Python producer polls the Bicing GBFS station-status endpoint at a configurable interval and publishes station-level availability events to Kafka.

Source: [Barcelona Bicing GBFS Station Status API](https://barcelona.publicbikesystem.net/customer/gbfs/v3.0/station_status)

### 2. Event streaming

Apache Kafka distributes the station-status events through the `bicing_station_status` topic, partitioned by station ID.

A Python consumer reads the events and persists observations to PostgreSQL. A unique constraint on `(station_id, last_reported)` prevents duplicate observations, while manual Kafka offset commits provide explicit control over message processing.

### 3. Data transformation with dbt

dbt organizes the raw observations into staging, intermediate, and mart models.

| Model | Purpose |
|---|---|
| `stg_station_status` | Exposes the raw station observations in a consistent staging model |
| `int_station_availability` | Calculates station capacity and bike/dock availability percentages |
| `mart_station_availability` | Provides station-level historical availability metrics and status classifications |
| `mart_station_availability_incremental` | Incrementally processes station observations |
| `mart_station_latest` | Selects the latest observation for each station |
| `mart_network_summary` | Aggregates network-wide availability metrics |
| `mart_network_availability_5min` | Aggregates network availability into five-minute time buckets |

Data quality checks validate required fields and test for negative available-bike counts.

The dbt project successfully builds its models against Supabase, with all configured tests passing.

### 4. Analytics dashboard

The Streamlit dashboard connects to the hosted Supabase PostgreSQL database and queries the analytical marts.

It provides:

- **Network overview:** reporting stations, available bikes, free docks, empty stations, and low-availability stations.
- **Historical trends:** bike availability, dock availability, and station reporting coverage over time.
- **Station explorer:** searchable and filterable station-level availability data, with CSV export.

The dashboard is deployed using Streamlit Community Cloud.

> **Current status:** The dashboard is deployed and connected to Supabase. The ingestion pipeline has been developed and tested locally; continuous cloud-based ingestion is planned as future work.

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Git
- Access to the Bicing GBFS API

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

### 3. Configure the local environment

Create a `.env` file in the project root:

```dotenv
POSTGRES_DB=bicing
POSTGRES_USER=bicing
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Replace the example password with your own local database password. Never commit `.env` or database credentials to Git.

### 4. Start the infrastructure

```bash
docker compose up -d
```

Initialize the local PostgreSQL schema and Kafka topic according to the project configuration before starting ingestion.

### 5. Run the producer and consumer

Run the producer in one terminal:

```bash
PYTHONPATH=src python scripts/producer.py
```

Run the consumer in another terminal:

```bash
PYTHONPATH=src python scripts/consumer.py
```

### 6. Run dbt

Configure the `bicing_analytics` profile in `~/.dbt/profiles.yml` to point to the PostgreSQL database you want to transform.

Then run:

```bash
dbt debug --project-dir dbt/bicing_analytics
dbt build --project-dir dbt/bicing_analytics
```

The hosted deployment uses Supabase connection details configured through environment variables locally and Streamlit Secrets in the cloud.

### 7. Launch the dashboard locally

```bash
streamlit run dashboard/app.py
```

The dashboard will normally be available at `http://localhost:8501`.

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
│   ├── copy_to_supabase.py
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

## Future Improvements

- Deploy the ingestion pipeline for continuous cloud-based data collection.
- Schedule dbt transformations and automate refreshes.
- Add pipeline monitoring, retries, and failure alerts.
- Improve handling of delayed and out-of-order events.
- Add automated tests and continuous integration.
- Expand historical analysis as more observations are collected.

## Author

**Daniel Milian**  
[GitHub](https://github.com/DanielMilian)
