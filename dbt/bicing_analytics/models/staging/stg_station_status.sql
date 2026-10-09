SELECT
    station_id,
    num_vehicles_available,
    num_docks_available,
    num_vehicles_disabled,
    num_docks_disabled,
    last_reported,
    is_installed,
    is_renting,
    is_returning,
    ingested_at
FROM {{ source('bicing', 'raw_station_status')}} 
