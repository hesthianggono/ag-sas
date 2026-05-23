"""
HTML Report Renderer
=====================
Merender template Jinja2 menjadi HTML string untuk preview laporan.
Data dipreparasi di sini agar template tetap bersih (logika minimal di template).
"""
from __future__ import annotations
import math
from pathlib import Path
from datetime import datetime
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)

# Custom filter: format float to 4 decimal places
_env.filters["fmt4"] = lambda v: f"{v:.4f}" if isinstance(v, float) else str(v)


# ── Standard reference definitions ────────────────────────────────────────────

_SNI_MAP = {
    "SNI 1727:2020": "Beban Desain Minimum dan Kriteria Terkait untuk Bangunan Gedung — Kombinasi beban LRFD Pasal 5.3.1",
    "SNI 2847:2019": "Persyaratan Beton Struktural untuk Bangunan Gedung — Desain lentur singly reinforced, faktor β₁, ρ_min, ρ_max, φMn",
    "SNI 1729:2020": "Spesifikasi untuk Bangunan Gedung Baja Struktural — Cek kelangsingan sayap B4.1b, kapasitas lentur F2/F3",
    "SNI 1726:2019": "Tata Cara Perencanaan Ketahanan Gempa untuk Struktur Bangunan Gedung",
    "SNI 7860:2020": "Ketentuan Seismik untuk Struktur Baja Struktural",
}


def _parse_standards(standard_references: str) -> list[dict]:
    """Ekstrak kode standar dari string referensi dan beri deskripsi."""
    standards = []
    seen = set()
    for code, desc in _SNI_MAP.items():
        if code in standard_references and code not in seen:
            standards.append({"code": code, "scope": desc})
            seen.add(code)
    if not standards:
        # fallback: split by comma
        for part in standard_references.split(","):
            code = part.strip()
            if code and code not in seen:
                standards.append({"code": code, "scope": "—"})
                seen.add(code)
    return standards


def _build_concrete_context(input_data: dict, output_data: dict) -> dict:
    """Build template context khusus untuk concrete_beam."""
    fc = input_data["fc_prime_mpa"]
    fy = input_data["fy_mpa"]
    eff_d = output_data["effective_depth_d_mm"]
    sw_knm = input_data.get("dead_load_w_knm", 0)
    wl_knm = input_data.get("live_load_w_knm", 0)
    wu = output_data["wu_knm"]

    material = {
        "fc_prime_mpa": fc,
        "fy_mpa": fy,
        "ec_mpa": 4700 * math.sqrt(fc),
    }
    geometry = {
        "width_b_mm": input_data["width_b_mm"],
        "height_h_mm": input_data["height_h_mm"],
        "cover_cc_mm": input_data["cover_cc_mm"],
        "stirrup_diameter_mm": input_data["stirrup_diameter_mm"],
        "bar_diameter_mm": input_data["bar_diameter_mm"],
        "effective_depth_d_mm": round(eff_d, 1),
        "span_l_m": input_data["span_l_m"],
    }
    loading = {
        "dead_load_w_knm": sw_knm,
        "live_load_w_knm": wl_knm,
        "span_l_m": input_data["span_l_m"],
    }
    combination = {"wu_knm": round(wu, 3)}
    forces = {
        "mu_ultimate_knm": round(output_data["mu_ultimate_knm"], 2),
        "vu_ultimate_kn": round(output_data["vu_ultimate_kn"], 2),
    }
    capacity = {
        "beta1": round(output_data["beta1"], 4),
        "rho_min": output_data["rho_min"],
        "rho_max": output_data["rho_max"],
        "rho_required": output_data["rho_required"],
        "as_required_mm2": round(output_data["as_required_mm2"], 1),
        "as_min_mm2": round(output_data["as_min_mm2"], 1),
        "as_design_mm2": round(output_data["as_design_mm2"], 1),
        "bar_area_mm2": round(output_data["bar_area_mm2"], 1),
        "num_bars": output_data["num_bars"],
        "a_block_mm": round(output_data["a_block_mm"], 2),
        "mn_knm": round(output_data["mn_knm"], 2),
        "phi_factor": output_data["phi_factor"],
        "phi_mn_knm": round(output_data["phi_mn_knm"], 2),
        "capacity_ratio": round(output_data["capacity_ratio"], 4),
        "is_compact": None,
    }
    summary = {
        "loads": [
            {"label": "wu terfaktor", "value": round(wu, 3), "unit": "kN/m", "highlight": False},
            {"label": "Mu ultimit", "value": round(output_data["mu_ultimate_knm"], 2), "unit": "kN·m", "highlight": True},
            {"label": "Vu ultimit", "value": round(output_data["vu_ultimate_kn"], 2), "unit": "kN", "highlight": False},
        ],
        "capacity": [
            {"label": "d efektif", "value": round(eff_d, 1), "unit": "mm", "highlight": False},
            {"label": f"As ({output_data['num_bars']}×Ø{input_data['bar_diameter_mm']})", "value": round(output_data["as_design_mm2"], 0), "unit": "mm²", "highlight": True},
            {"label": "φMn kapasitas", "value": round(output_data["phi_mn_knm"], 2), "unit": "kN·m", "highlight": True},
            {"label": "Mu/φMn", "value": round(output_data["capacity_ratio"], 3), "unit": "—", "highlight": False},
        ],
    }
    return dict(material=material, geometry=geometry, loading=loading,
                combination=combination, forces=forces, capacity=capacity, summary=summary)


def _build_steel_context(input_data: dict, output_data: dict) -> dict:
    """Build template context khusus untuk steel_beam."""
    fy = input_data.get("fy_mpa", 250.0)
    sw = output_data["self_weight_knm"]
    wd = input_data["dead_load_w_knm"]
    wl = input_data["live_load_w_knm"]
    wu = output_data["wu_knm"]
    L = input_data["span_l_m"]

    material = {"fy_mpa": fy}
    geometry = {
        "profile_designation": output_data["profile_designation"],
        "height_h_mm": input_data.get("height_h_mm", "—"),
        "flange_width_b_mm": input_data.get("flange_width_b_mm", "—"),
        "web_thickness_tw_mm": input_data.get("web_thickness_tw_mm", "—"),
        "flange_thickness_tf_mm": input_data.get("flange_thickness_tf_mm", "—"),
        "sx_cm3": output_data["sx_cm3"],
        "zx_cm3": output_data["zx_cm3"],
        "weight_per_m_kgm": output_data["weight_per_m_kgm"],
        "span_l_m": L,
    }
    loading = {
        "dead_load_w_knm": wd,
        "live_load_w_knm": wl,
        "self_weight_knm": round(sw, 4),
        "dead_total_knm": round(wd + sw, 4),
        "span_l_m": L,
    }
    combination = {"wu_knm": round(wu, 3)}
    forces = {
        "mu_ultimate_knm": round(output_data["mu_ultimate_knm"], 2),
        "vu_ultimate_kn": None,
    }
    capacity = {
        "lambda_f": round(output_data["lambda_f"], 3),
        "lambda_pf": round(output_data["lambda_pf"], 3),
        "lambda_rf": round(output_data["lambda_rf"], 3),
        "is_compact": output_data["is_compact"],
        "mp_knm": round(output_data["mp_knm"], 2),
        "mn_knm": round(output_data.get("mn_knm", output_data["phi_mn_knm"] / output_data["phi_factor"]), 2),
        "phi_factor": output_data["phi_factor"],
        "phi_mn_knm": round(output_data["phi_mn_knm"], 2),
        "capacity_ratio": round(output_data["capacity_ratio"], 4),
        # concrete-specific, set None for template
        "beta1": None, "rho_min": None, "rho_max": None, "rho_required": None,
        "as_required_mm2": None, "as_min_mm2": None, "as_design_mm2": None,
        "bar_area_mm2": None, "num_bars": None, "a_block_mm": None,
    }
    compact_str = "Ya (Kompak)" if output_data["is_compact"] else "Tidak (Tidak Kompak)"
    summary = {
        "loads": [
            {"label": "SW profil", "value": round(sw, 3), "unit": "kN/m", "highlight": False},
            {"label": "wu terfaktor", "value": round(wu, 3), "unit": "kN/m", "highlight": False},
            {"label": "Mu ultimit", "value": round(output_data["mu_ultimate_knm"], 2), "unit": "kN·m", "highlight": True},
        ],
        "capacity": [
            {"label": "Kompak?", "value": compact_str, "unit": "—", "highlight": False},
            {"label": "Mp plastis", "value": round(output_data["mp_knm"], 2), "unit": "kN·m", "highlight": False},
            {"label": "φMn kapasitas", "value": round(output_data["phi_mn_knm"], 2), "unit": "kN·m", "highlight": True},
            {"label": "Mu/φMn", "value": round(output_data["capacity_ratio"], 3), "unit": "—", "highlight": False},
        ],
    }
    return dict(material=material, geometry=geometry, loading=loading,
                combination=combination, forces=forces, capacity=capacity, summary=summary)


# ── Public API ────────────────────────────────────────────────────────────────

def render_report_html(
    *,
    calc_type: str,
    title: str,
    project: dict,
    input_data: dict,
    output_data: dict,
    standard_references: str,
    formula_version: str,
    generated_at: datetime,
    generated_by: str,
) -> str:
    """
    Render HTML laporan perhitungan dari data kalkulasi.
    Returns: HTML string yang siap ditampilkan di browser atau disimpan ke DB.
    """
    template = _env.get_template("report.html")

    if calc_type == "concrete_beam":
        ctx = _build_concrete_context(input_data, output_data)
    else:
        ctx = _build_steel_context(input_data, output_data)

    status = output_data.get("status", "TIDAK AMAN")
    # Normalize: dataclass serialization uses "TIDAK AMAN" string
    if status not in ("AMAN", "TIDAK AMAN"):
        status = "TIDAK AMAN"

    return template.render(
        calc_type=calc_type,
        title=title,
        project=project,
        standards=_parse_standards(standard_references),
        formula_version=formula_version,
        generated_at=generated_at.strftime("%d %B %Y, %H:%M"),
        generated_by=generated_by,
        status=status,
        **ctx,
    )
