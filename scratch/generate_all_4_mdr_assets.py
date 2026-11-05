import fitz
import json
import math
import os
from PIL import Image, ImageOps, ImageFilter

PROJ_DIR = "/Users/dianjulie/Documents/Map Project"
SCRATCH_DIR = os.path.join(PROJ_DIR, "scratch")
PDF_PATH = os.path.join(PROJ_DIR, "SHIP PLAN OVERVIEW BOOKLET.pdf")

os.makedirs(SCRATCH_DIR, exist_ok=True)

doc = fitz.open(PDF_PATH)
page = doc[4]  # Page 5 contains Deck 5, Deck 6, and Deck 7 vector columns
drawings = page.get_drawings()

Y_MID = 464.885  # Shared longitudinal midpoint for all decks (Stern=-33.67m .. Bow=+33.67m)


def sample_bezier(p0, p1, p2, p3, n=20):
    pts = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1.0 - t
        x = (mt**3) * p0.x + 3 * (mt**2) * t * p1.x + 3 * mt * (t**2) * p2.x + (t**3) * p3.x
        y = (mt**3) * p0.y + 3 * (mt**2) * t * p1.y + 3 * mt * (t**2) * p2.y + (t**3) * p3.y
        pts.append((x, y))
    return pts


def extract_subpaths_xy(d, n_bez=20):
    subpaths = []
    curr = []
    for item in d["items"]:
        op = item[0]
        if op == "l":
            p1, p2 = (item[1].x, item[1].y), (item[2].x, item[2].y)
            if not curr or (p1[0] - curr[-1][0])**2 + (p1[1] - curr[-1][1])**2 > 1e-2:
                if curr:
                    subpaths.append(curr)
                curr = [p1, p2]
            else:
                curr.append(p2)
        elif op == "c":
            p0 = (item[1].x, item[1].y)
            bpts = sample_bezier(item[1], item[2], item[3], item[4], n=n_bez)
            if not curr or (p0[0] - curr[-1][0])**2 + (p0[1] - curr[-1][1])**2 > 1e-2:
                if curr:
                    subpaths.append(curr)
                curr = [p0] + bpts
            else:
                curr.extend(bpts)
        elif op == "re":
            r = item[1]
            if curr:
                subpaths.append(curr)
                curr = []
            subpaths.append([
                (r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)
            ])
    if curr:
        subpaths.append(curr)
    return subpaths


def dedup_pts(pts, tol=0.08):
    if not pts:
        return []
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= tol:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < tol:
        out.pop()
    return out


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def draw_pdf_item_to_shape(shape, d, clip, fill_col, stroke_col, width_mult=1.45):
    for item in d["items"]:
        op = item[0]
        if op == "l":
            p1 = fitz.Point(item[1].x - clip.x0, item[1].y - clip.y0)
            p2 = fitz.Point(item[2].x - clip.x0, item[2].y - clip.y0)
            shape.draw_line(p1, p2)
        elif op == "c":
            p1 = fitz.Point(item[1].x - clip.x0, item[1].y - clip.y0)
            p2 = fitz.Point(item[2].x - clip.x0, item[2].y - clip.y0)
            p3 = fitz.Point(item[3].x - clip.x0, item[3].y - clip.y0)
            p4 = fitz.Point(item[4].x - clip.x0, item[4].y - clip.y0)
            shape.draw_bezier(p1, p2, p3, p4)
        elif op == "re":
            r = item[1]
            nr = fitz.Rect(r.x0 - clip.x0, r.y0 - clip.y0, r.x1 - clip.x0, r.y1 - clip.y0)
            shape.draw_rect(nr)
    w = (d.get("width") or 0.22) * width_mult
    shape.finish(fill=fill_col, color=stroke_col, width=w, even_odd=d.get("even_odd", False))


# ==============================================================================
# 1. EXACT CLEAN POLYGONS OF ALL 4 MAIN DINING ROOMS (MDRs)
# ==============================================================================
# 1A. La Colombina — Deck 5 (#422)
d422 = drawings[422]["items"]
colombina_clean_poly = dedup_pts(
    [(192.37, 733.82), (192.37, 721.46)]
    + sample_bezier(d422[9][1], d422[9][2], d422[9][3], d422[9][4], 4)
    + sample_bezier(d422[10][1], d422[10][2], d422[10][3], d422[10][4], 4)
    + sample_bezier(d422[11][1], d422[11][2], d422[11][3], d422[11][4], 4)
    + [
        (171.68, 718.38),
        (171.68, 720.37),
        (163.37, 720.37),
        (163.37, 718.38),
        (144.98, 718.15),
    ]
    + sample_bezier(d422[40][1], d422[40][2], d422[40][3], d422[40][4], 4)
    + sample_bezier(d422[41][1], d422[41][2], d422[41][3], d422[41][4], 4)
    + [
        (142.71, 733.96),
        (126.27, 733.96),
        (126.28, 788.46),
    ]
    + sample_bezier(d422[60][1], d422[60][2], d422[60][3], d422[60][4], 8)
    + sample_bezier(d422[61][1], d422[61][2], d422[61][3], d422[61][4], 8)
    + sample_bezier(d422[62][1], d422[62][2], d422[62][3], d422[62][4], 8)
    + sample_bezier(d422[63][1], d422[63][2], d422[63][3], d422[63][4], 12)
    + sample_bezier(d422[64][1], d422[64][2], d422[64][3], d422[64][4], 12)
    + sample_bezier(d422[65][1], d422[65][2], d422[65][3], d422[65][4], 12)
    + [(208.74, 733.82)],
    tol=0.90
)

# 1B. Il Meneghino — Deck 6 (#307)
d307 = drawings[307]["items"]
meneghino_clean_poly = dedup_pts(
    [
        (255.46, 707.35),
        (255.46, 717.39),
        (259.97, 717.39),
        (259.97, 733.65),
        (245.11, 733.70),
        (245.16, 763.92),
        (255.21, 763.92),
        (255.21, 780.01),
        (244.72, 780.01),
        (244.65, 786.96),
    ]
    + sample_bezier(d307[27][1], d307[27][2], d307[27][3], d307[27][4], 8)
    + sample_bezier(d307[28][1], d307[28][2], d307[28][3], d307[28][4], 5)
    + sample_bezier(d307[29][1], d307[29][2], d307[29][3], d307[29][4], 6)
    + sample_bezier(d307[30][1], d307[30][2], d307[30][3], d307[30][4], 8)
    + sample_bezier(d307[31][1], d307[31][2], d307[31][3], d307[31][4], 12)
    + sample_bezier(d307[32][1], d307[32][2], d307[32][3], d307[32][4], 12)
    + sample_bezier(d307[33][1], d307[33][2], d307[33][3], d307[33][4], 6)
    + sample_bezier(d307[34][1], d307[34][2], d307[34][3], d307[34][4], 8)
    + sample_bezier(d307[35][1], d307[35][2], d307[35][3], d307[35][4], 6)
    + [
        (327.89, 780.01),
        (317.38, 780.01),
        (317.38, 763.92),
        (327.54, 763.97),
        (327.48, 733.59),
        (309.31, 733.54),
        (309.31, 714.31),
        (312.10, 714.31),
        (312.06, 717.68),
        (325.61, 717.68),
        (325.61, 707.35),
        (297.18, 707.35),
        (297.18, 721.25),
        (291.30, 721.25),
        (291.30, 707.35),
        (281.30, 707.35),
        (281.30, 721.34),
        (275.41, 721.34),
        (275.41, 707.35),
    ],
    tol=0.90
)

# 1C. Arlecchino — Deck 6 (#308)
arlecchino_clean_poly = [
    (315.55, 551.63),
    (313.47, 551.63),
    (313.47, 549.00),
    (296.02, 549.00),
    (296.02, 556.93),
    (276.62, 556.93),
    (276.62, 537.92),
    (277.23, 537.92),
    (277.23, 509.55),
    (243.96, 509.55),
    (243.96, 647.48),
    (277.23, 647.48),
    (277.23, 613.63),
    (276.62, 613.63),
    (276.62, 571.77),
    (295.98, 571.77),
    (295.98, 592.71),
    (298.96, 592.71),
    (298.96, 585.90),
    (315.55, 585.90),
]

# 1D. Il Rugantino — Deck 7 (#135)
rugantino_clean_poly = [
    (381.16, 777.43),
    (394.15, 777.43),
    (397.80, 772.29),
    (406.30, 772.29),
    (406.30, 773.42),
    (419.34, 773.42),
    (419.40, 772.29),
    (427.85, 772.29),
    (431.48, 777.43),
    (444.47, 777.43),
    (451.35, 772.29),
    (451.32, 762.03),
    (448.34, 756.88),
    (448.34, 732.86),
    (443.82, 732.86),
    (443.82, 725.04),
    (438.94, 725.04),
    (438.94, 708.06),
    (433.54, 708.06),
    (433.54, 705.50),
    (422.40, 705.50),
    (422.35, 711.87),
    (418.63, 711.87),
    (418.58, 726.16),
    (415.52, 726.16),
    (415.54, 710.63),
    (410.15, 710.63),
    (410.10, 726.16),
    (407.09, 726.16),
    (407.01, 711.77),
    (403.38, 711.74),
    (403.38, 705.50),
    (386.32, 705.50),
    (386.32, 731.19),
    (377.35, 731.19),
    (377.35, 756.88),
    (374.26, 762.01),
    (374.24, 772.29),
]


# ==============================================================================
# 2. HULL LOOPS, LIFEBOATS & WALLS FOR DECK 5, DECK 6, AND DECK 7
# ==============================================================================
# --- DECK 5 ("TAORMINA") ---
CLIP_D5 = fitz.Rect(118.0, 122.0, 217.0, 808.0)
X_CENTER_D5 = 167.515
s423 = extract_subpaths_xy(drawings[423], n_bez=24)
hull_loop_d5 = dedup_pts(s423[41], tol=0.08)

zone_polys_d5 = {}
for idx in range(376, 422):
    sps = extract_subpaths_xy(drawings[idx], n_bez=12)
    if sps:
        zone_polys_d5[f"CabinBlock_{idx}"] = dedup_pts(max(sps, key=len), tol=0.10)

walls_d5 = []
for w_idx in range(423, 432):
    sps = extract_subpaths_xy(drawings[w_idx], n_bez=12)
    for sp_i, sp in enumerate(sps):
        if w_idx == 423 and sp_i == 41:
            continue  # Outer hull loop already used for bulwark wall
        pts_clean = dedup_pts(sp, tol=0.15)
        if len(pts_clean) < 2:
            continue
        tlen = sum(math.hypot(pts_clean[k+1][0]-pts_clean[k][0], pts_clean[k+1][1]-pts_clean[k][1]) for k in range(len(pts_clean)-1))
        if tlen < 3.0:
            continue
        if any(point_in_poly(px, py, colombina_clean_poly) for px, py in pts_clean):
            continue
        walls_d5.append(pts_clean)

elevators_d5 = [
    (158.4, 341.8, 162.7, 364.2),
    (172.0, 341.8, 176.3, 364.2),
    (158.4, 509.8, 162.7, 531.6),
    (172.0, 509.8, 176.3, 531.6),
    (158.2, 675.8, 162.5, 692.4),
    (171.8, 675.8, 176.1, 692.4),
]

# --- DECK 6 ("MATERA / ROMA") ---
CLIP_D6 = fitz.Rect(225.0, 122.0, 347.6, 808.0)
X_CENTER_D6 = 286.300
s329 = extract_subpaths_xy(drawings[329], n_bez=24)
s371_all = extract_subpaths_xy(drawings[371], n_bez=24)
colosseo_port_d6 = None
colosseo_stbd_d6 = None
for sp in s371_all:
    xs = [p[0] for p in sp]
    ys = [p[1] for p in sp]
    if len(sp) > 50 and abs(min(ys) - 427.1) < 1.0 and abs(max(ys) - 488.5) < 1.0:
        if min(xs) < 240.0 and max(xs) < 245.0:
            colosseo_port_d6 = sp
        elif max(xs) > 332.0 and min(xs) > 327.0:
            colosseo_stbd_d6 = sp

hull_loop_d6 = dedup_pts(
    s329[147]
    + list(reversed(colosseo_port_d6))
    + s329[150]
    + list(reversed(s329[151]))
    + colosseo_stbd_d6
    + list(reversed(s329[148])),
    tol=0.08
)

s342 = extract_subpaths_xy(drawings[342], n_bez=12)
lifeboats_d6 = []
for sp in s342:
    xs = [p[0] for p in sp]
    ys = [p[1] for p in sp]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    if 10.0 < w < 15.0 and 25.0 < h < 32.0 and (max(xs) < 245.0 or min(xs) > 328.0):
        lifeboats_d6.append(dedup_pts(sp, tol=0.12))

elevators_d6 = [
    (277.2, 341.8, 281.5, 364.2),
    (290.8, 341.8, 295.1, 364.2),
    (277.2, 509.8, 281.5, 531.6),
    (290.8, 509.8, 295.1, 531.6),
    (277.0, 675.8, 281.3, 692.4),
    (290.6, 675.8, 294.9, 692.4),
]

# --- DECK 7 ("POSITANO") ---
CLIP_D7 = fitz.Rect(351.5, 122.0, 474.1, 808.0)
X_CENTER_D7 = 412.810
s161 = extract_subpaths_xy(drawings[161], n_bez=24)
hull_loop_d7 = dedup_pts(
    list(reversed(s161[19]))
    + list(reversed(s161[34]))
    + list(reversed(s161[43]))
    + [(363.64, 726.05)]
    + [p for p in reversed(s161[18]) if p[1] >= 726.0]
    + s161[41]
    + [(461.99, 726.05)]
    + s161[44]
    + s161[35]
    + s161[45],
    tol=0.08
)
colosseo_port_d7 = dedup_pts(list(reversed(s161[34])), tol=0.08)
colosseo_stbd_d7 = dedup_pts(s161[35], tol=0.08)

s305 = extract_subpaths_xy(drawings[305], n_bez=12)
lifeboats_d7 = []
for sp in s305:
    xs = [p[0] for p in sp]
    ys = [p[1] for p in sp]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    if 10.0 < w < 15.0 and 25.0 < h < 32.0 and (max(xs) < 372.0 or min(xs) > 453.0):
        lifeboats_d7.append(dedup_pts(sp, tol=0.12))

zone_polys_d7 = {}
for z_idx, z_name in [
    (132, "Lungomare_Port"),
    (133, "Lungomare_Stbd"),
    (134, "Terrazza_Superba"),
    (136, "Sunset_Bar"),
    (137, "Piazza_di_Spagna"),
    (138, "Galleria_Shops_Aft"),
    (139, "Galleria_Shops_Mid"),
    (140, "Galleria_Shops_Fwd1"),
    (142, "Galleria_Shops_Fwd2"),
    (145, "CoDe_Museum"),
    (146, "Colosseo_Balcony"),
    (147, "Colosseo_Atrium"),
    (148, "Laguna_Casino"),
    (150, "Campari_Bar"),
    (152, "Sanremo_Theatre_Balcony"),
    (157, "Bellavista_Restaurant"),
]:
    sps = extract_subpaths_xy(drawings[z_idx], n_bez=16)
    if sps:
        zone_polys_d7[z_name] = dedup_pts(max(sps, key=len), tol=0.10)

walls_d7 = []
for w_idx in range(160, 185):
    sps = extract_subpaths_xy(drawings[w_idx], n_bez=12)
    for sp_i, sp in enumerate(sps):
        if w_idx == 161 and sp_i in (18, 19, 34, 35, 41, 43, 44, 45):
            continue
        pts_clean = dedup_pts(sp, tol=0.15)
        if len(pts_clean) < 2:
            continue
        tlen = sum(math.hypot(pts_clean[k+1][0]-pts_clean[k][0], pts_clean[k+1][1]-pts_clean[k][1]) for k in range(len(pts_clean)-1))
        if tlen < 3.5:
            continue
        if any(point_in_poly(px, py, rugantino_clean_poly) for px, py in pts_clean):
            continue
        walls_d7.append(pts_clean)

elevators_d7 = [
    (403.7, 341.8, 408.0, 364.2),
    (417.3, 341.8, 421.6, 364.2),
    (403.7, 509.8, 408.0, 531.6),
    (417.3, 509.8, 421.6, 531.6),
    (403.5, 675.8, 407.8, 692.4),
    (417.1, 675.8, 421.4, 692.4),
]


# ==============================================================================
# 3. RENDER 8K MONOCHROME TEXTURES & BUMP MAPS FOR ALL 4 MDR CONFIGS
# ==============================================================================
def save_monochrome_textures(out_prefix, out_page):
    pix = out_page.get_pixmap(dpi=800)
    tex_path = os.path.join(SCRATCH_DIR, f"{out_prefix}_monochrome_plan_8k.png")
    pix.save(tex_path)
    im_color = Image.open(tex_path).convert("L")
    im_bump = ImageOps.autocontrast(im_color)
    im_bump = im_bump.filter(ImageFilter.GaussianBlur(radius=0.8))
    bump_path = os.path.join(SCRATCH_DIR, f"{out_prefix}_monochrome_bump_8k.png")
    im_bump.save(bump_path)
    print(f"Saved {out_prefix} 8K plan & bump ({pix.width}x{pix.height})")
    return tex_path, bump_path


# --- 3A. Render Deck 5 (La Colombina) Texture ---
def generate_deck5_colombina():
    out_doc = fitz.open()
    out_page = out_doc.new_page(width=CLIP_D5.width, height=CLIP_D5.height)
    shape = out_page.new_shape()

    shape.draw_rect(fitz.Rect(0, 0, CLIP_D5.width, CLIP_D5.height))
    shape.finish(fill=(0.10, 0.11, 0.13), color=None)

    hull_pts = [fitz.Point(x - CLIP_D5.x0, y - CLIP_D5.y0) for x, y in hull_loop_d5]
    for i in range(len(hull_pts)):
        shape.draw_line(hull_pts[i], hull_pts[(i + 1) % len(hull_pts)])
    shape.finish(fill=(0.95, 0.96, 0.98), color=(0.06, 0.07, 0.08), width=0.7)

    # Bow Forecastle / Crew Mooring Area (y <= 244.8) -> Cool Silver Grey
    bow_poly = [p for p in hull_loop_d5 if p[1] <= 245.5]
    if len(bow_poly) > 4:
        b_pts = [fitz.Point(x - CLIP_D5.x0, y - CLIP_D5.y0) for x, y in bow_poly]
        for i in range(len(b_pts)):
            shape.draw_line(b_pts[i], b_pts[(i + 1) % len(b_pts)])
        shape.finish(fill=(0.80, 0.82, 0.85), color=(0.12, 0.13, 0.15), width=0.4)
        for gx in range(130, 206, 4):
            shape.draw_line(fitz.Point(gx - CLIP_D5.x0, 134.0 - CLIP_D5.y0), fitz.Point(gx - CLIP_D5.x0, 244.0 - CLIP_D5.y0))
        shape.finish(fill=None, color=(0.68, 0.70, 0.74), width=0.22)

    # Mid-Aft Galley / Service Zone forward of La Colombina (y = 676.0 .. 733.8)
    galley_d5 = fitz.Rect(126.3 - CLIP_D5.x0, 676.0 - CLIP_D5.y0, 208.7 - CLIP_D5.x0, 733.8 - CLIP_D5.y0)
    shape.draw_rect(galley_d5)
    shape.finish(fill=(0.64, 0.67, 0.72), color=(0.10, 0.11, 0.13), width=0.4)
    for gy in range(680, 732, 6):
        shape.draw_line(fitz.Point(129.0 - CLIP_D5.x0, gy - CLIP_D5.y0), fitz.Point(205.0 - CLIP_D5.x0, gy - CLIP_D5.y0))
    shape.finish(fill=None, color=(0.48, 0.51, 0.56), width=0.22)

    # Central Engine Casing Core on Deck 5
    casing_d5 = fitz.Rect(158.0 - CLIP_D5.x0, 567.0 - CLIP_D5.y0, 177.2 - CLIP_D5.x0, 613.5 - CLIP_D5.y0)
    shape.draw_rect(casing_d5)
    shape.finish(fill=(0.46, 0.49, 0.54), color=(0.08, 0.09, 0.11), width=0.45)

    for idx in range(376, 687):
        if idx in (422, 432):
            continue
        d = drawings[idx]
        if not CLIP_D5.intersects(d["rect"]):
            continue
        orig_fill = d.get("fill")
        fill_col = None
        if orig_fill is not None:
            r, g, b = orig_fill[0], orig_fill[1], orig_fill[2]
            if r > 0.95 and g > 0.90:  # Cream interior cabins
                fill_col = (0.76, 0.78, 0.82)
            elif b > 0.45 and r < 0.2:  # Blue oceanview cabins
                fill_col = (0.50, 0.53, 0.59)
            elif r > 0.85 and g > 0.50:  # Orange balcony cabins
                fill_col = (0.62, 0.65, 0.70)
            elif r < 0.15 and g < 0.15 and b < 0.15:  # Black icons/stairs
                fill_col = (0.10, 0.11, 0.13)
            else:
                fill_col = (0.42, 0.45, 0.50)
        stroke_col = (0.04, 0.05, 0.06) if d.get("color") is not None else None
        draw_pdf_item_to_shape(shape, d, CLIP_D5, fill_col, stroke_col)

    # Solid Emerald Green footprint for La Colombina
    col_pts = [fitz.Point(x - CLIP_D5.x0, y - CLIP_D5.y0) for x, y in colombina_clean_poly]
    for i in range(len(col_pts)):
        shape.draw_line(col_pts[i], col_pts[(i + 1) % len(col_pts)])
    shape.finish(fill=(0.08, 0.74, 0.38), color=(0.04, 0.42, 0.20), width=0.6)
    shape.commit()

    tex_path, bump_path = save_monochrome_textures("deck5_colombina", out_page)
    vec_data = {
        "name": "Deck5_La_Colombina",
        "clip": [CLIP_D5.x0, CLIP_D5.y0, CLIP_D5.x1, CLIP_D5.y1],
        "x_center": X_CENTER_D5,
        "y_mid": Y_MID,
        "hull_outer_loop": hull_loop_d5,
        "colosseo_port_outer": [],
        "colosseo_stbd_outer": [],
        "lifeboats": [],
        "mdr_poly": colombina_clean_poly,
        "zone_polys": zone_polys_d5,
        "wall_polylines": walls_d5,
        "elevators": elevators_d5,
        "engine_casing": [(158.0, 567.0), (177.2, 567.0), (177.2, 613.5), (158.0, 613.5)],
        "tex_plan": tex_path,
        "tex_bump": bump_path,
    }
    json_path = os.path.join(SCRATCH_DIR, "deck5_colombina_vector_data.json")
    with open(json_path, "w") as f:
        json.dump(vec_data, f)


# --- 3B & 3C. Render Deck 6 (Il Meneghino OR Arlecchino) Texture ---
def generate_deck6_variant(active_mdr_idx, active_mdr_poly, out_prefix, model_name):
    out_doc = fitz.open()
    out_page = out_doc.new_page(width=CLIP_D6.width, height=CLIP_D6.height)
    shape = out_page.new_shape()

    shape.draw_rect(fitz.Rect(0, 0, CLIP_D6.width, CLIP_D6.height))
    shape.finish(fill=(0.10, 0.11, 0.13), color=None)

    hull_pts = [fitz.Point(x - CLIP_D6.x0, y - CLIP_D6.y0) for x, y in hull_loop_d6]
    for i in range(len(hull_pts)):
        shape.draw_line(hull_pts[i], hull_pts[(i + 1) % len(hull_pts)])
    shape.finish(fill=(0.96, 0.97, 0.98), color=(0.06, 0.07, 0.08), width=0.7)

    # Bow Forecastle / Mooring Deck
    bow_poly = [p for p in hull_loop_d6 if p[1] <= 230.5]
    if len(bow_poly) > 4:
        b_pts = [fitz.Point(x - CLIP_D6.x0, y - CLIP_D6.y0) for x, y in bow_poly]
        for i in range(len(b_pts)):
            shape.draw_line(b_pts[i], b_pts[(i + 1) % len(b_pts)])
        shape.finish(fill=(0.80, 0.82, 0.85), color=(0.12, 0.13, 0.15), width=0.4)
        for gx in range(250, 325, 4):
            shape.draw_line(fitz.Point(gx - CLIP_D6.x0, 132.0 - CLIP_D6.y0), fitz.Point(gx - CLIP_D6.x0, 229.0 - CLIP_D6.y0))
        shape.finish(fill=None, color=(0.68, 0.70, 0.74), width=0.22)

    # Main Galley (between Arlecchino and Il Meneghino)
    galley_rect = fitz.Rect(244.0 - CLIP_D6.x0, 647.5 - CLIP_D6.y0, 277.2 - CLIP_D6.x0, 707.4 - CLIP_D6.y0)
    shape.draw_rect(galley_rect)
    shape.finish(fill=(0.62, 0.65, 0.70), color=(0.10, 0.11, 0.13), width=0.4)
    for gy in range(653, 705, 6):
        shape.draw_line(fitz.Point(247.0 - CLIP_D6.x0, gy - CLIP_D6.y0), fitz.Point(274.0 - CLIP_D6.x0, gy - CLIP_D6.y0))
    for gx in (254, 261, 268):
        shape.draw_line(fitz.Point(gx - CLIP_D6.x0, 650.0 - CLIP_D6.y0), fitz.Point(gx - CLIP_D6.x0, 704.0 - CLIP_D6.y0))
    shape.finish(fill=None, color=(0.45, 0.48, 0.53), width=0.25)

    # Central Engine Casing Core
    casing_rect = fitz.Rect(276.6 - CLIP_D6.x0, 571.8 - CLIP_D6.y0, 295.9 - CLIP_D6.x0, 613.6 - CLIP_D6.y0)
    shape.draw_rect(casing_rect)
    shape.finish(fill=(0.46, 0.49, 0.54), color=(0.08, 0.09, 0.11), width=0.45)
    for cy0, cy1 in [(573.0, 591.5), (593.0, 612.0)]:
        r_bay = fitz.Rect(278.0 - CLIP_D6.x0, cy0 - CLIP_D6.y0, 294.5 - CLIP_D6.x0, cy1 - CLIP_D6.y0)
        shape.draw_rect(r_bay)
        shape.draw_line(fitz.Point(r_bay.x0, r_bay.y0), fitz.Point(r_bay.x1, r_bay.y1))
        shape.draw_line(fitz.Point(r_bay.x1, r_bay.y0), fitz.Point(r_bay.x0, r_bay.y1))
    shape.finish(fill=None, color=(0.30, 0.33, 0.38), width=0.25)

    zone_greys = {
        307: (0.48, 0.51, 0.56),  # Il Meneghino when not highlighted
        308: (0.48, 0.51, 0.56),  # Arlecchino when not highlighted
        309: (0.68, 0.71, 0.75),  # Quelli della Notte Jazz Club
        373: (0.68, 0.71, 0.75),
        310: (0.38, 0.41, 0.46),  # My Moments Photo Store
        311: (0.78, 0.80, 0.84),  # My Tours
        312: (0.84, 0.86, 0.89),  # Colosseo
        313: (0.44, 0.47, 0.52),  # Illy Bar
        314: (0.64, 0.67, 0.72),  # Mastroianni Grand Bar
        374: (0.64, 0.67, 0.72),
        315: (0.50, 0.53, 0.58),  # Sanremo Theatre
        372: (0.50, 0.53, 0.58),
        375: (0.50, 0.53, 0.58),
    }

    for idx in range(307, 376):
        if idx == active_mdr_idx:
            continue
        d = drawings[idx]
        if not CLIP_D6.intersects(d["rect"]):
            continue
        fill_col = zone_greys.get(idx)
        if fill_col is None and d.get("fill") is not None:
            fill_col = (0.34, 0.37, 0.42)
        stroke_col = (0.04, 0.05, 0.06) if d.get("color") is not None else None
        draw_pdf_item_to_shape(shape, d, CLIP_D6, fill_col, stroke_col)

    mdr_pts = [fitz.Point(x - CLIP_D6.x0, y - CLIP_D6.y0) for x, y in active_mdr_poly]
    for i in range(len(mdr_pts)):
        shape.draw_line(mdr_pts[i], mdr_pts[(i + 1) % len(mdr_pts)])
    shape.finish(fill=(0.08, 0.74, 0.38), color=(0.04, 0.42, 0.20), width=0.6)
    shape.commit()

    tex_path, bump_path = save_monochrome_textures(out_prefix, out_page)

    zone_polys_d6 = {}
    for z_idx, z_name in [
        (307, "Il_Meneghino"),
        (308, "Arlecchino"),
        (309, "Jazz_Club"),
        (310, "Photo_Store"),
        (311, "My_Tours"),
        (312, "Colosseo"),
        (313, "Illy_Bar"),
        (314, "Mastroianni_Bar"),
        (315, "Sanremo_Theatre"),
    ]:
        if z_idx == active_mdr_idx:
            continue
        if z_idx == 308:
            zone_polys_d6[z_name] = arlecchino_clean_poly
        elif z_idx == 307:
            zone_polys_d6[z_name] = meneghino_clean_poly
        else:
            sps = extract_subpaths_xy(drawings[z_idx], n_bez=16)
            if sps:
                zone_polys_d6[z_name] = dedup_pts(max(sps, key=len), tol=0.10)

    walls_d6 = []
    for w_idx in [329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 368, 369, 370, 371]:
        sps = extract_subpaths_xy(drawings[w_idx], n_bez=12)
        for sp in sps:
            if w_idx == 329 and len(sp) >= 95:
                continue
            pts_clean = dedup_pts(sp, tol=0.15)
            if len(pts_clean) < 2:
                continue
            tlen = sum(math.hypot(pts_clean[k+1][0]-pts_clean[k][0], pts_clean[k+1][1]-pts_clean[k][1]) for k in range(len(pts_clean)-1))
            if tlen < 3.5:
                continue
            if any(point_in_poly(px, py, active_mdr_poly) for px, py in pts_clean):
                continue
            walls_d6.append(pts_clean)

    vec_data = {
        "name": model_name,
        "clip": [CLIP_D6.x0, CLIP_D6.y0, CLIP_D6.x1, CLIP_D6.y1],
        "x_center": X_CENTER_D6,
        "y_mid": Y_MID,
        "hull_outer_loop": hull_loop_d6,
        "colosseo_port_outer": dedup_pts(colosseo_port_d6, tol=0.08),
        "colosseo_stbd_outer": dedup_pts(colosseo_stbd_d6, tol=0.08),
        "lifeboats": lifeboats_d6,
        "mdr_poly": active_mdr_poly,
        "zone_polys": zone_polys_d6,
        "wall_polylines": walls_d6,
        "elevators": elevators_d6,
        "engine_casing": [(277.6, 572.5), (294.8, 572.5), (294.8, 612.5), (277.6, 612.5)],
        "tex_plan": tex_path,
        "tex_bump": bump_path,
    }
    json_path = os.path.join(SCRATCH_DIR, f"{out_prefix}_vector_data.json")
    with open(json_path, "w") as f:
        json.dump(vec_data, f)


# --- 3D. Render Deck 7 (Il Rugantino) Texture ---
def generate_deck7_rugantino():
    out_doc = fitz.open()
    out_page = out_doc.new_page(width=CLIP_D7.width, height=CLIP_D7.height)
    shape = out_page.new_shape()

    shape.draw_rect(fitz.Rect(0, 0, CLIP_D7.width, CLIP_D7.height))
    shape.finish(fill=(0.10, 0.11, 0.13), color=None)

    hull_pts = [fitz.Point(x - CLIP_D7.x0, y - CLIP_D7.y0) for x, y in hull_loop_d7]
    for i in range(len(hull_pts)):
        shape.draw_line(hull_pts[i], hull_pts[(i + 1) % len(hull_pts)])
    shape.finish(fill=(0.96, 0.97, 0.98), color=(0.06, 0.07, 0.08), width=0.7)

    # Bow Forecastle / Crew Deck on Deck 7 (y <= 255.0)
    bow_poly = [p for p in hull_loop_d7 if p[1] <= 255.5]
    if len(bow_poly) > 4:
        b_pts = [fitz.Point(x - CLIP_D7.x0, y - CLIP_D7.y0) for x, y in bow_poly]
        for i in range(len(b_pts)):
            shape.draw_line(b_pts[i], b_pts[(i + 1) % len(b_pts)])
        shape.finish(fill=(0.80, 0.82, 0.85), color=(0.12, 0.13, 0.15), width=0.4)
        for gx in range(376, 450, 4):
            shape.draw_line(fitz.Point(gx - CLIP_D7.x0, 132.0 - CLIP_D7.y0), fitz.Point(gx - CLIP_D7.x0, 254.0 - CLIP_D7.y0))
        shape.finish(fill=None, color=(0.68, 0.70, 0.74), width=0.22)

    zone_greys_d7 = {
        132: (0.72, 0.75, 0.79),  # Passeggiata Lungomare Riviera (Port)
        133: (0.72, 0.75, 0.79),  # Passeggiata Lungomare Riviera (Stbd)
        134: (0.62, 0.65, 0.70),  # Terrazza Superba Aft Lounge
        136: (0.66, 0.69, 0.74),  # Sunset Lounge Bar
        137: (0.82, 0.84, 0.88),  # Piazza di Spagna / Campidoglio
        138: (0.48, 0.51, 0.56),  # Galleria Shops
        139: (0.48, 0.51, 0.56),
        140: (0.48, 0.51, 0.56),
        141: (0.48, 0.51, 0.56),
        142: (0.48, 0.51, 0.56),
        143: (0.48, 0.51, 0.56),
        144: (0.48, 0.51, 0.56),
        145: (0.68, 0.71, 0.76),  # Co.De Museum
        146: (0.68, 0.71, 0.76),
        147: (0.85, 0.87, 0.90),  # Colosseo Upper Atrium
        148: (0.54, 0.57, 0.63),  # Laguna Casino
        149: (0.66, 0.69, 0.74),
        150: (0.44, 0.47, 0.52),  # Campari Bar
        151: (0.44, 0.47, 0.52),
        152: (0.50, 0.53, 0.58),  # Sanremo Theatre Upper Level
        153: (0.58, 0.61, 0.66),
        154: (0.58, 0.61, 0.66),
        155: (0.58, 0.61, 0.66),
        156: (0.58, 0.61, 0.66),
        157: (0.46, 0.49, 0.55),  # Bellavista Club Restaurant
        158: (0.58, 0.61, 0.66),
        159: (0.58, 0.61, 0.66),
    }

    for idx in range(132, 307):
        if idx == 135:
            continue
        d = drawings[idx]
        if not CLIP_D7.intersects(d["rect"]):
            continue
        fill_col = zone_greys_d7.get(idx)
        if fill_col is None and d.get("fill") is not None:
            fill_col = (0.36, 0.39, 0.44)
        stroke_col = (0.04, 0.05, 0.06) if d.get("color") is not None else None
        draw_pdf_item_to_shape(shape, d, CLIP_D7, fill_col, stroke_col)

    rug_pts = [fitz.Point(x - CLIP_D7.x0, y - CLIP_D7.y0) for x, y in rugantino_clean_poly]
    for i in range(len(rug_pts)):
        shape.draw_line(rug_pts[i], rug_pts[(i + 1) % len(rug_pts)])
    shape.finish(fill=(0.08, 0.74, 0.38), color=(0.04, 0.42, 0.20), width=0.6)
    shape.commit()

    tex_path, bump_path = save_monochrome_textures("deck7_rugantino", out_page)
    vec_data = {
        "name": "Deck7_Il_Rugantino",
        "clip": [CLIP_D7.x0, CLIP_D7.y0, CLIP_D7.x1, CLIP_D7.y1],
        "x_center": X_CENTER_D7,
        "y_mid": Y_MID,
        "hull_outer_loop": hull_loop_d7,
        "colosseo_port_outer": colosseo_port_d7,
        "colosseo_stbd_outer": colosseo_stbd_d7,
        "lifeboats": lifeboats_d7,
        "mdr_poly": rugantino_clean_poly,
        "zone_polys": zone_polys_d7,
        "wall_polylines": walls_d7,
        "elevators": elevators_d7,
        "engine_casing": [(404.1, 572.5), (421.3, 572.5), (421.3, 612.5), (404.1, 612.5)],
        "tex_plan": tex_path,
        "tex_bump": bump_path,
    }
    json_path = os.path.join(SCRATCH_DIR, "deck7_rugantino_vector_data.json")
    with open(json_path, "w") as f:
        json.dump(vec_data, f)


if __name__ == "__main__":
    generate_deck5_colombina()
    generate_deck6_variant(307, meneghino_clean_poly, "deck6_meneghino", "Deck6_Il_Meneghino")
    generate_deck6_variant(308, arlecchino_clean_poly, "deck6_arlecchino", "Deck6_Arlecchino")
    generate_deck7_rugantino()
    print("ALL 4 MDR VECTOR ASSETS & 8K TEXTURES GENERATED SUCCESSFULLY!")
