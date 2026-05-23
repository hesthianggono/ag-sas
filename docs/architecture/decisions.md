# Architecture Decision Records

## ADR-001: Calculation Engine Terpisah dari API Layer

**Keputusan:** Semua fungsi kalkulasi berada di `app/calculation/` dan tidak memiliki dependency ke database atau FastAPI.

**Alasan:** Memungkinkan unit test murni tanpa mock database, dan memudahkan migrasi ke calculation microservice di masa depan.

## ADR-002: Setiap Hasil Kalkulasi Menyimpan Input Snapshot

**Keputusan:** `CalculationRecord.input_data` menyimpan seluruh input pada saat perhitungan (JSON).

**Alasan:** Audit trail — engineer dapat mereproduksi hasil dengan input yang sama.

## ADR-003: Formula Version di Setiap Output

**Keputusan:** Setiap output kalkulasi menyertakan `formula_version` (SemVer).

**Alasan:** Ketika formula dikoreksi, hasil lama tetap dapat diidentifikasi versinya.

## ADR-004: ReportLab untuk PDF (bukan WeasyPrint)

**Keputusan:** Menggunakan ReportLab karena tidak memerlukan dependensi sistem (Cairo, GTK).

**Alasan:** Lebih mudah dijalankan di Docker tanpa layer OS tambahan.

## ADR-005: JWT Stateless (tidak ada refresh token di DB)

**Keputusan:** JWT access token saja, tidak ada tabel refresh token untuk MVP.

**Alasan:** Menyederhanakan implementasi MVP. Refresh token akan ditambahkan di v1.1.
