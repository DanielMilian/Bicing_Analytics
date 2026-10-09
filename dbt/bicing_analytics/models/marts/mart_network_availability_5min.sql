{{ config(materialized='table') }}

WITH bucketed AS (
    SELECT
        *,
        date_bin(
            INTERVAL '5 minutes',
            ingested_at,
            TIMESTAMPTZ '2000-01-01 00:00:00+00'
        ) AS time_bucket
    FROM {{ ref('mart_station_availability_incremental') }}
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY station_id, time_bucket
            ORDER BY ingested_at DESC, last_reported DESC
        ) AS row_num
    FROM bucketed
)

SELECT
    time_bucket,
    COUNT(*) AS stations_reporting,
    SUM(num_vehicles_available) AS bikes_available,
    SUM(num_docks_available) AS docks_available,
    ROUND(AVG(bike_availability_pct), 2)
        AS avg_station_bike_availability_pct
FROM ranked
WHERE row_num = 1
GROUP BY time_bucket
