import os

from dotenv import load_dotenv

load_dotenv()

STATION_STATUS_URL = (
        "https://barcelona.publicbikesystem.net/"
        "customer/gbfs/v3.0/station_status"
        )

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

