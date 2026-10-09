import psycopg

from bicing.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


def get_connection():
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def insert_station_status(conn, event: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_station_status (
                station_id,
                num_vehicles_available,
                num_docks_available,
                num_vehicles_disabled,
                num_docks_disabled,
                last_reported,
                is_installed,
                is_renting,
                is_returning
            )
            VALUES (
                %(station_id)s,
                %(num_vehicles_available)s,
                %(num_docks_available)s,
                %(num_vehicles_disabled)s,
                %(num_docks_disabled)s,
                %(last_reported)s,
                %(is_installed)s,
                %(is_renting)s,
                %(is_returning)s
            )
            ON CONFLICT (station_id, last_reported) DO NOTHING
            """,
            event,
        )

    conn.commit()
