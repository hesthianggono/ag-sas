"""
BAB 1 — Pendahuluan
====================
1.1 Latar Belakang
1.2 Maksud dan Tujuan
1.3 Ruang Lingkup Pekerjaan
1.4 Sistematika Laporan
"""
from __future__ import annotations

from typing import Any

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, h3, p, spacer, hr, note,
)


def build_s01(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 1, "PENDAHULUAN")

    # ── 1.1 Latar Belakang ────────────────────────────────────────────────
    story += h2(ctx, "Latar Belakang")
    project_name = config.project_name or "proyek yang bersangkutan"
    story.append(p(
        f"Laporan perhitungan struktur ini disusun dalam rangka perencanaan "
        f"dan analisis elemen struktur untuk <b>{project_name}</b>. "
        f"Perhitungan dilakukan menggunakan perangkat lunak AG Structural "
        f"Analysis Suite (AG-SAS) dengan mengacu pada standar nasional "
        f"Indonesia yang berlaku."
    ))
    story.append(p(
        "Analisis struktural mencakup pemodelan beban, penentuan gaya dalam, "
        "pemeriksaan kapasitas penampang, serta kontrol lendutan dan retak "
        "sesuai persyaratan yang ditetapkan."
    ))

    # ── 1.2 Maksud dan Tujuan ─────────────────────────────────────────────
    story += h2(ctx, "Maksud dan Tujuan")
    story.append(p(
        "Maksud disusunnya laporan ini adalah untuk mendokumentasikan seluruh "
        "tahapan analisis dan perencanaan elemen struktur secara sistematis "
        "dan terverifikasi."
    ))
    story.append(p("Tujuan laporan ini adalah:"))
    story.append(p(
        "a) Menyajikan data input, asumsi, dan parameter desain yang digunakan;<br/>"
        "b) Mendokumentasikan prosedur analisis dan hasil perhitungan;<br/>"
        "c) Membuktikan bahwa elemen struktur memenuhi persyaratan kekuatan "
        f"   ({config.sni_concrete}) dan kemampuan layan;<br/>"
        "d) Menyediakan acuan teknis untuk pelaksanaan konstruksi."
    ))

    # ── 1.3 Ruang Lingkup ─────────────────────────────────────────────────
    story += h2(ctx, "Ruang Lingkup Pekerjaan")
    calc_title = data.calc_title or "elemen struktur"
    calc_type_id = {
        "concrete_beam": "Balok Beton Bertulang",
        "steel_beam":    "Balok Baja Profil",
    }.get(data.calc_type, "Elemen Struktur")

    story.append(p(
        f"Ruang lingkup laporan ini mencakup analisis dan perencanaan "
        f"<b>{calc_type_id}</b> — <b>{calc_title}</b>, meliputi:"
    ))
    story.append(p(
        "a) Data proyek dan parameter desain;<br/>"
        "b) Spesifikasi material struktur;<br/>"
        "c) Analisis pembebanan (beban mati, beban hidup, kombinasi terfaktor);<br/>"
        "d) Pemodelan struktur dan analisis gaya dalam;<br/>"
        "e) Kontrol kekuatan lentur, geser, dan torsi;<br/>"
        "f) Kontrol lendutan dan retak (kemampuan layan);<br/>"
        "g) Gambar teknik hasil analisis."
    ))

    # ── 1.4 Sistematika Laporan ───────────────────────────────────────────
    story += h2(ctx, "Sistematika Laporan")
    story.append(p("Laporan ini disusun dengan sistematika sebagai berikut:"))
    story.append(p(
        "<b>Bab 1</b> — Pendahuluan: latar belakang, tujuan, ruang lingkup.<br/>"
        "<b>Bab 2</b> — Data Proyek: identitas proyek dan lokasi.<br/>"
        "<b>Bab 3</b> — Dasar Perencanaan: standar, kode, dan peraturan yang digunakan.<br/>"
        "<b>Bab 4</b> — Material: spesifikasi beton, baja tulangan, dan baja profil.<br/>"
        "<b>Bab 5</b> — Pembebanan: beban rencana dan kombinasi beban.<br/>"
        "<b>Bab 6</b> — Model Struktur: geometri dan kondisi batas.<br/>"
        "<b>Bab 7</b> — Analisis Struktur: gaya dalam (momen, geser, aksial).<br/>"
        "<b>Bab 8</b> — Perencanaan Penampang: kontrol kekuatan dan penulangan.<br/>"
        "<b>Bab 9</b> — Kemampuan Layan: lendutan dan kontrol retak.<br/>"
        "<b>Bab 10</b> — Ringkasan dan Kesimpulan.<br/>"
        "<b>Bab 11</b> — Gambar Teknik.<br/>"
        "<b>Lampiran</b> — Referensi tabel dan diagram tambahan."
    ))

    story.append(spacer(4))
    return story
