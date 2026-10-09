from pprint import pprint

from bicing.api import get_station_status
from bicing.events import build_station_event


def main() -> None:
    data = get_station_status()
 
    stations = data["data"]["stations"]
    
    event = build_station_event(stations[0])

    print(event)

if __name__ == "__main__":
    main()
