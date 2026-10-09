def build_station_event(station: dict) -> dict:
    return {
        "station_id": station["station_id"],
        "num_vehicles_available": station["num_vehicles_available"],
        "num_docks_available": station["num_docks_available"],
        "num_vehicles_disabled": station["num_vehicles_disabled"],
        "num_docks_disabled": station["num_docks_disabled"],
        "last_reported": station["last_reported"],
        "is_installed": station["is_installed"],
        "is_renting": station["is_renting"],
        "is_returning": station["is_returning"],
    }
