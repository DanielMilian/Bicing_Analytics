import os
import subprocess
from getpass import getpass
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# Load the existing local .env without printing secrets.
for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))

# Discover the host port mapped to the local PostgreSQL container.
port_output = subprocess.check_output(
    ["docker", "port", "bicing-postgres", "5432/tcp"],
    text=True,
).strip().splitlines()

if not port_output:
    raise SystemExit("No host port found for bicing-postgres.")

local_port = int(port_output[0].rsplit(":", 1)[1])

local_config = {
    "host": "127.0.0.1",
    "port": local_port,
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "connect_timeout": 10,
}

supabase_password = getpass("Enter your Supabase database password (input hidden): ")

cloud_config = {
    "host": "db.faiqvtezxorprnuzlvlz.supabase.co",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": supabase_password,
    "sslmode": "require",
    "connect_timeout": 15,
}

columns = (
    "station_id",
    "num_vehicles_available",
    "num_docks_available",
    "num_vehicles_disabled",
    "num_docks_disabled",
    "last_reported",
    "is_installed",
    "is_renting",
    "is_returning",
    "ingested_at",
)

try:
    with psycopg2.connect(**local_config) as local_conn, \
         psycopg2.connect(**cloud_config) as cloud_conn:

        with local_conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM public.raw_station_status"
            )
            source_count = cur.fetchone()[0]

            cur.execute("""
                SELECT station_id, num_vehicles_available,
                       num_docks_available, num_vehicles_disabled,
                       num_docks_disabled, last_reported, is_installed,
                       is_renting, is_returning, ingested_at
                FROM public.raw_station_status
            """)
            rows = cur.fetchall()

        print(f"Local source rows: {source_count}")

        with cloud_conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM public.raw_station_status"
            )
            existing_count = cur.fetchone()[0]

            if existing_count != 0:
                raise RuntimeError(
                    f"Supabase table already has {existing_count} rows. "
                    "Stopping to avoid duplicate data."
                )

            insert_sql = """
                INSERT INTO public.raw_station_status
                (station_id, num_vehicles_available, num_docks_available,
                 num_vehicles_disabled, num_docks_disabled, last_reported,
                 is_installed, is_renting, is_returning, ingested_at)
                VALUES %s
            """

            execute_values(cur, insert_sql, rows, page_size=500)

            cur.execute(
                "SELECT COUNT(*) FROM public.raw_station_status"
            )
            destination_count = cur.fetchone()[0]

        if destination_count != source_count:
            raise RuntimeError(
                f"Row count mismatch: source={source_count}, "
                f"Supabase={destination_count}"
            )

        print(f"Supabase destination rows: {destination_count}")
        print("SUCCESS: All rows copied and row counts match.")

except Exception as exc:
    print(f"\nTransfer failed: {type(exc).__name__}: {exc}")
    raise SystemExit(1)
