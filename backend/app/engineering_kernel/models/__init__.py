"""
AG-SAS Structural Data Models
==============================
Struktur data dasar untuk semua entitas model struktur.
Semua model adalah pure Python dataclass — tidak ada dependensi web/DB.
"""

from app.engineering_kernel.models.geometry import Node, Element, Support
from app.engineering_kernel.models.material import Material, STEEL_BJ41, STEEL_BJ37, CONCRETE_FC21, CONCRETE_FC25, CONCRETE_FC30
from app.engineering_kernel.models.section import SectionProperties, SectionType
from app.engineering_kernel.models.loads import (
    LoadDirection,
    LoadCaseType,
    NodalLoad,
    UniformMemberLoad,
    TrapezoidMemberLoad,
    PointMemberLoad,
    TemperatureLoad,
    LoadCase,
)
from app.engineering_kernel.models.combination import LoadCombination, LoadFactor
from app.engineering_kernel.models.results import (
    NodeDisplacement,
    NodeReaction,
    ElementEndForces,
    AnalysisResult,
    DesignCheckStatus,
    DesignCheckResult,
)

__all__ = [
    # Geometri
    "Node", "Element", "Support",
    # Material
    "Material", "STEEL_BJ41", "STEEL_BJ37", "CONCRETE_FC21", "CONCRETE_FC25", "CONCRETE_FC30",
    # Penampang
    "SectionProperties", "SectionType",
    # Beban
    "LoadDirection", "LoadCaseType", "NodalLoad",
    "UniformMemberLoad", "TrapezoidMemberLoad", "PointMemberLoad",
    "TemperatureLoad", "LoadCase",
    # Kombinasi beban
    "LoadCombination", "LoadFactor",
    # Hasil
    "NodeDisplacement", "NodeReaction", "ElementEndForces",
    "AnalysisResult", "DesignCheckStatus", "DesignCheckResult",
]
