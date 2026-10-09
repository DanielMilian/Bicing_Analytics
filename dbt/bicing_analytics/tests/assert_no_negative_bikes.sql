SELECT *
FROM {{ ref('stg_station_status') }}
WHERE num_vehicles_available < 0
