import fitz
import json
import math
import os
from PIL import Image, ImageOps, ImageFilter

PROJ_DIR = "/Users/dianjulie/Documents/Map Project"
SCRATCH_DIR = os.path.join(PROJ_DIR, "scratch")
PDF_PATH = os.path.join(PROJ_DIR, "SHIP PLAN OVERVIEW BOOKLET.pdf")

doc = fitz.open(PDF_PATH)
page = doc[4]  # Page 5: Ponte 6 - Matera
drawings = page.get_drawings()

# Exact bounding clip of Deck 6 column in PDF coordinates
CLIP = fitz.Rect(225.0, 122.0, 347.6, 808.0)
X_CENTER = 286.30
Y_MID = 464.885  # Midpoint between bow (128.23) and stern (801.54)


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


def dedup_pts(pts, tol=0.05):
    if not pts:
        return []
    out = [pts[0]]
    for p in pts[1:]:
        if (p[0] - out[-1][0])**2 + (p[1] - out[-1][1])**2 > tol * tol:
            out.append(p)
    if len(out) > 2 and (out[0][0] - out[-1][0])**2 + (out[0][1] - out[-1][1])**2 <= tol * tol:
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


# 1. Stitch the 100% exact outer hull contour of Deck 6 from #329 and #371
s329 = extract_subpaths_xy(drawings[329], n_bez=24)
s371_all = extract_subpaths_xy(drawings[371], n_bez=24)
colosseo_port_outer = None
colosseo_stbd_outer = None

for sp in s371_all:
    xs = [p[0] for p in sp]
    ys = [p[1] for p in sp]
    if len(sp) > 50 and abs(min(ys) - 427.1) < 1.0 and abs(max(ys) - 488.5) < 1.0:
        if min(xs) < 240.0 and max(xs) < 245.0:
            colosseo_port_outer = sp
        elif max(xs) > 332.0 and min(xs) > 327.0:
            colosseo_stbd_outer = sp

hull_outer_loop = (
    s329[147]
    + list(reversed(colosseo_port_outer))
    + s329[150]
    + list(reversed(s329[151]))
    + colosseo_stbd_outer
    + list(reversed(s329[148]))
)
hull_outer_loop = dedup_pts(hull_outer_loop, tol=0.08)

# 2. Extract the 16 Lifeboats from #342
s342 = extract_subpaths_xy(drawings[342], n_bez=12)
lifeboats = []
for sp in s342:
    xs = [p[0] for p in sp]
    ys = [p[1] for p in sp]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    if 10.0 < w < 15.0 and 25.0 < h < 32.0 and (max(xs) < 245.0 or min(xs) > 328.0):
        lifeboats.append(dedup_pts(sp, tol=0.12))

# 3. Exact Clean Outer Polygon of Ristorante Arlecchino (#308)
#    Every segment is >= 2.0 pt so the 3D top bevel is 100% manifold & crease-free!
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

# Extract major monochrome zone polygons (#307, #309, #310, #311, #312, #313, #314, #315)
zone_polys = {}
for z_idx, z_name in [
    (307, "Il_Meneghino"),
    (309, "Jazz_Club"),
    (310, "Photo_Store"),
    (311, "My_Tours"),
    (312, "Colosseo"),
    (313, "Illy_Bar"),
    (314, "Mastroianni_Bar"),
    (315, "Sanremo_Theatre"),
]:
    sps = extract_subpaths_xy(drawings[z_idx], n_bez=16)
    if sps:
        main_sp = max(sps, key=lambda s: len(s))
        zone_polys[z_name] = dedup_pts(main_sp, tol=0.10)

# Extract 3D architectural wall & structural linework subpaths from #329..#341 and #368..#371
wall_polylines = []
for w_idx in [329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 368, 369, 370, 371]:
    sps = extract_subpaths_xy(drawings[w_idx], n_bez=12)
    for sp in sps:
        if w_idx == 329 and len(sp) >= 95:
            continue
        pts_clean = dedup_pts(sp, tol=0.15)
        if len(pts_clean) < 2:
            continue
        total_len = sum(
            math.hypot(pts_clean[k+1][0] - pts_clean[k][0], pts_clean[k+1][1] - pts_clean[k][1])
            for k in range(len(pts_clean) - 1)
        )
        if total_len < 3.5:
            continue
        any_in_arl = False
        for px, py in pts_clean:
            if point_in_poly(px, py, arlecchino_clean_poly):
                any_in_arl = True
                break
        if any_in_arl:
            continue
        wall_polylines.append(pts_clean)

vec_data = {
    "clip": [CLIP.x0, CLIP.y0, CLIP.x1, CLIP.y1],
    "x_center": X_CENTER,
    "y_mid": Y_MID,
    "hull_outer_loop": hull_outer_loop,
    "colosseo_port_outer": dedup_pts(colosseo_port_outer, tol=0.08),
    "colosseo_stbd_outer": dedup_pts(colosseo_stbd_outer, tol=0.08),
    "lifeboats": lifeboats,
    "arlecchino_poly": arlecchino_clean_poly,
    "zone_polys": zone_polys,
    "wall_polylines": wall_polylines,
}
with open(os.path.join(SCRATCH_DIR, "deck6_vector_data.json"), "w") as f:
    json.dump(vec_data, f)

# 4. Render High-Contrast Black / White / Grey 8K Floor Plan Texture via PyMuPDF
out_doc = fitz.open()
out_page = out_doc.new_page(width=CLIP.width, height=CLIP.height)
shape = out_page.new_shape()

# Background fill (deep obsidian outside the ship hull)
shape.draw_rect(fitz.Rect(0, 0, CLIP.width, CLIP.height))
shape.finish(fill=(0.10, 0.11, 0.13), color=None)

# Fill the main ship hull interior (corridors & concourses) with crisp Pure Architectural White (#F6F7F9)
hull_pts_local = [fitz.Point(x - CLIP.x0, y - CLIP.y0) for x, y in hull_outer_loop]
for i in range(len(hull_pts_local)):
    shape.draw_line(hull_pts_local[i], hull_pts_local[(i + 1) % len(hull_pts_local)])
shape.finish(fill=(0.96, 0.97, 0.98), color=(0.06, 0.07, 0.08), width=0.7)

# Subtle architectural zone shading for Bow Mooring Deck, Engine Casing, and Galley
# a) Bow Forecastle / Mooring Deck (y = 128.2 .. 229.4) -> Light Cool Silver Grey
bow_poly = [p for p in hull_outer_loop if p[1] <= 230.5]
if len(bow_poly) > 4:
    b_pts = [fitz.Point(x - CLIP.x0, y - CLIP.y0) for x, y in bow_poly]
    for i in range(len(b_pts)):
        shape.draw_line(b_pts[i], b_pts[(i + 1) % len(b_pts)])
    shape.finish(fill=(0.80, 0.82, 0.85), color=(0.12, 0.13, 0.15), width=0.4)
    for gx in range(250, 325, 4):
        shape.draw_line(fitz.Point(gx - CLIP.x0, 132.0 - CLIP.y0), fitz.Point(gx - CLIP.x0, 229.0 - CLIP.y0))
    shape.finish(fill=None, color=(0.68, 0.70, 0.74), width=0.22)

# b) Main Galley (between Arlecchino and Il Meneghino on Port side) -> Medium Slate Grey
galley_rect = fitz.Rect(244.0 - CLIP.x0, 647.5 - CLIP.y0, 277.2 - CLIP.x0, 707.4 - CLIP.y0)
shape.draw_rect(galley_rect)
shape.finish(fill=(0.62, 0.65, 0.70), color=(0.10, 0.11, 0.13), width=0.4)
for gy in range(653, 705, 6):
    shape.draw_line(fitz.Point(247.0 - CLIP.x0, gy - CLIP.y0), fitz.Point(274.0 - CLIP.x0, gy - CLIP.y0))
for gx in (254, 261, 268):
    shape.draw_line(fitz.Point(gx - CLIP.x0, 650.0 - CLIP.y0), fitz.Point(gx - CLIP.x0, 704.0 - CLIP.y0))
shape.finish(fill=None, color=(0.45, 0.48, 0.53), width=0.25)

# c) Central Engine Casing Core -> Deep Charcoal Grey
casing_rect = fitz.Rect(276.6 - CLIP.x0, 571.8 - CLIP.y0, 295.9 - CLIP.y0, 613.6 - CLIP.y0)
shape.draw_rect(casing_rect)
shape.finish(fill=(0.46, 0.49, 0.54), color=(0.08, 0.09, 0.11), width=0.45)
for cy0, cy1 in [(573.0, 591.5), (593.0, 612.0)]:
    r_bay = fitz.Rect(278.0 - CLIP.x0, cy0 - CLIP.y0, 294.5 - CLIP.x0, cy1 - CLIP.y0)
    shape.draw_rect(r_bay)
    shape.draw_line(fitz.Point(r_bay.x0, r_bay.y0), fitz.Point(r_bay.x1, r_bay.y1))
    shape.draw_line(fitz.Point(r_bay.x1, r_bay.y0), fitz.Point(r_bay.x0, r_bay.y1))
shape.finish(fill=None, color=(0.30, 0.33, 0.38), width=0.25)

# Rich Multi-Tone Black / White / Grey Palette for Deck 6 Zones
zone_greys = {
    307: (0.48, 0.51, 0.56),  # Il Meneghino Restaurant -> Deep Architectural Slate Grey
    309: (0.68, 0.71, 0.75),  # Quelli della Notte Jazz Club -> Medium Silver-Slate Grey
    373: (0.68, 0.71, 0.75),
    310: (0.38, 0.41, 0.46),  # My Moments Photo Store -> Dark Pewter/Charcoal Grey
    311: (0.78, 0.80, 0.84),  # My Tours -> Light Pearl Grey
    312: (0.84, 0.86, 0.89),  # Colosseo -> Bright Architectural Silver-White
    313: (0.44, 0.47, 0.52),  # Illy Bar -> Deep Slate Grey
    314: (0.64, 0.67, 0.72),  # Mastroianni Grand Bar -> Medium Cool Grey
    374: (0.64, 0.67, 0.72),
    315: (0.50, 0.53, 0.58),  # Sanremo Theatre / Mito Disco -> Rich Theatre Slate Grey
    372: (0.50, 0.53, 0.58),
    375: (0.50, 0.53, 0.58),
}

for idx in range(307, 376):
    if idx == 308:
        continue
    d = drawings[idx]
    if not CLIP.intersects(d["rect"]):
        continue
    for item in d["items"]:
        op = item[0]
        if op == "l":
            p1 = fitz.Point(item[1].x - CLIP.x0, item[1].y - CLIP.y0)
            p2 = fitz.Point(item[2].x - CLIP.x0, item[2].y - CLIP.y0)
            shape.draw_line(p1, p2)
        elif op == "c":
            p1 = fitz.Point(item[1].x - CLIP.x0, item[1].y - CLIP.y0)
            p2 = fitz.Point(item[2].x - CLIP.x0, item[2].y - CLIP.y0)
            p3 = fitz.Point(item[3].x - CLIP.x0, item[3].y - CLIP.y0)
            p4 = fitz.Point(item[4].x - CLIP.x0, item[4].y - CLIP.y0)
            shape.draw_bezier(p1, p2, p3, p4)
        elif op == "re":
            r = item[1]
            nr = fitz.Rect(r.x0 - CLIP.x0, r.y0 - CLIP.y0, r.x1 - CLIP.x0, r.y1 - CLIP.y0)
            shape.draw_rect(nr)
    fill_col = zone_greys.get(idx)
    if fill_col is None and d.get("fill") is not None:
        fill_col = (0.34, 0.37, 0.42)  # Services / Restrooms -> Dark Charcoal Grey
    stroke_col = (0.04, 0.05, 0.06) if d.get("color") is not None else None
    w = (d.get("width") or 0.22) * 1.45
    shape.finish(fill=fill_col, color=stroke_col, width=w, even_odd=d.get("even_odd", False))

# Draw clean solid Arlecchino polygon over the Arlecchino area so zero internal lines appear inside it
arl_pts_local = [fitz.Point(x - CLIP.x0, y - CLIP.y0) for x, y in arlecchino_clean_poly]
for i in range(len(arl_pts_local)):
    shape.draw_line(arl_pts_local[i], arl_pts_local[(i + 1) % len(arl_pts_local)])
shape.finish(fill=(0.08, 0.74, 0.38), color=(0.04, 0.42, 0.20), width=0.6)

shape.commit()

pix = out_page.get_pixmap(dpi=800)
tex_path = os.path.join(SCRATCH_DIR, "deck6_monochrome_plan_8k.png")
pix.save(tex_path)
print("Saved high-contrast 8K monochrome texture:", tex_path, pix.width, pix.height)

im_color = Image.open(tex_path).convert("L")
im_bump = ImageOps.autocontrast(im_color)
im_bump = im_bump.filter(ImageFilter.GaussianBlur(radius=0.8))
bump_path = os.path.join(SCRATCH_DIR, "deck6_monochrome_bump_8k.png")
im_bump.save(bump_path)
print("Saved 8K bump map:", bump_path)
