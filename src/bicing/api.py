import requests

from bicing.config import STATION_STATUS_URL 

def get_station_status() -> dict:
    response = requests.get(
            STATION_STATUS_URL,
            timeout=10,
            )

    response.raise_for_status()

    return response.json()
