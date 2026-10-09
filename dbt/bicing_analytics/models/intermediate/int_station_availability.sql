SELECT
    station_id,
    last_reported,
    ingested_at,
    num_vehicles_available,
    num_docks_available,
    num_vehicles_disabled,
    num_docks_disabled,

    num_vehicles_available
        + num_docks_available AS total_capacity,

    ROUND(
        100.0 * num_vehicles_available
        / NULLIF(
            num_vehicles_available + num_docks_available,
            0
        ),
        2
    ) AS bike_availability_pct,

    ROUND(
        100.0 * num_docks_available
        / NULLIF(
            num_vehicles_available + num_docks_available,
            0
        ),
        2
    ) AS dock_availability_pct

FROM {{ ref('stg_station_status') }}
