import json
import time

from kafka import KafkaProducer

from bicing.api import get_station_status
from bicing.events import build_station_event

TOPIC = "bicing_station_status"
POLL_INTERVAL_SECONDS = 60

def main() -> None:
    print("Connecting to Kafka")
    data = get_station_status()
    stations = data["data"]["stations"]

    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )
    
    print("Connected to Kafka")

    try:
        while True:
            print("Fetching Bicing data...")

            data = get_station_status()
            stations = data["data"]["stations"]
            
            print(f"Got {len(stations)} stations. Sending...")

            for station in stations:
                event = build_station_event(station)

                producer.send(
                    TOPIC,
                    key=event["station_id"],
                    value=event,
                )

            producer.flush()
        
            print(f"Sent {len(stations)} station events.")
            print(f"Waiting {POLL_INTERVAL_SECONDS} seconds...")
            time.sleep(POLL_INTERVAL_SECONDS)
        
    except KeyboardInterrupt:
        print("\nStopping producer...")

    finally:
        producer.close()

if __name__ == "__main__":
    main()
