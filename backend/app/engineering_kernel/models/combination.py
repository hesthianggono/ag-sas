"""
Model kombinasi beban AG-SAS.

LoadCombination mendefinisikan cara menggabungkan beberapa LoadCase
dengan faktor pengali.

Kombinasi aktual (SNI built-in dan custom) disimpan di database
melalui model LoadCombinationRule (app/models/load_combination_rule.py).
Struktur di sini adalah representasi runtime yang digunakan solver.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DesignMethod(str, Enum):
    """Metode desain yang digunakan untuk kombinasi beban."""
    LRFD = "LRFD"   # Load and Resistance Factor Design (SNI 1727:2020)
    ASD  = "ASD"    # Allowable Stress Design


@dataclass
class LoadFactor:
    """
    Faktor pengali untuk satu load case dalam kombinasi.

    Attributes:
        load_case_id:   ID LoadCase
        load_case_type: Tipe load case ("D", "L", "W", "E", dst.)
        factor:         Faktor pengali (e.g. 1.2, 1.6, 0.9)
    """
    load_case_id: str
    load_case_type: str    # nilai dari LoadCaseType.value
    factor: float

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.load_case_id.strip():
            errors.append("LoadFactor.load_case_id tidak boleh kosong.")
        if self.factor == 0.0:
            errors.append(
                f"LoadFactor untuk '{self.load_case_id}': faktor=0 — "
                "load case tidak berkontribusi pada kombinasi ini."
            )
        return errors


@dataclass
class LoadCombination:
    """
    Definisi runtime satu kombinasi beban.

    Ini adalah representasi yang digunakan solver — dibuat dari
    LoadCombinationRule yang tersimpan di database.

    Superposisi linear:
      U_combo = Σ(factor_i × U_case_i)

    Prinsip: Solve sekali per load case, kemudian scale dan sum hasilnya.
    JANGAN solve ulang untuk setiap kombinasi.

    Attributes:
        id:                  Identifikasi unik (e.g. "U2")
        name:                Nama deskriptif (e.g. "1.2D + 1.6L")
        expression:          Ekspresi string (e.g. "1.2D + 1.6L")
        method:              LRFD atau ASD
        load_factors:        Daftar LoadFactor
        source_reference:    Referensi pasal standar
        db_rule_id:          ID LoadCombinationRule di database (untuk traceability)
        description:         Catatan tambahan
    """
    id: str
    name: str
    expression: str
    method: DesignMethod
    load_factors: list[LoadFactor] = field(default_factory=list)
    source_reference: str = ""
    db_rule_id: Optional[int] = None
    description: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("LoadCombination.id tidak boleh kosong.")
        if not self.load_factors:
            errors.append(
                f"LoadCombination '{self.id}': tidak ada load factor — "
                "kombinasi tidak dapat dihitung."
            )
        for lf in self.load_factors:
            errors.extend(lf.validate())
        # Cek duplikasi load_case_id
        ids = [lf.load_case_id for lf in self.load_factors]
        if len(ids) != len(set(ids)):
            errors.append(
                f"LoadCombination '{self.id}': ada load_case_id yang duplikat."
            )
        return errors

    def get_factor(self, load_case_id: str) -> float:
        """Kembalikan faktor untuk load case tertentu. 0.0 jika tidak ada."""
        for lf in self.load_factors:
            if lf.load_case_id == load_case_id:
                return lf.factor
        return 0.0

    def get_factor_by_type(self, load_case_type: str) -> Optional[float]:
        """
        Kembalikan faktor berdasarkan tipe load case.
        None jika tipe tidak ada dalam kombinasi.
        """
        for lf in self.load_factors:
            if lf.load_case_type == load_case_type:
                return lf.factor
        return None

    @property
    def involved_load_case_ids(self) -> list[str]:
        """Daftar ID load case yang terlibat dalam kombinasi ini."""
        return [lf.load_case_id for lf in self.load_factors]


# ── Kombinasi SNI 1727:2020 LRFD — template (bukan hardcode untuk solver) ────
# Ini adalah deskripsi untuk keperluan seeding database.
# Nilai aktual yang digunakan solver diambil dari DB (LoadCombinationRule).

SNI_1727_2020_LRFD_TEMPLATES = [
    {
        "combination_name": "U1: 1.4D",
        "expression": "1.4D",
        "method": "LRFD",
        "load_factors": {"D": 1.4},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 1",
    },
    {
        "combination_name": "U2: 1.2D + 1.6L",
        "expression": "1.2D + 1.6L",
        "method": "LRFD",
        "load_factors": {"D": 1.2, "L": 1.6},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 2",
    },
    {
        "combination_name": "U3: 1.2D + 1.6Lr + L",
        "expression": "1.2D + 1.6Lr + L",
        "method": "LRFD",
        "load_factors": {"D": 1.2, "Lr": 1.6, "L": 1.0},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 3",
    },
    {
        "combination_name": "U4a: 1.2D + 1.0W + L",
        "expression": "1.2D + 1.0W + L",
        "method": "LRFD",
        "load_factors": {"D": 1.2, "W": 1.0, "L": 1.0},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 4a",
    },
    {
        "combination_name": "U4b: 0.9D + 1.0W",
        "expression": "0.9D + 1.0W",
        "method": "LRFD",
        "load_factors": {"D": 0.9, "W": 1.0},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 4b",
    },
    {
        "combination_name": "U5a: 1.2D + 1.0E + L",
        "expression": "1.2D + 1.0E + L",
        "method": "LRFD",
        "load_factors": {"D": 1.2, "E": 1.0, "L": 1.0},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 5a",
    },
    {
        "combination_name": "U5b: 0.9D + 1.0E",
        "expression": "0.9D + 1.0E",
        "method": "LRFD",
        "load_factors": {"D": 0.9, "E": 1.0},
        "source_reference": "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi 5b",
    },
]
