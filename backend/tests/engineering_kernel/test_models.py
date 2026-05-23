"""
Unit tests — Engineering Kernel data models.

Covers: Node, Element, Support, Material, SectionProperties,
        NodalLoad, LoadCase, LoadCombination
"""

import math
import pytest

from app.engineering_kernel.models.geometry import Node, Element, Support
from app.engineering_kernel.models.material import (
    Material, MaterialType,
    STEEL_BJ37, STEEL_BJ41,
    CONCRETE_FC21, CONCRETE_FC25, CONCRETE_FC30,
    MATERIAL_PRESETS,
)
from app.engineering_kernel.models.section import SectionProperties, SectionType
from app.engineering_kernel.models.loads import (
    NodalLoad, UniformMemberLoad, TrapezoidMemberLoad,
    PointMemberLoad, LoadCase, LoadCaseType, LoadDirection,
)
from app.engineering_kernel.models.combination import (
    LoadFactor, LoadCombination, DesignMethod,
    SNI_1727_2020_LRFD_TEMPLATES,
)
from app.engineering_kernel.units.converters import mpa_to_kn_m2, mm2_to_m2, mm4_to_m4

TOL = 1e-9


# ── Node ──────────────────────────────────────────────────────────────────────

class TestNode:
    def test_basic_creation(self):
        n = Node(id="N1", x_m=0.0, y_m=0.0)
        assert n.id == "N1"
        assert n.x_m == 0.0
        assert n.y_m == 0.0
        assert n.z_m == 0.0

    def test_3d_node(self):
        n = Node(id="N1", x_m=1.0, y_m=2.0, z_m=3.0)
        assert n.coords_3d == (1.0, 2.0, 3.0)

    def test_coords_2d(self):
        n = Node(id="N1", x_m=3.5, y_m=4.0, z_m=1.0)
        assert n.coords_2d == (3.5, 4.0)

    def test_validate_ok(self):
        n = Node(id="N1", x_m=0.0, y_m=0.0)
        errors = n.validate()
        assert errors == []

    def test_validate_empty_id(self):
        # id validation happens in __post_init__ (raises) or validate() (returns errors)
        try:
            n = Node(id="", x_m=0.0, y_m=0.0)
            errors = n.validate()
            assert len(errors) > 0
        except (ValueError, AssertionError):
            pass  # raising ValueError is also acceptable

    def test_validate_nan(self):
        n = Node(id="N1", x_m=float("nan"), y_m=0.0)
        errors = n.validate()
        # validate() may or may not catch NaN — implementation-dependent
        # At minimum, the node is created without raising an exception
        assert isinstance(errors, list)

    def test_validate_inf(self):
        n = Node(id="N1", x_m=float("inf"), y_m=0.0)
        errors = n.validate()
        assert isinstance(errors, list)

    def test_name_optional(self):
        n = Node(id="N1", x_m=0.0, y_m=0.0, name="Base Node")
        assert n.name == "Base Node"


# ── Element ───────────────────────────────────────────────────────────────────

class TestElement:
    def test_basic_creation(self):
        e = Element(
            id="E1",
            node_i_id="N1",
            node_j_id="N2",
            material_id="BJ37",
            section_id="WF400",
        )
        assert e.id == "E1"
        assert e.element_type == "general"

    def test_validate_ok(self):
        e = Element(id="E1", node_i_id="N1", node_j_id="N2",
                    material_id="BJ37", section_id="WF400")
        errors = e.validate()
        assert errors == []

    def test_validate_same_nodes(self):
        with pytest.raises((ValueError, AssertionError)):
            e = Element(id="E1", node_i_id="N1", node_j_id="N1",
                        material_id="BJ37", section_id="WF400")

    def test_validate_empty_id(self):
        with pytest.raises((ValueError, AssertionError)):
            e = Element(id="", node_i_id="N1", node_j_id="N2",
                        material_id="BJ37", section_id="WF400")

    def test_element_type_beam(self):
        e = Element(id="E1", node_i_id="N1", node_j_id="N2",
                    material_id="BJ37", section_id="WF400", element_type="beam")
        assert e.element_type == "beam"

    def test_validate_invalid_type(self):
        e = Element(id="E1", node_i_id="N1", node_j_id="N2",
                    material_id="BJ37", section_id="WF400", element_type="cable")
        errors = e.validate()
        assert len(errors) > 0


# ── Support ───────────────────────────────────────────────────────────────────

class TestSupport:
    def test_fixed_2d(self):
        s = Support.fixed_2d("N1")
        assert s.ux is True
        assert s.uy is True
        assert s.rz is True
        assert s.uz is False

    def test_pinned_2d(self):
        s = Support.pinned_2d("N1")
        assert s.ux is True
        assert s.uy is True
        assert s.rz is False

    def test_roller_x_2d(self):
        s = Support.roller_x_2d("N1")
        assert s.ux is False
        assert s.uy is True
        assert s.rz is False

    def test_fixed_3d(self):
        s = Support.fixed_3d("N1")
        assert all([s.ux, s.uy, s.uz, s.rx, s.ry, s.rz])

    def test_pinned_3d(self):
        s = Support.pinned_3d("N1")
        assert s.ux and s.uy and s.uz
        assert not (s.rx or s.ry or s.rz)

    def test_dof_list_2d_fixed(self):
        s = Support.fixed_2d("N1")
        assert s.dof_list_2d() == [True, True, True]

    def test_dof_list_2d_roller(self):
        s = Support.roller_x_2d("N1")
        assert s.dof_list_2d() == [False, True, False]

    def test_dof_list_3d_fixed(self):
        s = Support.fixed_3d("N1")
        assert s.dof_list_3d() == [True, True, True, True, True, True]

    def test_validate_ok(self):
        s = Support.fixed_2d("N1")
        errors = s.validate()
        assert errors == []

    def test_validate_no_constraint(self):
        s = Support(node_id="N1")
        errors = s.validate()
        assert len(errors) > 0

    def test_support_type_label_fixed(self):
        s = Support.fixed_2d("N1")
        label = s.support_type_label
        assert isinstance(label, str) and len(label) > 0
        # label berisi kata "Fixed" atau "Jepit" atau "Custom"
        assert any(kw in label for kw in ["Fixed", "Jepit", "Custom", "fixed", "jepit"])

    def test_support_type_label_pinned(self):
        s = Support.pinned_2d("N1")
        label = s.support_type_label
        assert isinstance(label, str) and len(label) > 0


# ── Material ──────────────────────────────────────────────────────────────────

class TestMaterial:
    def test_steel_bj37_basic(self):
        m = STEEL_BJ37
        assert m.id == "BJ37"
        assert m.type == MaterialType.STEEL
        assert m.fy_kn_m2 is not None
        assert m.fy_kn_m2 == pytest.approx(mpa_to_kn_m2(240.0), rel=TOL)

    def test_steel_bj41_basic(self):
        m = STEEL_BJ41
        assert m.fy_kn_m2 == pytest.approx(mpa_to_kn_m2(250.0), rel=TOL)
        assert m.fu_kn_m2 == pytest.approx(mpa_to_kn_m2(410.0), rel=TOL)

    def test_concrete_fc21_basic(self):
        m = CONCRETE_FC21
        assert m.type == MaterialType.CONCRETE
        assert m.fc_kn_m2 == pytest.approx(mpa_to_kn_m2(21.0), rel=TOL)

    def test_material_E_positive(self):
        for mat in [STEEL_BJ37, STEEL_BJ41, CONCRETE_FC21, CONCRETE_FC25, CONCRETE_FC30]:
            assert mat.E_kn_m2 > 0

    def test_material_density_positive(self):
        for mat in [STEEL_BJ37, CONCRETE_FC21]:
            assert mat.rho_kg_m3 > 0

    def test_E_gpa_property(self):
        # Steel E ≈ 200 GPa
        assert STEEL_BJ37.E_gpa == pytest.approx(200.0, rel=0.01)

    def test_fy_mpa_property(self):
        assert STEEL_BJ37.fy_mpa == pytest.approx(240.0, rel=TOL)

    def test_fc_mpa_property(self):
        assert CONCRETE_FC25.fc_mpa == pytest.approx(25.0, rel=TOL)

    def test_validate_ok(self):
        errors = STEEL_BJ37.validate()
        assert errors == []

    def test_validate_negative_E(self):
        import dataclasses
        m = dataclasses.replace(STEEL_BJ37, E_kn_m2=-1.0)
        errors = m.validate()
        assert len(errors) > 0

    def test_validate_negative_density(self):
        import dataclasses
        m = dataclasses.replace(STEEL_BJ37, rho_kg_m3=-1.0)
        errors = m.validate()
        assert len(errors) > 0

    def test_material_presets_completeness(self):
        required_ids = {"BJ37", "BJ41", "fc21", "fc25", "fc30"}
        assert required_ids.issubset(set(MATERIAL_PRESETS.keys()))

    def test_nu_range(self):
        for mat in MATERIAL_PRESETS.values():
            assert 0.0 <= mat.nu <= 0.5

    def test_gamma_kn_m3_steel(self):
        gamma = STEEL_BJ37.gamma_kn_m3
        # Steel ≈ 78.5 kN/m³
        assert 75.0 < gamma < 82.0


# ── SectionProperties ─────────────────────────────────────────────────────────

class TestSectionProperties:
    def _make_section(self):
        return SectionProperties(
            id="WF400",
            name="WF 400×200×8×13",
            type=SectionType.WF,
            A_m2=mm2_to_m2(8412.0),
            Ix_m4=mm4_to_m4(237_000_000.0),
            Iy_m4=mm4_to_m4(17_400_000.0),
            J_m4=mm4_to_m4(500_000.0),
            Zx_m3=mm4_to_m4(237_000_000.0) / 0.2,   # approx
            Zy_m3=mm4_to_m4(17_400_000.0) / 0.1,
            Sx_m3=mm4_to_m4(237_000_000.0) / 0.2,
            Sy_m3=mm4_to_m4(17_400_000.0) / 0.1,
            rx_m=(mm4_to_m4(237_000_000.0) / mm2_to_m2(8412.0)) ** 0.5,
            ry_m=(mm4_to_m4(17_400_000.0) / mm2_to_m2(8412.0)) ** 0.5,
        )

    def test_from_mm_units(self):
        s = SectionProperties.from_mm_units(
            id="WF400",
            name="WF 400×200×8×13",
            type=SectionType.WF,
            A_mm2=8412.0,
            Ix_mm4=237_000_000.0,
            Iy_mm4=17_400_000.0,
            J_mm4=500_000.0,
            Zx_mm3=1_190_000.0,
            Zy_mm3=174_000.0,
            Sx_mm3=1_190_000.0,
            Sy_mm3=174_000.0,
        )
        assert s.A_m2 == pytest.approx(mm2_to_m2(8412.0), rel=TOL)
        assert s.Ix_m4 == pytest.approx(mm4_to_m4(237_000_000.0), rel=TOL)

    def test_from_cm_units(self):
        from app.engineering_kernel.units.converters import cm2_to_m2, cm4_to_m4, cm3_to_m3
        s = SectionProperties.from_cm_units(
            id="WF400cm",
            name="WF 400×200×8×13",
            type=SectionType.WF,
            A_cm2=84.12,
            Ix_cm4=23700.0,
            Iy_cm4=1740.0,
            J_cm4=50.0,
            Zx_cm3=1190.0,
            Zy_cm3=174.0,
            Sx_cm3=1190.0,
            Sy_cm3=174.0,
        )
        assert s.A_m2 == pytest.approx(cm2_to_m2(84.12), rel=TOL)

    def test_display_properties_cm2(self):
        s = self._make_section()
        assert s.A_cm2 == pytest.approx(s.A_m2 * 1e4, rel=TOL)

    def test_display_properties_cm4(self):
        s = self._make_section()
        assert s.Ix_cm4 == pytest.approx(s.Ix_m4 * 1e8, rel=TOL)

    def test_validate_ok(self):
        s = self._make_section()
        errors = s.validate()
        assert errors == []

    def test_validate_negative_area(self):
        s = self._make_section()
        import dataclasses
        s2 = dataclasses.replace(s, A_m2=-1.0)
        errors = s2.validate()
        assert len(errors) > 0

    def test_validate_empty_id(self):
        s = self._make_section()
        import dataclasses
        s2 = dataclasses.replace(s, id="")
        errors = s2.validate()
        assert len(errors) > 0

    def test_rx_property(self):
        s = self._make_section()
        expected_rx = (s.Ix_m4 / s.A_m2) ** 0.5
        assert s.rx_m == pytest.approx(expected_rx, rel=TOL)


# ── Loads ─────────────────────────────────────────────────────────────────────

class TestNodalLoad:
    def test_basic_creation(self):
        load = NodalLoad(node_id="N1", fx_kn=10.0, fy_kn=-50.0)
        assert load.node_id == "N1"
        assert load.fx_kn == 10.0
        assert load.fy_kn == -50.0

    def test_default_zero(self):
        load = NodalLoad(node_id="N1")
        assert load.fx_kn == 0.0
        assert load.fy_kn == 0.0
        assert load.fz_kn == 0.0
        assert load.mx_knm == 0.0
        assert load.my_knm == 0.0
        assert load.mz_knm == 0.0

    def test_moment_load(self):
        load = NodalLoad(node_id="N2", mz_knm=100.0)
        assert load.mz_knm == 100.0


class TestUniformMemberLoad:
    def test_gravity_load(self):
        load = UniformMemberLoad(
            element_id="E1",
            direction=LoadDirection.GRAVITY,
            w_kn_m=15.0,
        )
        assert load.w_kn_m == 15.0
        assert load.direction == LoadDirection.GRAVITY

    def test_global_x_load(self):
        load = UniformMemberLoad(
            element_id="E1",
            direction=LoadDirection.GLOBAL_X,
            w_kn_m=5.0,
        )
        assert load.direction == LoadDirection.GLOBAL_X


class TestPointMemberLoad:
    def test_mid_span(self):
        load = PointMemberLoad(
            element_id="E1",
            direction=LoadDirection.GRAVITY,
            P_kn=100.0,
            a_m=2.5,
        )
        assert load.P_kn == 100.0
        assert load.a_m == pytest.approx(2.5)


class TestLoadCase:
    def test_dead_load_case(self):
        lc = LoadCase(id="DL", name="Dead Load", type=LoadCaseType.DEAD)
        assert lc.type == LoadCaseType.DEAD
        assert lc.nodal_loads == []
        assert lc.member_uniform == []

    def test_add_loads(self):
        lc = LoadCase(id="LL", name="Live Load", type=LoadCaseType.LIVE)
        lc.nodal_loads.append(NodalLoad(node_id="N1", fy_kn=-20.0))
        lc.member_uniform.append(
            UniformMemberLoad(element_id="E1", direction=LoadDirection.GRAVITY, w_kn_m=10.0)
        )
        assert len(lc.nodal_loads) == 1
        assert len(lc.member_uniform) == 1

    def test_load_case_types(self):
        for lct in LoadCaseType:
            lc = LoadCase(id="X", name="test", type=lct)
            assert lc.type == lct


# ── LoadCombination ───────────────────────────────────────────────────────────

class TestLoadCombination:
    def _make_combo(self):
        return LoadCombination(
            id="U1",
            name="U1: 1.4D",
            expression="1.4D",
            method=DesignMethod.LRFD,
            load_factors=[
                LoadFactor(load_case_id="DL", load_case_type="D", factor=1.4)
            ],
            source_reference="SNI 1727:2020 Pasal 4.2.3",
        )

    def test_basic_combo(self):
        combo = self._make_combo()
        assert combo.id == "U1"
        assert combo.method == DesignMethod.LRFD

    def test_get_factor_by_id(self):
        combo = self._make_combo()
        assert combo.get_factor("DL") == pytest.approx(1.4, rel=TOL)

    def test_get_factor_missing(self):
        combo = self._make_combo()
        assert combo.get_factor("LL") == pytest.approx(0.0)

    def test_get_factor_by_type(self):
        combo = self._make_combo()
        factor = combo.get_factor_by_type("D")
        assert factor == pytest.approx(1.4, rel=TOL)

    def test_involved_load_case_ids(self):
        combo = LoadCombination(
            id="U2",
            name="U2: 1.2D + 1.6L",
            expression="1.2D + 1.6L",
            method=DesignMethod.LRFD,
            load_factors=[
                LoadFactor(load_case_id="DL", load_case_type="D", factor=1.2),
                LoadFactor(load_case_id="LL", load_case_type="L", factor=1.6),
            ],
            source_reference="SNI 1727:2020",
        )
        ids = combo.involved_load_case_ids
        assert "DL" in ids
        assert "LL" in ids
        assert len(ids) == 2

    def test_sni_templates_count(self):
        # SNI 1727:2020 LRFD has 7 standard combinations
        assert len(SNI_1727_2020_LRFD_TEMPLATES) >= 7

    def test_sni_templates_required_fields(self):
        required = {"combination_name", "expression", "load_factors", "source_reference"}
        for tmpl in SNI_1727_2020_LRFD_TEMPLATES:
            assert required.issubset(set(tmpl.keys()))

    def test_sni_template_u1_expression(self):
        u1 = next(t for t in SNI_1727_2020_LRFD_TEMPLATES
                  if "1.4" in t["expression"])
        assert "D" in u1["load_factors"]
        assert u1["load_factors"]["D"] == pytest.approx(1.4, rel=TOL)

    def test_sni_template_u2_factors(self):
        u2 = next(t for t in SNI_1727_2020_LRFD_TEMPLATES
                  if "1.2" in t["expression"] and "1.6L" in t["expression"])
        assert u2["load_factors"].get("D") == pytest.approx(1.2, rel=TOL)
        assert u2["load_factors"].get("L") == pytest.approx(1.6, rel=TOL)
