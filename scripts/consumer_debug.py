import json

from kafka import KafkaConsumer


TOPIC = "bicing_station_status"


def main() -> None:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers="localhost:9092",
        group_id="bicing-debug-group",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
    )

    print("Debug consumer started.")

    try:
        for message in consumer:
            event = message.value

            print(
                f"Consumer PID: {__import__('os').getpid()} | "
                f"Partition: {message.partition} | "
                f"Offset: {message.offset} | "
                f"Station: {event['station_id']}"
            )

    except KeyboardInterrupt:
        print("\nStopping consumer...")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
