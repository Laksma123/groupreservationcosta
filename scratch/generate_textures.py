import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = "/Users/dianjulie/Documents/Map Project/scratch/textures"
PHOTO_DIR = "/Users/dianjulie/Documents/Map Project/Arlecchino 1st Block Starboardside"
os.makedirs(OUT_DIR, exist_ok=True)


def make_arlecchino_carpet(size=1024):
    """
    Generates the iconic Costa Smeralda Ristorante Arlecchino carpet texture:
    Deep crimson/burgundy hexagonal lozenges surrounded by black-and-white
    striped radiating fan/trapezoid segments, on a rich crimson interstitial field
    with woven carpet fiber micro-texture.
    """
    red_main = (158, 25, 38)       # Rich Arlecchino crimson
    red_dark = (115, 14, 24)       # Darker crimson border/inner
    ivory = (232, 226, 218)        # Off-white / cream stripe
    black = (22, 18, 20)           # Charcoal black stripe

    # Base background is rich crimson red (fills the interstitial hexagons/diamonds!)
    img = Image.new("RGB", (size, size), red_main)
    draw = ImageDraw.Draw(img)

    def draw_striped_quad(p0, p1, p2, p3, n_stripes=9):
        """Fill quad p0-p1-p2-p3 with alternating black & ivory stripes interpolating along p0->p1 and p3->p2."""
        for i in range(n_stripes):
            t0 = i / n_stripes
            t1 = (i + 1) / n_stripes
            a0 = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
            a1 = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
            b0 = (p3[0] + (p2[0] - p3[0]) * t0, p3[1] + (p2[1] - p3[1]) * t0)
            b1 = (p3[0] + (p2[0] - p3[0]) * t1, p3[1] + (p2[1] - p3[1]) * t1)
            col = ivory if (i % 2 == 0) else black
            draw.polygon([a0, a1, b1, b0], fill=col)
        draw.line([p0, p1, p2, p3, p0], fill=black, width=3)

    # Tile grid: 2x2 staggered repeating cells per texture
    nx, ny = 2, 2
    cw = size / nx
    ch = size / ny

    for row in range(-1, ny + 2):
        for col in range(-1, nx + 2):
            cx = (col + (0.5 if row % 2 != 0 else 0.0)) * cw
            cy = row * ch

            # Central elongated hexagon (crimson red block)
            rx = cw * 0.25
            ry = ch * 0.19
            sx = cw * 0.14
            hex_pts = [
                (cx - rx, cy),
                (cx - sx, cy - ry),
                (cx + sx, cy - ry),
                (cx + rx, cy),
                (cx + sx, cy + ry),
                (cx - sx, cy + ry),
            ]

            # Outer boundary of the fan ring around the crimson hexagon
            orx = cw * 0.44
            ory = ch * 0.36
            osx = cw * 0.24
            outer_pts = [
                (cx - orx, cy),
                (cx - osx, cy - ory),
                (cx + osx, cy - ory),
                (cx + orx, cy),
                (cx + osx, cy + ory),
                (cx - osx, cy + ory),
            ]

            # 6 radiating striped fan segments around the crimson hexagon
            for k in range(6):
                kn = (k + 1) % 6
                draw_striped_quad(hex_pts[k], hex_pts[kn], outer_pts[kn], outer_pts[k], n_stripes=9)

            draw.polygon(hex_pts, fill=red_main, outline=black)
            in_rx, in_ry, in_sx = rx * 0.80, ry * 0.76, sx * 0.80
            in_pts = [
                (cx - in_rx, cy),
                (cx - in_sx, cy - in_ry),
                (cx + in_sx, cy - in_ry),
                (cx + in_rx, cy),
                (cx + in_sx, cy + in_ry),
                (cx - in_sx, cy + in_ry),
            ]
            draw.line(in_pts + [in_pts[0]], fill=red_dark, width=3)
            draw.line(hex_pts + [hex_pts[0]], fill=black, width=4)
            draw.line(outer_pts + [outer_pts[0]], fill=black, width=4)

    # Add realistic woven carpet tuft micro-noise
    arr = np.array(img, dtype=np.float32)
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 7.5, (size, size, 1))
    x_grid = (np.sin(np.linspace(0, size * math.pi, size)) * 3.0)[None, :, None]
    y_grid = (np.cos(np.linspace(0, size * math.pi, size)) * 3.0)[:, None, None]
    arr = np.clip(arr + noise + x_grid + y_grid, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr)
    out.save(os.path.join(OUT_DIR, "arlecchino_carpet.png"))
    print("Saved arlecchino_carpet.png")


def make_corridor_tile(width=2048, height=1024):
    """
    Generates the exact symmetrical black-and-white geometric ceramic corridor runner tile
    from Costa Smeralda Ristorante Arlecchino (14.14.04 (2).jpeg):
    - Left & Right margins (U = 0.00..0.21 and 0.79..1.00): plain dark charcoal ceramic tile grid
    - Center (U = 0.21..0.79, V = 0.00..1.00): Single centered row of square geometric medallions:
      1. Central solid black square
      2. Inner white square frame with diagonal corner miters & midpoint grout lines
      3. Outer black square frame with diagonal corner miters
      4. 2 white isosceles right triangles pointing outward on each of the 4 sides of the black frame
         (creating the signature interlocking sawtooth / diamond border)
    """
    black = (30, 30, 32)
    ivory = (236, 232, 224)
    grout_dark = (48, 48, 52)
    grout_light = (150, 146, 140)

    img = Image.new("RGB", (width, height), black)
    draw = ImageDraw.Draw(img)

    # 1. Background grid of dark charcoal ceramic tiles across the whole corridor width
    # 8 columns across width (2048px -> 256px per tile), 4 rows along length (1024px -> 256px per tile)
    tile_step = 256
    for x in range(0, width + 1, tile_step):
        draw.line([(x, 0), (x, height)], fill=grout_dark, width=3)
    for y in range(0, height + 1, tile_step):
        draw.line([(0, y), (width, y)], fill=grout_dark, width=3)

    # Center of the corridor medallion: cx = width // 2 (1024), cy = height // 2 (512)
    cx = width // 2
    cy = height // 2

    # Half-sizes of the concentric square layers (in pixels, out of height=1024):
    # Exact 45-45-90 right triangles: r_black_outer = 342, tri_h = 170 -> r_tri_tip = 512 (touches seamlessly at y=0/1024!)
    r_tri_tip = 512       # Outer apex of the 2 white triangles on each side (seamless vertical tiling!)
    r_black_outer = 342   # Outer edge of the black square frame (2 * 171px = exact 45-deg triangles)
    r_white_outer = 252   # Outer edge of the inner white square frame
    r_center_black = 140  # Half-size of the central solid black square

    # Helper to draw the 2 outward-pointing white right triangles along each of the 4 sides of the black square frame
    # Each side of the black frame has length 2 * r_black_outer (from -r_black_outer to +r_black_outer),
    # split into 2 triangles: [-r_black_outer .. 0] and [0 .. +r_black_outer], with height (r_tri_tip - r_black_outer) = 132px.
    tri_h = r_tri_tip - r_black_outer
    for seg_start, seg_end in [(-r_black_outer, 0), (0, r_black_outer)]:
        seg_mid = (seg_start + seg_end) // 2
        # Top side (pointing -Y)
        pts_top = [
            (cx + seg_start, cy - r_black_outer),
            (cx + seg_end,   cy - r_black_outer),
            (cx + seg_mid,   cy - r_black_outer - tri_h),
        ]
        draw.polygon(pts_top, fill=ivory, outline=grout_dark)

        # Bottom side (pointing +Y)
        pts_bot = [
            (cx + seg_start, cy + r_black_outer),
            (cx + seg_end,   cy + r_black_outer),
            (cx + seg_mid,   cy + r_black_outer + tri_h),
        ]
        draw.polygon(pts_bot, fill=ivory, outline=grout_dark)

        # Left side (pointing -X)
        pts_left = [
            (cx - r_black_outer, cy + seg_start),
            (cx - r_black_outer, cy + seg_end),
            (cx - r_black_outer - tri_h, cy + seg_mid),
        ]
        draw.polygon(pts_left, fill=ivory, outline=grout_dark)

        # Right side (pointing +X)
        pts_right = [
            (cx + r_black_outer, cy + seg_start),
            (cx + r_black_outer, cy + seg_end),
            (cx + r_black_outer + tri_h, cy + seg_mid),
        ]
        draw.polygon(pts_right, fill=ivory, outline=grout_dark)

    # Wrapping 3rd left & right triangles at the top/bottom seam (y = 0 and y = height)
    # so the left/right sawtooth border (< < < and > > >) is 100% continuous along the corridor!
    for seam_cy in (0, height):
        # Left wrapping triangle (split by horizontal grout line at seam_cy)
        for dy0, dy1 in [(-tri_h, 0), (0, tri_h)]:
            pts_l_seam = [
                (cx - r_black_outer, seam_cy + dy0),
                (cx - r_black_outer, seam_cy),
                (cx - r_black_outer - tri_h, seam_cy),
            ] if dy0 < 0 else [
                (cx - r_black_outer, seam_cy),
                (cx - r_black_outer, seam_cy + dy1),
                (cx - r_black_outer - tri_h, seam_cy),
            ]
            draw.polygon(pts_l_seam, fill=ivory, outline=grout_dark)
            pts_r_seam = [
                (cx + r_black_outer, seam_cy + dy0),
                (cx + r_black_outer, seam_cy),
                (cx + r_black_outer + tri_h, seam_cy),
            ] if dy0 < 0 else [
                (cx + r_black_outer, seam_cy),
                (cx + r_black_outer, seam_cy + dy1),
                (cx + r_black_outer + tri_h, seam_cy),
            ]
            draw.polygon(pts_r_seam, fill=ivory, outline=grout_dark)

    # 2. Outer Black Square Frame (from r_white_outer to r_black_outer)
    draw.rectangle(
        [cx - r_black_outer, cy - r_black_outer, cx + r_black_outer, cy + r_black_outer],
        fill=black,
        outline=grout_dark,
        width=3,
    )

    # 3. Inner White Square Frame (from r_center_black to r_white_outer)
    draw.rectangle(
        [cx - r_white_outer, cy - r_white_outer, cx + r_white_outer, cy + r_white_outer],
        fill=ivory,
        outline=grout_light,
        width=3,
    )

    # 4. Central Solid Black Square
    draw.rectangle(
        [cx - r_center_black, cy - r_center_black, cx + r_center_black, cy + r_center_black],
        fill=black,
        outline=grout_dark,
        width=4,
    )

    # 5. Authentic Tile Miter & Grout Joints inside the Medallion (matching 14.14.04 (2).jpeg!)
    # Diagonal corner miters across both the white and black frames
    for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        # Across white frame (from r_center_black to r_white_outer)
        draw.line(
            [(cx + sx * r_center_black, cy + sy * r_center_black),
             (cx + sx * r_white_outer,  cy + sy * r_white_outer)],
            fill=grout_light,
            width=3,
        )
        # Across black frame (from r_white_outer to r_black_outer)
        draw.line(
            [(cx + sx * r_white_outer,  cy + sy * r_white_outer),
             (cx + sx * r_black_outer,  cy + sy * r_black_outer)],
            fill=grout_dark,
            width=3,
        )
    # Midpoint orthogonal grout joints across the white and black frames
    for sign in (-1, 1):
        # Vertical midpoints (top & bottom of white frame)
        draw.line([(cx, cy + sign * r_center_black), (cx, cy + sign * r_white_outer)], fill=grout_light, width=3)
        # Horizontal midpoints (left & right of white frame)
        draw.line([(cx + sign * r_center_black, cy), (cx + sign * r_white_outer, cy)], fill=grout_light, width=3)

    # Subtle ceramic micro-grain
    arr = np.array(img, dtype=np.float32)
    rng = np.random.default_rng(99)
    arr = np.clip(arr + rng.normal(0, 2.2, (height, width, 1)), 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(os.path.join(OUT_DIR, "corridor_tile.png"))
    print("Saved symmetrical corridor_tile.png")
    print("Saved corridor_tile.png")


def make_carrara_marble(size=1024):
    """
    Generates realistic white Carrara / Calacatta marble texture with grey/taupe veins
    matching the dining tables in 14.14.04 (3).jpeg and 14.14.06.jpeg.
    """
    rng = np.random.default_rng(108)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32) / size

    # Multi-octave domain warping for realistic marble veins
    def fbm(u, v, octaves=5, seed_offset=0):
        val = np.zeros_like(u)
        amp = 0.5
        freq = 2.0 * math.pi
        for o in range(octaves):
            ph1 = (o * 1.7 + seed_offset)
            ph2 = (o * 2.3 - seed_offset)
            val += amp * (
                np.sin(u * freq + np.cos(v * freq * 0.8 + ph1))
                + np.cos(v * freq * 1.1 - np.sin(u * freq * 0.9 + ph2))
            ) * 0.5
            freq *= 2.02
            amp *= 0.5
        return val

    w1 = fbm(x, y, octaves=5, seed_offset=1.2)
    w2 = fbm(x + 0.4, y - 0.3, octaves=5, seed_offset=3.7)

    # Primary diagonal Calacatta vein
    vein1 = np.abs(np.sin((x * 1.4 + y * 0.9 + w1 * 0.35) * math.pi * 2.0))
    vein1_mask = np.exp(-((vein1) ** 2) / 0.0045)

    # Secondary softer branching vein
    vein2 = np.abs(np.sin((x * 0.8 - y * 1.3 + w2 * 0.4) * math.pi * 3.0))
    vein2_mask = np.exp(-((vein2) ** 2) / 0.0020) * 0.55

    # Broad subtle warm clouding
    cloud = (w1 + 1.0) * 0.5

    # Base warm white Carrara color: (246, 244, 239)
    r = 246.0 - cloud * 7.0 - vein1_mask * 58.0 - vein2_mask * 36.0
    g = 244.0 - cloud * 8.0 - vein1_mask * 60.0 - vein2_mask * 38.0
    b = 239.0 - cloud * 9.0 - vein1_mask * 62.0 - vein2_mask * 40.0

    rgb = np.stack([r, g, b], axis=-1)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb).filter(ImageFilter.GaussianBlur(radius=0.8))
    img.save(os.path.join(OUT_DIR, "carrara_marble.png"))
    print("Saved carrara_marble.png")


def crop_photo_assets():
    """
    Crops real decorative plates, framed paintings, and menu cards from the 8 photos.
    """
    # 1. 9 Decorative Fornasetti Plates from 14.14.04 (3).jpeg (1920x1080)
    p_plates = Image.open(os.path.join(PHOTO_DIR, "WhatsApp Image 2026-10-24 at 14.14.04 (3).jpeg"))
    w, h = p_plates.size
    # Plates are around x: 0.39..0.51, y: 0.23..0.45
    plates_crop = p_plates.crop((int(w * 0.395), int(h * 0.235), int(w * 0.505), int(h * 0.445)))
    plates_crop.save(os.path.join(OUT_DIR, "plates_wall.png"))

    # Fire safety sticker from 14.14.04 (3).jpeg
    fire_crop = p_plates.crop((int(w * 0.028), int(h * 0.435), int(w * 0.098), int(h * 0.482)))
    fire_crop.save(os.path.join(OUT_DIR, "fire_sticker.png"))

    # 2. Framed portrait from 14.14.04 (1).jpeg (4032x2268)
    p_art = Image.open(os.path.join(PHOTO_DIR, "WhatsApp Image 2026-10-24 at 14.14.04 (1).jpeg"))
    wa, ha = p_art.size
    art1 = p_art.crop((int(wa * 0.252), int(ha * 0.245), int(wa * 0.412), int(ha * 0.568)))
    art1.save(os.path.join(OUT_DIR, "framed_art_1.png"))

    # 3. Framed B&W window pier photo from 14.14.05.jpeg (4032x2268)
    p5 = Image.open(os.path.join(PHOTO_DIR, "WhatsApp Image 2026-10-24 at 14.14.05.jpeg"))
    w5, h5 = p5.size
    art2 = p5.crop((int(w5 * 0.232), int(h5 * 0.360), int(w5 * 0.285), int(h5 * 0.492)))
    art2.save(os.path.join(OUT_DIR, "framed_art_2.png"))

    # 4. Framed pillar portrait from 14.14.06.jpeg
    p6 = Image.open(os.path.join(PHOTO_DIR, "WhatsApp Image 2026-10-24 at 14.14.06.jpeg"))
    w6, h6 = p6.size
    art3 = p6.crop((int(w6 * 0.763), int(h6 * 0.292), int(w6 * 0.818), int(h6 * 0.462)))
    art3.save(os.path.join(OUT_DIR, "framed_art_3.png"))

    # 5. Mediterranean Sea & Daylight Horizon Backdrop for Ship Windows
    w_sea, h_sea = 1024, 512
    y_sea, x_sea = np.mgrid[0:h_sea, 0:w_sea].astype(np.float32)
    t_v = y_sea / h_sea  # 0 at top (sky), 1 at bottom (sea)
    sea_img = np.zeros((h_sea, w_sea, 3), dtype=np.float32)
    # Upper 58%: bright Mediterranean sky gradient (soft azure to warm sunlit horizon)
    sky_mask = t_v < 0.58
    t_sky = np.clip(t_v / 0.58, 0.0, 1.0)
    sea_img[:, :, 0] = np.where(sky_mask, 165 + t_sky * 78, 0)
    sea_img[:, :, 1] = np.where(sky_mask, 208 + t_sky * 40, 0)
    sea_img[:, :, 2] = np.where(sky_mask, 245 + t_sky * 8, 0)
    # Lower 42%: sparkling turquoise-blue Mediterranean sea with sun shimmer
    t_water = np.clip((t_v - 0.58) / 0.42, 0.0, 1.0)
    shimmer = np.sin(x_sea * 0.15 + y_sea * 0.8) * np.cos(x_sea * 0.07 - y_sea * 1.2) * 14.0 * (1.0 - t_water * 0.6)
    sea_img[:, :, 0] = np.where(~sky_mask, 48 + (1.0 - t_water) * 95 + shimmer, sea_img[:, :, 0])
    sea_img[:, :, 1] = np.where(~sky_mask, 125 + (1.0 - t_water) * 85 + shimmer, sea_img[:, :, 1])
    sea_img[:, :, 2] = np.where(~sky_mask, 175 + (1.0 - t_water) * 60 + shimmer, sea_img[:, :, 2])
    Image.fromarray(np.clip(sea_img, 0, 255).astype(np.uint8)).save(os.path.join(OUT_DIR, "ocean_view.png"))
    print("Cropped real photo art assets and generated ocean_view.png successfully!")


if __name__ == "__main__":
    make_arlecchino_carpet(1024)
    make_corridor_tile(2048, 1024)
    make_carrara_marble(1024)
    crop_photo_assets()
