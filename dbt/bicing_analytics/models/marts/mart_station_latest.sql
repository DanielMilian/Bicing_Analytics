{{ config(materialized='table') }}

SELECT DISTINCT ON (station_id)
    station_id,
    last_reported,
    ingested_at,
    num_vehicles_available,
    num_docks_available,
    num_vehicles_disabled,
    num_docks_disabled,
    total_capacity,
    bike_availability_pct,
    dock_availability_pct,
    availability_status
FROM {{ ref('mart_station_availability_incremental') }}
ORDER BY
    station_id,
    last_reported DESC NULLS LAST,
    ingested_at DESC
