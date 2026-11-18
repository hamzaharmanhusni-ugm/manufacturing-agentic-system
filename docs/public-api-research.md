# Riset API Publik untuk Prototipe Agentic Supply Chain Semen

Tanggal pengujian: 18 November 2026. Semua endpoint tanpa kunci dipanggil langsung dengan `curl` dari mesin pengembang. Contoh respons di bawah adalah potongan respons asli hari itu.

Lingkup sistem: satu pelabuhan muat (Tuban, -6.9, 112.05) mengirim semen curah ke 9 packing plant (Ciwandan, Tanjung Priok, Banjarmasin, Makassar, Balikpapan, Celukan Bawang, Kupang, Bitung, Sorong) dengan 19 kapal.

## Ringkasan

| No | API | Data | Autentikasi | Status | Agent tujuan |
|---|---|---|---|---|---|
| 1 | Open-Meteo Marine API | Tinggi gelombang, gelombang angin, swell, arus laut | Tanpa kunci | Verified | Dispatch Planner (kriteria cuaca), Fleet Tracking |
| 2 | Open-Meteo Forecast API | Curah hujan, kecepatan dan hembusan angin | Tanpa kunci | Verified | ML Forecasting, Dispatch Planner |
| 3 | Open-Meteo Historical (Archive) API | Curah hujan harian historis | Tanpa kunci | Verified | ML Forecasting (data latih) |
| 4 | BMKG Prakiraan Cuaca (api.bmkg.go.id) | Prakiraan cuaca 3 jam per desa/kelurahan | Tanpa kunci | Verified | ML Forecasting, Dispatch Planner |
| 5 | BMKG Peta Maritim | Prakiraan gelombang per wilayah perairan | Tanpa kunci | Not verified | Dispatch Planner |
| 6 | Nager.Date | Hari libur nasional | Tanpa kunci | Verified (data tidak lengkap) | ML Forecasting |
| 7 | Pustaka Python `holidays` | Hari libur nasional termasuk hari raya keagamaan | Tanpa kunci (offline) | Verified | ML Forecasting |
| 8 | Frankfurter | Kurs USD/IDR harian (sumber ECB) | Tanpa kunci | Verified | Stock Monitoring (opsional) |
| 9 | ExchangeRate-API Open Access | Kurs harian 160+ mata uang | Tanpa kunci | Verified | Stock Monitoring (opsional) |
| 10 | World Bank Indicators API dan Pink Sheet | Kurs resmi tahunan, harga komoditas bulanan (minyak, batu bara) | Tanpa kunci | Verified | ML Forecasting, Stock Monitoring (opsional) |
| 11 | OpenStreetMap Nominatim | Koordinat dan poligon area pelabuhan | Tanpa kunci (wajib User-Agent) | Verified | Fleet Tracking (geofence) |
| 12 | OpenStreetMap Overpass API | Kueri fitur OSM (dermaga, area pelabuhan) | Tanpa kunci | Verified (endpoint), kueri perlu disesuaikan | Fleet Tracking (geofence) |
| 13 | searoute (pustaka Python) | Jarak dan lintasan laut antarpelabuhan | Tanpa kunci (offline) | Verified | Dispatch Planner, Fleet Tracking (ETA) |
| 14 | aisstream.io | Posisi AIS kapal real-time (WebSocket) | Kunci gratis | Not verified | Fleet Tracking |
| 15 | Global Fishing Watch API | Identitas kapal dan aktivitas AIS historis | Token gratis (nonkomersial) | Not verified | Fleet Tracking (pelengkap) |

## 1. Open-Meteo Marine API

- Base URL: `https://marine-api.open-meteo.com/v1/marine`
- Autentikasi: tidak diperlukan.
- Batas pemakaian gratis: 10.000 panggilan/hari, 5.000/jam, 600/menit, khusus penggunaan nonkomersial. Proyek akademik termasuk kategori ini.
- Lisensi: data CC BY 4.0, wajib mencantumkan atribusi "Weather data by Open-Meteo.com".
- Agent tujuan: Dispatch Planner (kriteria cuaca keberangkatan), Fleet Tracking (risiko di rute).

Parameter `temporal_resolution=hourly_6` langsung menghasilkan data per 6 jam, sesuai kebutuhan proposal. Beberapa titik rute dapat diminta sekaligus dengan memisahkan koordinat menggunakan koma.

Contoh permintaan (titik Laut Jawa di utara Tuban):

```
curl "https://marine-api.open-meteo.com/v1/marine?latitude=-6.5&longitude=112.5&hourly=wave_height,wind_wave_height,swell_wave_height,ocean_current_velocity&forecast_days=1&temporal_resolution=hourly_6&timezone=Asia%2FJakarta"
```

Contoh respons (dipangkas):

```json
{
  "latitude": -6.458336, "longitude": 112.45836, "timezone": "Asia/Jakarta",
  "hourly_units": {"wave_height": "m", "wind_wave_height": "m", "swell_wave_height": "m"},
  "hourly": {
    "time": ["2026-11-18T00:00", "2026-11-18T06:00", "2026-11-18T12:00", "2026-11-18T18:00"],
    "wave_height": [0.18, 0.26, 0.2, 0.14],
    "wind_wave_height": [0.0, 0.0, 0.0, 0.02],
    "swell_wave_height": [0.14, 0.18, 0.16, 0.12],
    "ocean_current_velocity": [0.4, 0.5, 0.6, 0.8]
  }
}
```

Field yang digunakan: `hourly.time`, `wave_height` (ambang keberangkatan, misalnya di atas 2,5 m dianggap berisiko), `wind_wave_height`, `swell_wave_height`, `ocean_current_velocity` (km/jam). Catatan: resolusi model berkisar 5 sampai 25 km, sehingga titik yang terlalu dekat garis pantai dapat menghasilkan nilai kosong. Pilih titik sampel rute di perairan terbuka.

## 2. Open-Meteo Forecast API

- Base URL: `https://api.open-meteo.com/v1/forecast`
- Autentikasi, batas, dan lisensi sama dengan Marine API.
- Agent tujuan: ML Forecasting (curah hujan di 9 plant sebagai fitur permintaan), Dispatch Planner (angin di rute).

Contoh permintaan (Tuban, per 6 jam, angin dalam knot):

```
curl "https://api.open-meteo.com/v1/forecast?latitude=-6.9&longitude=112.05&hourly=precipitation,wind_speed_10m,wind_gusts_10m&daily=precipitation_sum&forecast_days=1&temporal_resolution=hourly_6&wind_speed_unit=kn&timezone=Asia%2FJakarta"
```

Contoh respons (dipangkas):

```json
{
  "hourly": {
    "time": ["2026-11-18T00:00", "2026-11-18T06:00", "2026-11-18T12:00", "2026-11-18T18:00"],
    "precipitation": [2.8, 1.1, 0.5, 3.6],
    "wind_speed_10m": [5.2, 5.3, 8.3, 4.5],
    "wind_gusts_10m": [10.3, 9.3, 18.1, 9.5]
  },
  "daily": {"time": ["2026-11-18"], "precipitation_sum": [8.7]}
}
```

Permintaan beberapa plant dalam satu panggilan juga berhasil diuji:

```
curl "https://api.open-meteo.com/v1/forecast?latitude=-6.10,-3.33&longitude=106.88,114.58&daily=precipitation_sum&forecast_days=2&timezone=Asia%2FJakarta"
```

Hasilnya berupa array JSON, satu objek per lokasi: Tanjung Priok `[6.0, 20.9]` mm dan Banjarmasin `[18.6, 19.4]` mm. Field yang digunakan: `daily.precipitation_sum`, `hourly.precipitation`, `hourly.wind_speed_10m`, `hourly.wind_gusts_10m`.

## 3. Open-Meteo Historical (Archive) API

- Base URL: `https://archive-api.open-meteo.com/v1/archive`
- Autentikasi, batas, dan lisensi sama dengan Open-Meteo lain. Data reanalisis ERA5 tersedia sejak 1940 dengan jeda sekitar 5 hari.
- Agent tujuan: ML Forecasting, untuk menyusun data latih curah hujan historis yang selaras dengan data penjualan historis.

Contoh permintaan (Makassar):

```
curl "https://archive-api.open-meteo.com/v1/archive?latitude=-5.13&longitude=119.41&start_date=2025-01-01&end_date=2025-01-03&daily=precipitation_sum&timezone=Asia%2FMakassar"
```

Contoh respons:

```json
{"latitude": -5.1669593, "longitude": 119.43022, "timezone": "Asia/Makassar",
 "daily": {"time": ["2025-01-01", "2025-01-02", "2025-01-03"], "precipitation_sum": [9.50, 13.30, 15.20]}}
```

## 4. BMKG Prakiraan Cuaca

- Base URL: `https://api.bmkg.go.id/publik/prakiraan-cuaca`
- Autentikasi: tidak diperlukan.
- Batas: 60 permintaan per menit per IP.
- Lisensi: data terbuka BMKG, wajib mencantumkan BMKG sebagai sumber.
- Agent tujuan: ML Forecasting dan Dispatch Planner, sebagai sumber resmi nasional pembanding Open-Meteo.

Parameter `adm4` adalah kode wilayah desa/kelurahan sesuai Kepmendagri. Tidak semua kode tersedia: `35.23.01.1001` dan `35.23.17.1001` mengembalikan `{"error":"Data cuaca tidak ditemukan"}`, sedangkan `35.23.17.2001` (Desa Trutup, Plumpang, Tuban) berhasil. Kode untuk 9 plant perlu dipetakan dan diuji satu per satu.

Contoh permintaan:

```
curl "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=35.23.17.2001"
```

Contoh respons (dipangkas):

```json
{
  "lokasi": {"adm4": "35.23.17.2001", "desa": "Trutup", "kecamatan": "Plumpang", "kotkab": "Tuban",
             "lat": -7.0462318351, "lon": 112.060475067, "timezone": "Asia/Jakarta"},
  "data": [{"cuaca": [[
    {"local_datetime": "2026-11-18 13:00:00", "t": 28, "hu": 83, "tp": 0.8, "weather_desc": "Cerah Berawan", "ws": 10.4, "wd": "N"},
    {"local_datetime": "2026-11-18 16:00:00", "t": 28, "hu": 80, "tp": 1, "weather_desc": "Hujan Ringan", "ws": 27.8, "wd": "SE"}
  ]]}]
}
```

Field yang digunakan: `local_datetime`, `tp` (curah hujan, mm), `ws` (angin, km/jam), `wd`, `weather_desc`. Data berupa prakiraan 3 jam untuk 3 hari ke depan, tanpa data historis, sehingga untuk data latih tetap digunakan Open-Meteo Archive.

## 5. BMKG Peta Maritim

- Base URL yang dicoba: `https://peta-maritim.bmkg.go.id/public_api/perairan/...`
- Status: Not verified. Beberapa pola URL yang beredar di dokumentasi komunitas mengembalikan 404, dan endpoint ini tidak memiliki dokumentasi resmi yang stabil.
- Agent tujuan: Dispatch Planner, sebagai sumber resmi kategori gelombang per wilayah perairan (misalnya Laut Jawa bagian timur).

Rekomendasi: gunakan Open-Meteo Marine sebagai sumber utama. BMKG Maritim dapat ditambahkan setelah daftar kode wilayah perairan yang valid diperoleh dari situs resminya.

## 6. Nager.Date

- Base URL: `https://date.nager.at/api/v3`
- Autentikasi: tidak diperlukan. Tidak ada batas resmi, gunakan secara wajar dan simpan hasilnya di cache (data hanya berubah setahun sekali).
- Lisensi: proyek sumber terbuka (MIT).
- Agent tujuan: ML Forecasting (fitur musiman).

Contoh permintaan:

```
curl "https://date.nager.at/api/v3/PublicHolidays/2026/ID"
```

Contoh respons (dipangkas):

```json
[
  {"date": "2026-01-01", "localName": "Tahun Baru Masehi", "name": "New Year's Day", "countryCode": "ID", "types": ["Public"]},
  {"date": "2026-08-17", "localName": "Hari Ulang Tahun Kemerdekaan Republik Indonesia", "countryCode": "ID", "types": ["Public"]}
]
```

Temuan penting: untuk Indonesia tahun 2026, Nager.Date hanya mengembalikan 8 hari libur. Idul Fitri, Idul Adha, Nyepi, Waisak, Imlek, Isra Mikraj, Tahun Baru Islam, dan Maulid Nabi tidak tercantum. Padahal periode Lebaran adalah faktor musiman terbesar bagi permintaan semen (proyek konstruksi berhenti). Nager.Date tidak memadai sebagai sumber tunggal.

## 7. Pustaka Python `holidays`

- Instalasi: `pip install holidays`
- Autentikasi: tidak diperlukan, berjalan offline.
- Lisensi: MIT.
- Agent tujuan: ML Forecasting.

Contoh penggunaan:

```python
import holidays
h = holidays.Indonesia(years=2026)
```

Hasil uji (17 hari libur, dipangkas):

```
2026-02-17 Tahun Baru Imlek
2026-03-19 Hari Suci Nyepi
2026-03-21 Hari Raya Idul Fitri
2026-03-22 Hari kedua dari Hari Raya Idul Fitri
2026-05-27 Hari Raya Idul Adha
2026-05-31 Hari Raya Waisak
2026-08-17 Hari Kemerdekaan Republik Indonesia
```

Pustaka ini mencakup hari raya keagamaan, tetapi belum memuat cuti bersama dari SKB 3 Menteri. Untuk fitur "minggu Lebaran", tambahkan jendela beberapa hari sebelum dan sesudah Idul Fitri secara manual di pipeline fitur.

## 8. Frankfurter

- Base URL: `https://api.frankfurter.dev/v1` (domain lama `api.frankfurter.app` kini mengembalikan 301, sehingga klien harus mengikuti redirect atau langsung menggunakan domain baru).
- Autentikasi: tidak diperlukan. Tidak ada batas resmi.
- Lisensi: sumber terbuka, data dari European Central Bank, diperbarui setiap hari kerja sekitar pukul 16.00 CET.
- Agent tujuan: Stock Monitoring atau modul biaya (opsional), misalnya konversi biaya bahan bakar kapal.

Contoh permintaan:

```
curl "https://api.frankfurter.dev/v1/latest?base=USD&symbols=IDR"
```

Contoh respons:

```json
{"amount": 1.0, "base": "USD", "date": "2026-11-17", "rates": {"IDR": 18271}}
```

Field yang digunakan: `date`, `rates.IDR`. Data historis tersedia melalui `/v1/2025-01-01..2025-12-31?base=USD&symbols=IDR`.

## 9. ExchangeRate-API Open Access

- Base URL: `https://open.er-api.com/v6/latest/{BASE}`
- Autentikasi: tidak diperlukan.
- Batas: diperbarui sekali sehari. Permintaan berlebih dibalas HTTP 429, sehingga cukup satu panggilan per hari.
- Lisensi: wajib mencantumkan atribusi ExchangeRate-API pada aplikasi.
- Agent tujuan: cadangan Frankfurter.

Contoh permintaan:

```
curl "https://open.er-api.com/v6/latest/USD"
```

Contoh respons (dipangkas):

```json
{"result": "success", "time_last_update_utc": "Wed, 18 Nov 2026 00:02:31 +0000",
 "base_code": "USD", "rates": {"IDR": 18278.202017, "EUR": 0.909215}}
```

## 10. World Bank Indicators API dan Pink Sheet

- Base URL: `https://api.worldbank.org/v2`
- Autentikasi: tidak diperlukan.
- Lisensi: CC BY 4.0.
- Agent tujuan: ML Forecasting (variabel makro tahunan), Stock Monitoring atau modul biaya (harga energi bulanan).

Contoh permintaan (kurs resmi rata-rata tahunan Indonesia):

```
curl "https://api.worldbank.org/v2/country/IDN/indicator/PA.NUS.FCRF?format=json&date=2020:2025"
```

Contoh respons (dipangkas):

```json
[{"page": 1, "total": 6, "lastupdated": "2026-11-11"},
 [{"indicator": {"id": "PA.NUS.FCRF", "value": "Official exchange rate (LCU per US$, period average)"},
   "countryiso3code": "IDN", "date": "2025", "value": 16477.8651797835}]]
```

Harga komoditas bulanan (Brent, batu bara Australia, dan lainnya) tidak tersedia sebagai API JSON. Data tersebut diterbitkan sebagai berkas Excel "Pink Sheet" (`CMO-Historical-Data-Monthly.xlsx`) di `thedocs.worldbank.org`. Permintaan HEAD ke berkas tersebut mengembalikan HTTP 200 dengan tipe spreadsheet. URL berkas berubah ketika terbit edisi baru, sehingga cara yang realistis adalah mengunduh sebulan sekali dan menyimpannya di folder `data/`. Untuk harga BBM domestik Pertamina tidak ditemukan API publik resmi.

## 11. OpenStreetMap Nominatim

- Base URL: `https://nominatim.openstreetmap.org`
- Autentikasi: tidak diperlukan, tetapi header `User-Agent` yang mengidentifikasi aplikasi wajib dikirim.
- Batas: maksimum 1 permintaan per detik, tidak untuk geocoding massal. Hasil wajib disimpan di cache.
- Lisensi: data ODbL, wajib atribusi "© OpenStreetMap contributors".
- Agent tujuan: Fleet Tracking, untuk membuat geofence pelabuhan (deteksi kapal tiba, sandar, berangkat).

Contoh permintaan dengan poligon:

```
curl -A "cement-scm-prototype/0.1" "https://nominatim.openstreetmap.org/search?q=Pelabuhan+Tanjung+Priok&format=geojson&polygon_geojson=1&polygon_threshold=0.001&limit=1"
```

Hasil uji: `Pelabuhan Tanjung Priok, Jakarta Utara`, geometri `Polygon` dengan 28 titik, titik pertama `[106.8726663, -6.1136825]`. Versi `format=jsonv2` juga mengembalikan `boundingbox`:

```json
{"osm_type": "way", "osm_id": 30088883, "lat": "-6.1045642", "lon": "106.8805674",
 "name": "Pelabuhan Tanjung Priok", "boundingbox": ["-6.1144940", "-6.0942836", "106.8726663", "106.8929386"]}
```

Untuk sepuluh pelabuhan, cukup jalankan sekali, simpan poligonnya ke `data/` sebagai GeoJSON, lalu gunakan secara lokal. Pelabuhan kecil seperti Celukan Bawang atau pelabuhan khusus Tuban mungkin tidak memiliki poligon. Untuk lokasi tersebut, gunakan geofence berupa lingkaran radius 2 sampai 3 km dari koordinat dermaga.

## 12. OpenStreetMap Overpass API

- Base URL: `https://overpass-api.de/api/interpreter`
- Autentikasi: tidak diperlukan. Server publik sering penuh: panggilan pertama menerima pesan "server is currently at capacity", panggilan ulang berhasil. Terapkan retry dengan backoff.
- Lisensi: ODbL.
- Agent tujuan: Fleet Tracking (geofence), alternatif Nominatim.

Contoh permintaan:

```
curl -A "cement-scm-prototype/0.1" --data-urlencode 'data=[out:json][timeout:25];way["landuse"="port"](around:5000,-6.10,106.88);out tags center 3;' https://overpass-api.de/api/interpreter
```

Contoh respons:

```json
{"version": 0.6, "generator": "Overpass API 0.7.62.11",
 "osm3s": {"timestamp_osm_base": "2026-11-18T05:03:01Z"}, "elements": []}
```

Endpoint berfungsi, tetapi tag `landuse=port` dan `harbour=yes` tidak menghasilkan elemen di sekitar Tanjung Priok, karena area tersebut ditandai sebagai `landuse=industrial`. Karena itu Nominatim lebih praktis untuk prototipe ini.

## 13. searoute (pustaka Python)

- Instalasi: `pip install searoute` (versi yang diuji 1.6.0).
- Autentikasi: tidak diperlukan, berjalan offline di atas jaringan rute laut global (basis data Eurostat MARNET).
- Lisensi: Apache 2.0.
- Agent tujuan: Dispatch Planner (jarak dan estimasi waktu tempuh), Fleet Tracking (lintasan rencana untuk menghitung deviasi dan ETA, serta titik sampel cuaca rute).

Contoh penggunaan:

```python
import searoute as sr
r = sr.searoute([112.05, -6.9], [131.25, -0.88], units="naut")  # [lon, lat]
r.properties["length"]          # jarak, mil laut
r.geometry["coordinates"]       # lintasan LineString
```

Hasil uji:

```
Tuban ke Sorong        : 1448.7 nmi, 15 titik lintasan, titik awal [112.656555, -6.780535]
Tuban ke Tanjung Priok : 419.9 nmi
```

Titik-titik `geometry.coordinates` dapat langsung dijadikan titik sampel cuaca untuk Open-Meteo Marine. Catatan: rute disambungkan ke simpul jaringan terdekat, sehingga titik awal tidak tepat di dermaga. Selisih ini wajar untuk tingkat prototipe.

## 14. aisstream.io

- Endpoint: WebSocket `wss://stream.aisstream.io/v0/stream`
- Autentikasi: kunci API gratis (registrasi dengan akun GitHub). Variabel lingkungan: `AISSTREAM_API_KEY`.
- Batas: pesan langganan harus dikirim dalam 3 detik setelah koneksi terbuka. Filter MMSI maksimum 50 kapal, sehingga 19 kapal masih tercakup. Layanan berstatus beta tanpa jaminan ketersediaan.
- Lisensi: ketentuan layanan aisstream.io, gratis untuk penggunaan wajar.
- Status: Not verified (kunci belum tersedia).
- Agent tujuan: Fleet Tracking.

Contoh pesan langganan setelah koneksi:

```json
{
  "APIKey": "<AISSTREAM_API_KEY>",
  "BoundingBoxes": [[[-11.0, 105.0], [2.0, 132.0]]],
  "FiltersShipMMSI": ["525000000"],
  "FilterMessageTypes": ["PositionReport"]
}
```

Field yang digunakan dari `PositionReport`: `MetaData.MMSI`, `MetaData.latitude`, `MetaData.longitude`, `MetaData.time_utc`, `Message.PositionReport.Sog` (kecepatan), `Cog`, `TrueHeading`, `NavigationalStatus`.

Keterbatasan: data berasal dari stasiun AIS darat sukarelawan, sehingga cakupan di perairan Indonesia timur (Kupang, Bitung, Sorong) kemungkinan besar terputus-putus. MMSI 19 kapal armada juga harus diketahui terlebih dahulu.

## 15. Global Fishing Watch API

- Base URL: `https://gateway.api.globalfishingwatch.org/v3`
- Autentikasi: token gratis untuk penggunaan nonkomersial setelah registrasi. Variabel lingkungan: `GFW_API_TOKEN`.
- Status: Not verified (token belum tersedia).
- Agent tujuan: Fleet Tracking, terbatas pada pencarian identitas kapal dan analisis historis.

Contoh permintaan:

```
curl -H "Authorization: Bearer $GFW_API_TOKEN" "https://gateway.api.globalfishingwatch.org/v3/vessels/search?query=<nama kapal>&datasets[0]=public-global-vessel-identity:latest"
```

Keterbatasan: fokus utama pada kapal perikanan, dan data aktivitas AIS memiliki jeda beberapa hari. API ini tidak cocok untuk pelacakan real-time, tetapi berguna untuk mencari MMSI atau IMO kapal kargo berdasarkan nama.

## Rekomendasi integrasi

Urutan integrasi yang disarankan:

1. **Open-Meteo Marine dan Forecast API.** Tanpa kunci, mendukung data per 6 jam dan beberapa titik dalam satu panggilan. Menjadi sumber utama kriteria cuaca Dispatch Planner dan fitur curah hujan ML Forecasting. Open-Meteo Archive digunakan untuk data latih historis.
2. **searoute.** Menghasilkan jarak dan lintasan 9 rute secara offline. Lintasan ini sekaligus menentukan titik sampel cuaca rute dan dasar perhitungan ETA.
3. **Pustaka `holidays` (Indonesia).** Lebih lengkap daripada Nager.Date karena memuat Idul Fitri dan hari raya keagamaan lain. Tambahkan jendela cuti bersama Lebaran secara manual.
4. **Nominatim untuk geofence, ditambah aisstream.io untuk posisi kapal.** Poligon pelabuhan diambil sekali dan disimpan lokal. Untuk AIS, simpan kunci di `AISSTREAM_API_KEY`. Karena cakupan AIS gratis di Indonesia timur tidak dapat dijamin, siapkan simulator posisi kapal yang bergerak di sepanjang lintasan searoute sebagai cadangan, sehingga Fleet Tracking Agent tetap dapat didemonstrasikan.

Variabel lingkungan yang diperlukan:

| Variabel | Layanan | Wajib |
|---|---|---|
| `AISSTREAM_API_KEY` | aisstream.io | Ya, untuk AIS real-time |
| `GFW_API_TOKEN` | Global Fishing Watch | Tidak, opsional |

Sumber lain (BMKG, Frankfurter, World Bank) bersifat pelengkap dan dapat ditambahkan setelah empat integrasi di atas berjalan. Seluruh atribusi lisensi (Open-Meteo, BMKG, OpenStreetMap, ExchangeRate-API) perlu dicantumkan di halaman dasbor atau README proyek.
