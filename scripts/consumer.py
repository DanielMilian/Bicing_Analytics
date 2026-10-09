import json

from kafka import KafkaConsumer

from bicing.db import get_connection, insert_station_status

TOPIC = "bicing_station_status"

def main() -> None:
    consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers="localhost:9092",
            group_id="bicing-consumers",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value: json.loads(value.decode("utf-8"))
            )
    
    conn = get_connection()

    print("Consumer started. Waiting for messages...")
    
    try:
        for message in consumer:
            event = message.value

            insert_station_status(conn, event)
            
            consumer.commit()

            print(
                 f"Partition: {message.partition} | "
                 f"Offset: {message.offset} | "
                 f"Station: {message.value['station_id']} | "
                 f"Bikes: {message.value['num_vehicles_available']}"
                 )

    except KeyboardInterrupt:
        print("\nStopping consumer...")

    finally:
        conn.close()
        consumer.close()
       
if __name__ == "__main__":
    main()

