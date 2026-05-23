"""
Konvensi Tanda Resmi AG-SAS
============================
Ini adalah SATU-SATUNYA sumber kebenaran untuk konvensi tanda di seluruh AG-SAS.
Tidak ada modul lain yang boleh mendefinisikan ulang konvensi ini.

Referensi utama:
  McGuire, Gallagher, Ziemian — "Matrix Structural Analysis" 2nd Ed. §3.2
  (selanjutnya disebut "McGuire MSA")

Versi: 1.0 (2026-05-22)
"""

from dataclasses import dataclass
from enum import Enum

# ── Identitas dokumen ─────────────────────────────────────────────────────────

SIGN_CONVENTION_VERSION: str = "1.0"
SIGN_CONVENTION_REFERENCE: str = (
    "McGuire, Gallagher, Ziemian — 'Matrix Structural Analysis' 2nd Ed. §3.2"
)


# ── Sumbu global ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _GlobalAxes:
    """
    Definisi arah sumbu koordinat global AG-SAS.

    Sistem koordinat: Right-hand rule (aturan tangan kanan).

      X → horizontal (positif ke kanan)
      Y ↑ vertikal   (positif ke atas, berlawanan dengan gravitasi)
      Z ○ keluar bidang XY (positif keluar dari layar/halaman)

    Gravitasi bekerja dalam arah -Y global.
    """
    X: str = "horizontal, positif ke kanan (+→)"
    Y: str = "vertikal, positif ke atas (+↑), berlawanan gravitasi"
    Z: str = "keluar bidang XY, positif keluar layar (+○), right-hand rule"
    gravity_direction: str = "-Y global"
    handedness: str = "right-hand rule"

GLOBAL_AXES = _GlobalAxes()


# ── Konvensi gaya aksial ──────────────────────────────────────────────────────

class AxialSignConvention(str, Enum):
    """
    Konvensi tanda gaya aksial elemen (dalam koordinat lokal elemen).

    POSITIF  = TARIK (tension)  — elemen memanjang
    NEGATIF  = TEKAN (compression) — elemen memendek

    Ref: McGuire MSA §3.2, Gambar 3.2-1
    Konsisten dengan: AISC, SAP2000, ETABS default.
    """
    TENSION_POSITIVE = "tarik_positif"
    COMPRESSION_NEGATIVE = "tekan_negatif"

    @classmethod
    def description(cls) -> str:
        return (
            "Gaya aksial N: positif = tarik (tension), negatif = tekan (compression). "
            "Ref: McGuire MSA §3.2"
        )


# ── Konvensi gaya geser ───────────────────────────────────────────────────────

class ShearSignConvention(str, Enum):
    """
    Konvensi tanda gaya geser elemen (dalam koordinat lokal elemen).

    Pada potongan di posisi x dari node I:
      Gaya geser V positif = gaya geser yang bekerja ke atas (+y lokal)
      pada muka kiri potongan (sisi node I).

    Ekivalen: V positif pada potongan kiri menyebabkan rotasi searah jarum jam
    pada elemen bebas di sebelah kiri.

    Ref: McGuire MSA §3.2, Gambar 3.2-2
    """
    POSITIVE_UP_LEFT_FACE = "geser_naik_muka_kiri_positif"

    @classmethod
    def description(cls) -> str:
        return (
            "Gaya geser V: positif = gaya ke atas (+y lokal) pada muka kiri potongan. "
            "Ref: McGuire MSA §3.2"
        )


# ── Konvensi momen lentur ─────────────────────────────────────────────────────

class MomentSignConvention(str, Enum):
    """
    Konvensi tanda momen lentur (dalam koordinat lokal elemen).

    Momen Mz (lentur dalam bidang XY lokal):
      POSITIF = sagging convention = serat bawah tarik, kurva cekung ke atas (∪)
      NEGATIF = hogging = serat atas tarik, kurva cembung ke atas (∩)

    Momen Mx (torsi):
      Positif mengikuti right-hand rule terhadap sumbu x lokal (arah I→J).

    Ref: McGuire MSA §3.2 — konsisten dengan mayoritas textbook struktur.

    CATATAN: Beberapa software (SAP2000) menggunakan konvensi berbeda untuk
    momen di nodal force vector vs diagram — periksa saat validasi cross-software.
    """
    SAGGING_POSITIVE = "sagging_positif_serat_bawah_tarik"

    @classmethod
    def description(cls) -> str:
        return (
            "Momen Mz: positif = sagging (serat bawah tarik, ∪). "
            "Ref: McGuire MSA §3.2"
        )


# ── Konvensi displacement ─────────────────────────────────────────────────────

class DisplacementSignConvention(str, Enum):
    """
    Konvensi tanda perpindahan nodal (koordinat global).

    ux positif = translasi arah +X global
    uy positif = translasi arah +Y global (ke atas)
    uz positif = translasi arah +Z global (keluar bidang)
    rx positif = rotasi berlawanan jarum jam dilihat dari +X
    ry positif = rotasi berlawanan jarum jam dilihat dari +Y
    rz positif = rotasi berlawanan jarum jam dilihat dari +Z (dalam bidang XY)

    Ref: McGuire MSA §4.1
    """
    POSITIVE_ALONG_POSITIVE_AXIS = "positif_searah_sumbu_positif"

    @classmethod
    def description(cls) -> str:
        return (
            "Displacement: positif searah sumbu global positif. "
            "Rotasi: positif berlawanan jarum jam (right-hand rule). "
            "Ref: McGuire MSA §4.1"
        )


# ── Konvensi reaksi perletakan ────────────────────────────────────────────────

class ReactionSignConvention(str, Enum):
    """
    Konvensi tanda reaksi perletakan.

    Reaksi dilaporkan dalam sistem koordinat global, arah positif sama dengan
    arah gaya eksternal positif.

    Reaksi positif berarti perletakan memberikan gaya ke node dalam arah positif.
    Contoh: reaksi Ry = +50 kN berarti perletakan mendorong node ke atas (+Y).

    Ref: McGuire MSA §5.3
    """
    POSITIVE_SAME_AS_EXTERNAL_FORCE = "positif_searah_gaya_eksternal"

    @classmethod
    def description(cls) -> str:
        return (
            "Reaksi: positif = perletakan mendorong node dalam arah sumbu positif. "
            "Ref: McGuire MSA §5.3"
        )


# ── Konvensi transformasi lokal-global ───────────────────────────────────────

@dataclass(frozen=True)
class _LocalGlobalTransformation:
    """
    Aturan transformasi koordinat lokal elemen ke koordinat global.

    Sumbu lokal elemen 2D:
      x_lokal = arah dari node I ke node J (unit vector)
      y_lokal = tegak lurus x_lokal, 90° berlawanan jarum jam

    Sudut θ = sudut antara x_lokal dan x_global (+X):
      θ positif = putaran berlawanan jarum jam dari +X ke x_lokal

    Matriks transformasi T (6×6 untuk elemen 2D):
      K_global = Tᵀ · K_lokal · T
      F_global = Tᵀ · F_lokal
      u_lokal  = T · u_global

    Ref: McGuire MSA §4.2, Persamaan 4.2-7
    """
    formula: str = "K_global = Tᵀ · K_lokal · T"
    positive_angle: str = "berlawanan jarum jam dari +X global ke x_lokal"
    reference: str = "McGuire MSA §4.2, Persamaan 4.2-7"

LOCAL_GLOBAL_TRANSFORM = _LocalGlobalTransformation()
