"""Section builders untuk laporan rekayasa lengkap AG-SAS."""
from app.reporting.full_report.sections.s01_introduction import build_s01
from app.reporting.full_report.sections.s02_project_data import build_s02
from app.reporting.full_report.sections.s03_design_basis import build_s03
from app.reporting.full_report.sections.s04_materials import build_s04
from app.reporting.full_report.sections.s05_loads import build_s05
from app.reporting.full_report.sections.s06_structural_model import build_s06
from app.reporting.full_report.sections.s07_analysis import build_s07
from app.reporting.full_report.sections.s08_design import build_s08
from app.reporting.full_report.sections.s09_serviceability import build_s09
from app.reporting.full_report.sections.s10_summary import build_s10
from app.reporting.full_report.sections.s11_appendix import build_s11

__all__ = [
    "build_s01", "build_s02", "build_s03", "build_s04", "build_s05",
    "build_s06", "build_s07", "build_s08", "build_s09", "build_s10",
    "build_s11",
]
