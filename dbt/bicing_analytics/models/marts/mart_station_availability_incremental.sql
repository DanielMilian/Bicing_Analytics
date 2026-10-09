{{ config(
    materialized='incremental',
    unique_key=['station_id', 'last_reported']
) }}

SELECT
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

    CASE
        WHEN bike_availability_pct = 0 THEN 'empty'
        WHEN bike_availability_pct < 20 THEN 'low'
        WHEN bike_availability_pct < 80 THEN 'medium'
        ELSE 'high'
    END AS availability_status

FROM {{ ref('int_station_availability') }}

{% if is_incremental() %}

WHERE ingested_at > (
    SELECT MAX(ingested_at) - INTERVAL '5 minutes'
    FROM {{ this }}
)

{% endif %}
