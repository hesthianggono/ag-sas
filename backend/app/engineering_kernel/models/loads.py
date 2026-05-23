"""
Model beban struktur AG-SAS.

Satuan semua beban dalam satuan internal solver:
  Gaya     : kN
  Momen    : kN·m
  Beban merata: kN/m
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Union


class LoadDirection(str, Enum):
    """
    Arah beban yang dapat diterapkan pada elemen.

    GX, GY, GZ = arah global X, Y, Z
    LX, LY, LZ = arah lokal elemen (x_lokal = I→J, y_lokal = tegak lurus)
    GRAVITY     = arah -Y global (shorthand untuk beban gravitasi)
    """
    GLOBAL_X  = "GX"
    GLOBAL_Y  = "GY"
    GLOBAL_Z  = "GZ"
    LOCAL_X   = "LX"
    LOCAL_Y   = "LY"
    LOCAL_Z   = "LZ"
    GRAVITY   = "GY_NEG"   # ekivalen dengan -Y global


class LoadCaseType(str, Enum):
    """
    Tipe load case berdasarkan SNI 1727:2020.

    Digunakan untuk pengelompokan beban dalam kombinasi.
    """
    DEAD         = "D"    # Beban mati
    LIVE         = "L"    # Beban hidup
    ROOF_LIVE    = "Lr"   # Beban hidup atap
    SNOW         = "S"    # Beban salju (jarang di Indonesia, tapi disertakan)
    WIND         = "W"    # Beban angin
    EARTHQUAKE   = "E"    # Beban gempa
    TEMPERATURE  = "T"    # Beban temperatur
    CONSTRUCTION = "C"    # Beban konstruksi
    SELF_WEIGHT  = "SW"   # Berat sendiri (dihitung otomatis dari material+section)
    OTHER        = "O"    # Lain-lain


# ── Beban nodal ───────────────────────────────────────────────────────────────

@dataclass
class NodalLoad:
    """
    Beban yang diterapkan langsung pada node.

    Semua nilai dalam satuan internal solver (kN, kN·m).
    Nilai nol (default) berarti tidak ada beban dalam arah tersebut.

    Attributes:
        node_id:   ID node tempat beban diterapkan
        fx_kn:     Gaya arah X global [kN]
        fy_kn:     Gaya arah Y global [kN]
        fz_kn:     Gaya arah Z global [kN]
        mx_knm:    Momen arah X global [kN·m]
        my_knm:    Momen arah Y global [kN·m]
        mz_knm:    Momen arah Z global [kN·m]
        name:      Label beban untuk laporan
    """
    node_id: str
    fx_kn:  float = 0.0
    fy_kn:  float = 0.0
    fz_kn:  float = 0.0
    mx_knm: float = 0.0
    my_knm: float = 0.0
    mz_knm: float = 0.0
    name: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.node_id.strip():
            errors.append("NodalLoad.node_id tidak boleh kosong.")
        all_zero = all(
            v == 0.0 for v in [self.fx_kn, self.fy_kn, self.fz_kn,
                                self.mx_knm, self.my_knm, self.mz_knm]
        )
        if all_zero:
            errors.append(
                f"NodalLoad pada node '{self.node_id}': semua komponen = 0 — "
                "beban ini tidak menghasilkan efek."
            )
        return errors

    def is_zero(self) -> bool:
        return all(
            v == 0.0 for v in [self.fx_kn, self.fy_kn, self.fz_kn,
                                self.mx_knm, self.my_knm, self.mz_knm]
        )


# ── Beban merata elemen ───────────────────────────────────────────────────────

@dataclass
class UniformMemberLoad:
    """
    Beban merata konstan sepanjang elemen.

    Attributes:
        element_id:  ID elemen
        direction:   Arah beban (LoadDirection)
        w_kn_m:      Intensitas beban [kN/m] — dapat negatif
        name:        Label beban
    """
    element_id: str
    direction: LoadDirection
    w_kn_m: float
    name: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.element_id.strip():
            errors.append("UniformMemberLoad.element_id tidak boleh kosong.")
        if self.w_kn_m == 0.0:
            errors.append(
                f"UniformMemberLoad pada elemen '{self.element_id}': w=0 tidak menghasilkan efek."
            )
        return errors


@dataclass
class TrapezoidMemberLoad:
    """
    Beban trapesoid: intensitas berubah linear dari node I ke node J.

    Attributes:
        element_id:  ID elemen
        direction:   Arah beban
        w_i_kn_m:    Intensitas di node I [kN/m]
        w_j_kn_m:    Intensitas di node J [kN/m]
        name:        Label beban
    """
    element_id: str
    direction: LoadDirection
    w_i_kn_m: float
    w_j_kn_m: float
    name: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.element_id.strip():
            errors.append("TrapezoidMemberLoad.element_id tidak boleh kosong.")
        if self.w_i_kn_m == 0.0 and self.w_j_kn_m == 0.0:
            errors.append(
                f"TrapezoidMemberLoad pada elemen '{self.element_id}': "
                "w_i=0 dan w_j=0 tidak menghasilkan efek."
            )
        return errors


@dataclass
class PointMemberLoad:
    """
    Beban terpusat di posisi tertentu sepanjang elemen.

    Attributes:
        element_id:  ID elemen
        direction:   Arah beban
        P_kn:        Besar gaya [kN]
        a_m:         Jarak dari node I [m], harus 0 ≤ a ≤ L
        name:        Label beban
    """
    element_id: str
    direction: LoadDirection
    P_kn: float
    a_m: float             # jarak dari node I [m]
    name: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.element_id.strip():
            errors.append("PointMemberLoad.element_id tidak boleh kosong.")
        if self.P_kn == 0.0:
            errors.append(
                f"PointMemberLoad pada elemen '{self.element_id}': P=0 tidak menghasilkan efek."
            )
        if self.a_m < 0:
            errors.append(
                f"PointMemberLoad pada elemen '{self.element_id}': "
                f"a={self.a_m} m harus ≥ 0."
            )
        return errors


@dataclass
class TemperatureLoad:
    """
    Beban temperatur (perubahan suhu seragam) pada elemen.
    Menghasilkan gaya aksial ekivalen: N = E·A·α·ΔT

    Attributes:
        element_id:  ID elemen
        delta_T_C:   Perubahan temperatur ΔT [°C] — positif = ekspansi
        alpha:       Koefisien termal [1/°C] — default baja: 1.2e-5
        name:        Label beban
    """
    element_id: str
    delta_T_C: float
    alpha: float = 1.2e-5     # default baja SNI 1729:2020
    name: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.element_id.strip():
            errors.append("TemperatureLoad.element_id tidak boleh kosong.")
        if self.delta_T_C == 0.0:
            errors.append(
                f"TemperatureLoad pada elemen '{self.element_id}': ΔT=0 tidak menghasilkan efek."
            )
        if self.alpha <= 0:
            errors.append(
                f"TemperatureLoad pada elemen '{self.element_id}': "
                f"alpha={self.alpha} harus > 0."
            )
        return errors


# ── Load Case ─────────────────────────────────────────────────────────────────

MemberLoadUnion = Union[UniformMemberLoad, TrapezoidMemberLoad, PointMemberLoad, TemperatureLoad]


@dataclass
class LoadCase:
    """
    Satu load case = satu kondisi pembebanan independen.

    Beberapa load case dikombinasikan oleh LoadCombination (models/combination.py).

    Attributes:
        id:              Identifikasi unik (e.g. "DL", "LL1", "WX")
        name:            Nama deskriptif (e.g. "Beban Mati", "Beban Hidup Lantai 1")
        type:            Tipe load case (LoadCaseType)
        nodal_loads:     Daftar beban nodal
        member_uniform:  Daftar beban merata elemen
        member_trapezoid: Daftar beban trapesoid elemen
        member_point:    Daftar beban terpusat pada elemen
        temperature:     Daftar beban temperatur
        description:     Catatan tambahan
    """
    id: str
    name: str
    type: LoadCaseType
    nodal_loads: list[NodalLoad] = field(default_factory=list)
    member_uniform: list[UniformMemberLoad] = field(default_factory=list)
    member_trapezoid: list[TrapezoidMemberLoad] = field(default_factory=list)
    member_point: list[PointMemberLoad] = field(default_factory=list)
    temperature: list[TemperatureLoad] = field(default_factory=list)
    description: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("LoadCase.id tidak boleh kosong.")
        total_loads = (
            len(self.nodal_loads) + len(self.member_uniform) +
            len(self.member_trapezoid) + len(self.member_point) +
            len(self.temperature)
        )
        if total_loads == 0:
            errors.append(
                f"LoadCase '{self.id}': tidak ada beban yang didefinisikan."
            )
        # Validasi masing-masing beban
        for load in self.nodal_loads:
            errors.extend(load.validate())
        for load in self.member_uniform:
            errors.extend(load.validate())
        for load in self.member_trapezoid:
            errors.extend(load.validate())
        for load in self.member_point:
            errors.extend(load.validate())
        for load in self.temperature:
            errors.extend(load.validate())
        return errors

    def is_empty(self) -> bool:
        return (
            not self.nodal_loads and not self.member_uniform and
            not self.member_trapezoid and not self.member_point and
            not self.temperature
        )
