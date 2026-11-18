---
name: saw-decision-engine
description: Referensi rumus decision engine (usable stock, days of cover, priority score grade 1-5, SAW ranking kapal, greedy assignment, Weibull failure risk) di Manufacturing Agentic System. Gunakan saat mengubah, menjelaskan, atau menguji decision engine.
---
# Decision engine (proposal Bab 6)

Implementasi: `shared/decision_engine.py`. Uji: `tests/test_decision_engine.py`.

**Pers. 1-2.** `Usable(p,c) = sum_s max(0, L(s)*Cap(s) - DS(s))`; `DoC(p,c) = Usable / mean(P50 14 hari)`.

**Pers. 14, priority plant.** Tiap kriteria diberi grade 1-5 dari batas `b(i,1..4)`; kriteria "lebih kecil lebih mendesak" urutannya dibalik. `Score(p) = sum_i w_i * g(i,p)` (skala 1-5).

| Kriteria | Bobot | Arah |
|---|---|---|
| Stock-out days (ARIMA) | 0,35 | kecil = mendesak |
| Endurance (days of cover) | 0,20 | kecil = mendesak |
| Selling price | 0,20 | besar = penting |
| Forecast demand (P50) | 0,15 | besar = penting |
| Contribution margin | 0,10 | besar = penting |

**Pers. 15-16, SAW kapal per plant.** Benefit `r = x/max x`, cost `r = min x / x`. Kriteria tanpa data untuk semua kandidat dikeluarkan dan bobot diskalakan ulang (`w'`).

| Kriteria | Bobot | Jenis |
|---|---|---|
| Arrival time (jam, RF ETA) | 0,35 | cost |
| Capacity (ton) | 0,20 | benefit |
| Proven calls ke plant | 0,20 | benefit |
| Evidence (kesegaran GPS 0-1) | 0,15 | benefit |
| Weather (wave height, m) | 0,10 | cost |

Kandidat dikeluarkan bila: maintenance, cement type tidak cocok, sudah ditugaskan, atau wave > 2,5 m (sailing not advised). Failure risk Weibull > 30% diberi warning.

**Pers. 17-18, assignment.** Plant diurutkan dari `Score(p)` tertinggi; tiap plant mengambil kapal terbaik yang masih bebas; simpan maksimal tiga alternatif.

Aturan: LLM tidak pernah menghitung angka ini. Narrator hanya mengutip output engine.
