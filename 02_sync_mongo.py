"""
LANGKAH 2 - Salin data dari MySQL -> MongoDB (NoSQL) dalam bentuk siap tampil.

Idenya: MySQL menyimpan data lengkap, sedangkan MongoDB menyimpan hasil
agregasi/denormalisasi (tanpa JOIN, tanpa GROUP BY berat) khusus untuk
dibaca dashboard. Jadi MySQL tidak terbebani oleh query tampilan.

Jalankan:  python 02_sync_mongo.py   (setelah 01_load_mysql.py)
"""
from collections import defaultdict

import mysql.connector
import pymongo

from config import MONGO_DB, MONGO_URI, MYSQL

DATE = "DATE_FORMAT(d.date, '%Y-%m-%d')"


def main():
    conn = mysql.connector.connect(**MYSQL)
    cur = conn.cursor(dictionary=True)
    db = pymongo.MongoClient(MONGO_URI)[MONGO_DB]

    def q(sql):
        cur.execute(sql)
        return cur.fetchall()

    def replace(name, docs):
        db[name].drop()
        if docs:
            db[name].insert_many(docs)
        print(f"   {name}: {len(docs):,} dokumen")

    print("[1] global_daily")
    replace("global_daily", q("""
        SELECT DATE_FORMAT(date,'%Y-%m-%d') AS date, confirmed, deaths, recovered, active,
               new_cases, new_deaths, new_recovered, num_countries
        FROM global_daily d ORDER BY date"""))
    db.global_daily.create_index("date", unique=True)

    print("[2] country_summary (kondisi terbaru per negara, sudah di-JOIN)")
    replace("country_summary", q("""
        SELECT c.name AS country, c.who_region, l.confirmed, l.deaths, l.recovered, l.active,
               l.new_cases, l.new_deaths, l.deaths_per_100_cases, l.week_pct_increase,
               w.population
        FROM countries c
        JOIN country_latest l ON l.country_id = c.country_id
        LEFT JOIN worldometer w ON w.country_name = c.name"""))
    db.country_summary.create_index("country", unique=True)
    for m in ("confirmed", "deaths", "recovered", "active"):
        db.country_summary.create_index([(m, -1)])

    print("[3] country_timeseries (1 dokumen per negara, deret waktu tertanam)")
    series = defaultdict(list)
    for r in q(f"""
        SELECT c.name AS country, {DATE} AS date, d.confirmed, d.deaths, d.recovered,
               d.active, d.new_cases, d.new_deaths
        FROM country_daily d JOIN countries c ON c.country_id = d.country_id
        ORDER BY c.name, d.date"""):
        country = r.pop("country")
        series[country].append(r)
    replace("country_timeseries", [{"country": k, "series": v} for k, v in series.items()])
    db.country_timeseries.create_index("country", unique=True)

    print("[4] who_region_summary")
    replace("who_region_summary", q("""
        SELECT c.who_region, COUNT(*) AS countries,
               CAST(SUM(l.confirmed) AS SIGNED) AS confirmed,
               CAST(SUM(l.deaths) AS SIGNED) AS deaths,
               CAST(SUM(l.recovered) AS SIGNED) AS recovered,
               CAST(SUM(l.active) AS SIGNED) AS active
        FROM countries c JOIN country_latest l ON l.country_id = c.country_id
        GROUP BY c.who_region"""))

    print("[5] usa_state_summary (agregasi 600rb+ baris county -> per negara bagian)")
    replace("usa_state_summary", q("""
        SELECT c.province_state AS state,
               CAST(SUM(d.confirmed) AS SIGNED) AS confirmed,
               CAST(SUM(d.deaths) AS SIGNED) AS deaths
        FROM usa_county_daily d JOIN usa_counties c ON c.uid = d.uid
        WHERE d.date = (SELECT MAX(date) FROM usa_county_daily)
        GROUP BY c.province_state"""))
    db.usa_state_summary.create_index("state", unique=True)

    cur.close()
    conn.close()
    print("Selesai. MongoDB siap dipakai dashboard.")


if __name__ == "__main__":
    main()
