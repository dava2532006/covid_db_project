# Konversi Data COVID-19 ke MySQL dan MongoDB + Dashboard

Alur: **JSON -> MySQL (data utama) -> MongoDB (data siap tampil) -> Dashboard**

MySQL menyimpan data lengkap dan ternormalisasi. MongoDB menyimpan hasil agregasi
(per negara, per wilayah WHO, per negara bagian AS) sehingga dashboard tidak perlu
menjalankan JOIN/GROUP BY berat di MySQL.

## Persiapan
1. Ekstrak `covid_json.zip` sehingga ada folder `covid_json/` di dalam folder proyek ini.
2. Jalankan MySQL dan MongoDB. Pilihan cepat dengan Docker: `docker compose up -d`
   (MySQL: user `root`, password `root`). Kalau pakai instalasi sendiri, ubah `config.py`
   atau set environment variable (`MYSQL_PASSWORD`, `MONGO_URI`, dst).
3. `pip install -r requirements.txt`

## Menjalankan
```
python 01_load_mysql.py     # JSON -> MySQL (file usa_county_wise.json besar, butuh beberapa menit)
python 02_sync_mongo.py     # MySQL -> MongoDB
python app.py               # dashboard di http://localhost:5000
```

## Struktur tabel MySQL
| Tabel | Sumber JSON |
|---|---|
| countries, country_latest | country_wise_latest.json |
| global_daily | day_wise.json |
| country_daily | full_grouped.json |
| province_daily | covid_19_clean_complete.json |
| worldometer | worldometer_data.json |
| usa_counties, usa_county_daily | usa_county_wise.json |

## Koleksi MongoDB
`global_daily`, `country_summary`, `country_timeseries` (deret waktu tertanam per negara),
`who_region_summary`, `usa_state_summary`.

## Dashboard
Tombol di kanan atas mengganti sumber data antara MongoDB dan MySQL. Setiap grafik
menampilkan waktu respons (ms), jadi perbandingan kedua pendekatan bisa langsung
ditunjukkan ke dosen.
