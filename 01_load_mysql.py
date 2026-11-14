"""
LANGKAH 1 - Konversi file JSON -> database SQL (MySQL).
MySQL adalah penyimpanan utama (data lengkap, ternormalisasi).

Jalankan:  python 01_load_mysql.py
"""
import datetime as dt
import json
import math
import os

import ijson
import mysql.connector

from config import DATA_DIR, MYSQL

BATCH = 5000

def clean_val(val):
    if isinstance(val, float) and (math.isinf(val) or math.isnan(val)):
        return None
    return val
    
def clean(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def to_int(v):
    v = clean(v)
    return None if v is None else int(v)


def to_float(v):
    v = clean(v)
    return None if v is None else float(v)


def load_json(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def insert_many(cur, sql, rows):
    for i in range(0, len(rows), BATCH):
        cur.executemany(sql, rows[i:i + BATCH])
    print(f"   -> {len(rows):,} baris")


def run_schema():
    cfg = {k: v for k, v in MYSQL.items() if k != "database"}
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    with open("schema.sql", encoding="utf-8") as f:
        for stmt in f.read().split(";"):
            if stmt.strip():
                cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()


def get_country_id(cur, ids, name, who=None):
    if name not in ids:
        cur.execute("INSERT INTO countries (name, who_region) VALUES (%s,%s)", (name, who))
        ids[name] = cur.lastrowid
    return ids[name]


def main():
    print("[0] Membuat database & tabel (schema.sql)")
    run_schema()
    conn = mysql.connector.connect(**MYSQL)
    cur = conn.cursor()

    print("[1] countries + country_latest  (country_wise_latest.json)")
    ids = {}
    rows = load_json("country_wise_latest.json")
    data = []
    for r in rows:
        cid = get_country_id(cur, ids, r["Country/Region"], r.get("WHO Region"))
        data.append((
            cid, to_int(r["Confirmed"]), to_int(r["Deaths"]), to_int(r["Recovered"]),
            to_int(r["Active"]), to_int(r["New cases"]), to_int(r["New deaths"]),
            to_int(r["New recovered"]), to_float(r["Deaths / 100 Cases"]),
            to_float(r["Recovered / 100 Cases"]), to_float(r["Deaths / 100 Recovered"]),
            to_int(r["Confirmed last week"]), to_int(r["1 week change"]),
            to_float(r["1 week % increase"]),
        ))
    insert_many(cur, """INSERT INTO country_latest VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", data)
    conn.commit()

    print("[2] global_daily  (day_wise.json)")
    data = [(
        r["Date"], to_int(r["Confirmed"]), to_int(r["Deaths"]), to_int(r["Recovered"]),
        to_int(r["Active"]), to_int(r["New cases"]), to_int(r["New deaths"]),
        to_int(r["New recovered"]), to_float(r["Deaths / 100 Cases"]),
        to_float(r["Recovered / 100 Cases"]), to_float(r["Deaths / 100 Recovered"]),
        to_int(r["No. of countries"]),
    ) for r in load_json("day_wise.json")]
    insert_many(cur, "INSERT INTO global_daily VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    conn.commit()

    print("[3] country_daily  (full_grouped.json)")
    data = []
    for r in load_json("full_grouped.json"):
        cid = get_country_id(cur, ids, r["Country/Region"], r.get("WHO Region"))
        data.append((
            cid, r["Date"], to_int(r["Confirmed"]), to_int(r["Deaths"]), to_int(r["Recovered"]),
            to_int(r["Active"]), to_int(r["New cases"]), to_int(r["New deaths"]),
            to_int(r["New recovered"]),
        ))
    insert_many(cur, "INSERT INTO country_daily VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    conn.commit()

    print("[4] province_daily  (covid_19_clean_complete.json)")
    data = []
    for r in load_json("covid_19_clean_complete.json"):
        cid = get_country_id(cur, ids, r["Country/Region"], r.get("WHO Region"))
        data.append((
            cid, r.get("Province/State"), to_float(r["Lat"]), to_float(r["Long"]), r["Date"],
            to_int(r["Confirmed"]), to_int(r["Deaths"]), to_int(r["Recovered"]), to_int(r["Active"]),
        ))
    insert_many(cur, """INSERT INTO province_daily
        (country_id, province_state, lat, lon, date, confirmed, deaths, recovered, active)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", data)
    conn.commit()

    print("[5] worldometer  (worldometer_data.json)")
    data = [(
        r["Country/Region"], r.get("Continent"), to_int(r["Population"]), to_int(r["TotalCases"]),
        to_int(r["NewCases"]), to_int(r["TotalDeaths"]), to_int(r["NewDeaths"]),
        to_int(r["TotalRecovered"]), to_int(r["NewRecovered"]), to_int(r["ActiveCases"]),
        to_int(r["Serious,Critical"]), to_float(r["Tot Cases/1M pop"]), to_float(r["Deaths/1M pop"]),
        to_int(r["TotalTests"]), to_float(r["Tests/1M pop"]), r.get("WHO Region"),
    ) for r in load_json("worldometer_data.json")]
    insert_many(cur, "INSERT IGNORE INTO worldometer VALUES (" + ",".join(["%s"] * 16) + ")", data)
    conn.commit()

    print("[6] usa_counties + usa_county_daily  (usa_county_wise.json, ~180 MB, di-stream)")
    counties, daily = {}, []
    path = os.path.join(DATA_DIR, "usa_county_wise.json")
    with open(path, "rb") as f:
        for r in ijson.items(f, "item", use_float=True):
            uid = int(r["UID"])
            if uid not in counties:
                counties[uid] = (
                    uid, r.get("iso2"), r.get("iso3"), to_int(r.get("FIPS")), r.get("Admin2"),
                    r.get("Province_State"), to_float(r.get("Lat")), to_float(r.get("Long_")),
                    r.get("Combined_Key"),
                )
            d = dt.datetime.strptime(r["Date"], "%m/%d/%y").date()
            daily.append((uid, d, to_int(r["Confirmed"]), to_int(r["Deaths"])))
    insert_many(cur, "INSERT INTO usa_counties VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", list(counties.values()))
    insert_many(cur, "INSERT INTO usa_county_daily VALUES (%s,%s,%s,%s)", daily)
    conn.commit()

    cur.close()
    conn.close()
    print("Selesai. Data sudah masuk ke MySQL.")


if __name__ == "__main__":
    main()
