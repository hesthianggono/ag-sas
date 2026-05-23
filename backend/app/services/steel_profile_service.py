"""Seed data profil baja dan service lookup."""
from sqlmodel import Session, select
from app.models.steel_profile import SteelProfile


WF_PROFILES = [
    # designation, H, B, tw, tf, r, A(cm²), Ix(cm⁴), Iy(cm⁴), Sx(cm³), Sy(cm³), Zx(cm³), Zy(cm³), rx, ry, W(kg/m)
    ("WF 100x50x5x7",    100, 50,  5.0,  7.0, 8, 11.85, 187,    14.8,  37.5,  5.91,  43.2,  9.08, 3.97, 1.12, 9.30),
    ("WF 125x60x6x8",    125, 60,  6.0,  8.0, 8, 16.98, 413,    29.2,  66.1,  9.72,  75.0, 14.8,  4.93, 1.31, 13.3),
    ("WF 150x75x5x7",    150, 75,  5.0,  7.0, 8, 17.85, 666,    49.5,  88.8, 13.2,  101,  20.3,  6.11, 1.66, 14.0),
    ("WF 175x90x5x8",    175, 90,  5.0,  8.0, 8, 23.05, 1210,   97.5, 138,   21.7,  158,  33.4,  7.24, 2.06, 18.1),
    ("WF 200x100x5.5x8", 200,100,  5.5,  8.0, 11, 26.67, 1840, 134,   184,   26.7,  210,  41.1,  8.30, 2.24, 20.9),
    ("WF 250x125x6x9",   250,125,  6.0,  9.0, 12, 36.97, 4050,  294,  324,   47.0,  370,  72.5, 10.5,  2.82, 29.0),
    ("WF 300x150x6.5x9", 300,150,  6.5,  9.0, 13, 46.78, 7210,  508,  481,   67.7,  551, 104,  12.4,  3.29, 36.7),
    ("WF 350x175x7x11",  350,175,  7.0, 11.0, 13, 63.14,13600,  984,  775,  112,    886,  171,  14.7,  3.95, 49.6),
    ("WF 400x200x8x13",  400,200,  8.0, 13.0, 13, 84.12,23700, 1740, 1190,  174,   1350,  267,  16.8,  4.54, 66.0),
    ("WF 450x200x9x14",  450,200,  9.0, 14.0, 13, 96.76,33500, 1870, 1490,  187,   1690,  288,  18.6,  4.40, 76.0),
    ("WF 500x200x10x16", 500,200, 10.0, 16.0, 13,114.2, 47800, 2140, 1910,  214,   2180,  330,  20.5,  4.33, 89.7),
    ("WF 600x200x11x17", 600,200, 11.0, 17.0, 13,134.4, 75600, 2270, 2520,  227,   2900,  351,  23.7,  4.11,106.0),
]

H_BEAM_PROFILES = [
    ("H-Beam 100x100x6x8",   100,100, 6.0,  8.0, 10, 21.59,  383,  134,  76.5,  26.7,  86.4,  40.8, 4.21, 2.49, 16.9),
    ("H-Beam 150x150x7x10",  150,150, 7.0, 10.0, 11, 40.14, 1640,  563, 219,   75.1,  245,  114,   6.39, 3.75, 31.5),
    ("H-Beam 200x200x8x12",  200,200, 8.0, 12.0, 13, 63.53, 4720, 1600, 472,  160,    530,  243,   8.62, 5.02, 49.9),
    ("H-Beam 250x250x9x14",  250,250, 9.0, 14.0, 13, 91.43,10800, 3650, 867,  292,    975,  444,  10.9,  6.32, 71.8),
    ("H-Beam 300x300x10x15", 300,300,10.0, 15.0, 13,119.8, 20200, 6750,1350,  450,   1520,  686,  13.0,  7.51, 94.0),
    ("H-Beam 350x350x12x19", 350,350,12.0, 19.0, 13,173.9, 40300,13600,2300,  776,   2590, 1180,  15.2,  8.85,137.0),
    ("H-Beam 400x400x13x21", 400,400,13.0, 21.0, 13,218.7, 66600,22400,3330, 1120,   3760, 1700,  17.4, 10.1, 172.0),
]

CNP_PROFILES = [
    ("CNP 60x30x3",   60, 30, 3.0, 3.0, None, 2.69,  17.6,  1.36, 5.87, 0.91, None, None, 2.56, 0.71, 2.11),
    ("CNP 80x40x4",   80, 40, 4.0, 4.0, None, 4.89,  57.4,  5.11, 14.3, 2.56, None, None, 3.42, 1.02, 3.84),
    ("CNP 100x50x5", 100, 50, 5.0, 5.0, None, 7.69, 166,   17.4,  33.2, 6.95, None, None, 4.65, 1.50, 6.04),
    ("CNP 120x55x6", 120, 55, 6.0, 6.0, None,10.53, 365,   32.4,  60.8,11.8,  None, None, 5.89, 1.75, 8.27),
    ("CNP 150x65x6", 150, 65, 6.0, 6.0, None,13.05, 715,   63.1,  95.3,19.4,  None, None, 7.40, 2.20,10.24),
    ("CNP 200x75x8", 200, 75, 8.0, 8.0, None,22.29,2090,  136,   209,  36.2,  None, None, 9.69, 2.47,17.5),
]

UNP_PROFILES = [
    ("UNP 60x30x5",   60, 30, 5.0, 5.0, None, 5.42,  31.6,  2.52, 10.5, 1.68, None, None, 2.42, 0.68, 4.26),
    ("UNP 80x45x6",   80, 45, 6.0, 6.0, None, 8.64, 106,    9.72, 26.5, 4.32, None, None, 3.50, 1.06, 6.78),
    ("UNP 100x50x6", 100, 50, 6.0, 6.0, None,10.6,  206,   16.8,  41.2, 6.72, None, None, 4.41, 1.26, 8.34),
    ("UNP 120x55x7", 120, 55, 7.0, 7.0, None,14.2,  364,   30.9,  60.7,11.2,  None, None, 5.06, 1.48,11.1),
    ("UNP 140x60x7", 140, 60, 7.0, 7.0, None,16.4,  573,   45.9,  81.9,15.3,  None, None, 5.91, 1.67,12.9),
    ("UNP 160x65x8", 160, 65, 8.0, 8.0, None,21.0,  925,   72.8, 116,  22.4,  None, None, 6.64, 1.86,16.5),
    ("UNP 200x75x8", 200, 75, 8.0, 8.0, None,26.5, 1950,  148,   195,  39.4,  None, None, 8.58, 2.36,20.8),
    ("UNP 250x90x9", 250, 90, 9.0, 9.0, None,38.4, 4810,  378,   385,  84.1,  None, None,11.2,  3.14,30.1),
    ("UNP 300x100x10",300,100,10.0,10.0,None, 53.3,8030,  495,   536,  99.0,  None, None,12.3,  3.05,41.8),
]


def seed_steel_profiles(session: Session) -> None:
    existing = session.exec(select(SteelProfile).limit(1)).first()
    if existing:
        return

    for row in WF_PROFILES:
        _insert_profile(session, "WF", row)
    for row in H_BEAM_PROFILES:
        _insert_profile(session, "H-Beam", row)
    for row in CNP_PROFILES:
        _insert_profile(session, "CNP", row, no_zx=True)
    for row in UNP_PROFILES:
        _insert_profile(session, "UNP", row, no_zx=True)

    session.commit()
    print(f"Seeded {len(WF_PROFILES)+len(H_BEAM_PROFILES)+len(CNP_PROFILES)+len(UNP_PROFILES)} steel profiles.")


def _insert_profile(session, category, row, no_zx=False):
    designation, H, B, tw, tf, r, A, Ix, Iy, Sx, Sy, Zx, Zy, rx, ry, W = row
    profile = SteelProfile(
        category=category,
        designation=designation,
        height_h=float(H), flange_width_b=float(B),
        web_thickness_tw=float(tw), flange_thickness_tf=float(tf),
        fillet_r=float(r) if r else None,
        area_a=float(A), ix=float(Ix), iy=float(Iy),
        sx=float(Sx), sy=float(Sy),
        zx=float(Zx) if Zx else float(Sx) * 1.12,
        zy=float(Zy) if Zy else float(Sy) * 1.12,
        rx=float(rx), ry=float(ry),
        weight_per_m=float(W),
    )
    session.add(profile)
