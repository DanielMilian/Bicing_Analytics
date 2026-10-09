{{ config(materialized='table') }}

SELECT
    COUNT(*) AS stations_reporting,
    SUM(num_vehicles_available) AS bikes_available,
    SUM(num_docks_available) AS docks_available,
    COUNT(*) FILTER (
        WHERE availability_status = 'empty'
    ) AS empty_stations,
    COUNT(*) FILTER (
        WHERE availability_status = 'low'
    ) AS low_availability_stations,
    ROUND(
        AVG(bike_availability_pct),
        2
    ) AS avg_station_bike_availability_pct,
    MAX(ingested_at) AS latest_ingestion
FROM {{ ref('mart_station_latest') }}
