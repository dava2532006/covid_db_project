"""Konfigurasi koneksi. Bisa diubah lewat environment variable."""
import os

DATA_DIR = os.getenv("DATA_DIR", "covid_json")  # folder hasil ekstrak covid_json.zip

MYSQL = dict(
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    database=os.getenv("MYSQL_DB", "covid_db"),
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "covid_db")
