"""
AG-SAS Engineering Kernel
=========================
Fondasi teknis untuk semua modul analisis struktur AG-SAS.

Kernel ini mendefinisikan:
- Sistem satuan dan konversi (units/)
- Konvensi tanda dan koordinat (conventions/)
- Struktur data dasar (models/)
- Sistem traceability (traceability/)

Aturan penggunaan:
- Semua modul solver dan calculation HARUS mengimpor tipe dari kernel ini.
- Kernel TIDAK boleh mengimpor FastAPI, SQLModel, atau dependensi web/DB.
- Kernel TIDAK mengimplementasikan solver — hanya fondasi data dan kontrak tipe.
"""

KERNEL_VERSION: str = "0.1.0"
"""Versi semantik kernel. Dinaikkan setiap ada perubahan pada kontrak tipe atau konvensi."""
