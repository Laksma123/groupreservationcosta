import os
import sys
import math
import subprocess
import numpy as np

ROOT = "/Users/dianjulie/Documents/Map Project"
BLEND_PATH = os.path.join(ROOT, "arlecchino_block1.blend")
GLB_PATH = os.path.join(ROOT, "arlecchino_block1.glb")
TEX_DIR = os.path.join(ROOT, "scratch", "textures")
PHOTO_B5_DIR = os.path.join(ROOT, "Arlecchino 5th Block")
os.makedirs(TEX_DIR, exist_ok=True)

# ==============================================================================
# 0. GENERATE AUTHENTIC BLOCK 5 TEXTURES FROM REAL PHOTOS & PROCEDURAL PATTERNS
# ==============================================================================
def generate_block5_textures():
    from PIL import Image, ImageDraw, ImageFilter
    # 1. Green Arlecchino Carpet Texture (Calibrated to Real Photo Linear/sRGB Contrast + Baked Table Contact Shadows)
    w_c, h_c = 2048, 2048
    teal_border = (16, 56, 76)
    teal_dark   = (20, 66, 88)
    sage_green  = (58, 88, 98)
    cream_white = (158, 150, 138)
    peach_terra = (146, 94, 70)
    coral_red   = (124, 36, 40)

    img_c = Image.new("RGB", (w_c, h_c), teal_dark)
    draw_c = ImageDraw.Draw(img_c)

    # Interior grid of 6x8 harlequin pinwheel squares inside the border
    b_px = 68  # Border width in pixels (~3.3% of carpet width -> ~24cm physical border)
    ix0, iy0, ix1, iy1 = b_px, b_px, w_c - b_px, h_c - b_px
    nx, ny = 6, 8
    cw = (ix1 - ix0) / nx
    ch = (iy1 - iy0) / ny

    palette_cycle = [
        (teal_dark, cream_white, sage_green, peach_terra, sage_green, coral_red, cream_white, teal_dark),
        (sage_green, peach_terra, teal_dark, cream_white, coral_red, sage_green, teal_dark, cream_white),
        (cream_white, teal_dark, peach_terra, coral_red, teal_dark, cream_white, sage_green, peach_terra),
        (peach_terra, coral_red, cream_white, sage_green, cream_white, teal_dark, peach_terra, sage_green),
    ]

    for r in range(ny):
        for c in range(nx):
            x0 = ix0 + c * cw
            y0 = iy0 + r * ch
            x1 = x0 + cw
            y1 = y0 + ch
            xm = 0.5 * (x0 + x1)
            ym = 0.5 * (y0 + y1)
            pal = palette_cycle[(r * 3 + c) % len(palette_cycle)]

            tris = [
                [(x0, y0), (xm, y0), (xm, ym)],
                [(xm, y0), (x1, y0), (xm, ym)],
                [(x1, y0), (x1, ym), (xm, ym)],
                [(x1, ym), (x1, y1), (xm, ym)],
                [(x1, y1), (xm, y1), (xm, ym)],
                [(xm, y1), (x0, y1), (xm, ym)],
                [(x0, y1), (x0, ym), (xm, ym)],
                [(x0, ym), (x0, y0), (xm, ym)],
            ]
            for t_i, pts in enumerate(tris):
                draw_c.polygon(pts, fill=pal[t_i], outline=(18, 42, 54))

    # Outer deep-teal carpet border
    draw_c.rectangle([0, 0, w_c, b_px], fill=teal_border)
    draw_c.rectangle([0, h_c - b_px, w_c, h_c], fill=teal_border)
    draw_c.rectangle([0, 0, b_px, h_c], fill=teal_border)
    draw_c.rectangle([w_c - b_px, 0, w_c, h_c], fill=teal_border)
    draw_c.rectangle([b_px, b_px, w_c - b_px, h_c - b_px], outline=(10, 38, 52), width=8)

    # Bake soft ambient-occlusion contact shadows under the 10 central tables & 2 black marble pillars
    # Carpet spans X = [30.65, 37.80] (dx=7.15), Y = [3.36, 14.10] (dy=10.74)
    # UV mapping: u = (y - 3.36)/10.74 -> col = u * w_c; w = (x - 30.65)/7.15 -> row = (1 - w) * h_c
    ao_img = Image.new("L", (w_c, h_c), 255)
    ao_draw = ImageDraw.Draw(ao_img)
    def world_box_to_carpet_px(wx, wy, sx, sy):
        u0 = (wy - sy * 0.5 - 3.36) / 10.74
        u1 = (wy + sy * 0.5 - 3.36) / 10.74
        w0 = (wx - sx * 0.5 - 30.65) / 7.15
        w1 = (wx + sx * 0.5 - 30.65) / 7.15
        c0, c1 = int(u0 * w_c), int(u1 * w_c)
        r0, r1 = int((1.0 - w1) * h_c), int((1.0 - w0) * h_c)
        return [c0, r0, c1, r1]

    # Pillars at (33.15, 5.95) & (33.15, 11.51)
    for py in (5.95, 11.51):
        ao_draw.ellipse(world_box_to_carpet_px(33.15, py, 1.25, 1.25), fill=85)
    # 4 Forward 4x tables at X = 31.85
    for ty in (4.55, 7.35, 10.11, 12.91):
        ao_draw.rounded_rectangle(world_box_to_carpet_px(31.85, ty, 1.85, 1.45), radius=52, fill=95)
    # 2 Long 10x Oak tables at X = 35.55
    for ty in (7.35, 10.11):
        ao_draw.rounded_rectangle(world_box_to_carpet_px(35.55, ty, 3.95, 1.60), radius=60, fill=90)
    # 4 Side 4x tables at X = 34.475, 36.625
    for tx in (34.475, 36.625):
        for ty in (4.55, 12.91):
            ao_draw.rounded_rectangle(world_box_to_carpet_px(tx, ty, 1.85, 1.45), radius=52, fill=95)
    # Aft glass partition wall base shadow at X = 37.80 (top of image r = 0..58)
    ao_draw.rectangle([0, 0, w_c, 58], fill=85)
    ao_img = ao_img.filter(ImageFilter.GaussianBlur(radius=42))
    ao_factor = np.array(ao_img, dtype=np.float32)[:, :, None] / 255.0

    # Woven carpet fiber micro-texture
    arr_c = np.array(img_c, dtype=np.float32) * ao_factor
    rng = np.random.default_rng(505)
    noise = rng.normal(0, 7.5, (h_c, w_c, 1))
    weave_x = (np.sin(np.linspace(0, w_c * math.pi * 0.5, w_c)) * 4.0)[None, :, None]
    weave_y = (np.cos(np.linspace(0, h_c * math.pi * 0.5, h_c)) * 4.0)[:, None, None]
    arr_c = np.clip(arr_c + noise + weave_x + weave_y, 0, 255).astype(np.uint8)
    carpet_path = os.path.join(TEX_DIR, "block5_green_carpet.png")
    Image.fromarray(arr_c).save(carpet_path)

    # 2. Rich Walnut-Honey Wood Plank Walkway Texture (Calibrated to Photo 14.30.44 (1).jpeg)
    w_w, h_w = 1024, 1024
    y_g, x_g = np.mgrid[0:h_w, 0:w_w].astype(np.float32)
    n_planks = 8
    plank_h = h_w / n_planks
    plank_idx = np.floor(y_g / plank_h).astype(np.int32)
    rng_w = np.random.default_rng(77)
    plank_shift = rng_w.uniform(-14.0, 14.0, size=(n_planks, 3))
    grain = (
        np.sin(x_g * 0.045 + np.sin(y_g * 0.12) * 1.8 + plank_idx * 2.1) * 8.5
        + np.sin(y_g * 0.65 + plank_idx * 1.3) * 4.0
        + rng_w.normal(0, 2.8, (h_w, w_w))
    )
    # Strong bevel shadow near plank edges so every plank has 3D relief
    plank_local_y = np.mod(y_g, plank_h) / plank_h
    plank_edge_ao = 0.72 + 0.30 * np.sin(plank_local_y * math.pi)
    base_rgb = np.zeros((h_w, w_w, 3), dtype=np.float32)
    base_rgb[:, :, 0] = (106.0 + plank_shift[plank_idx % n_planks, 0] + grain) * plank_edge_ao
    base_rgb[:, :, 1] = (72.0  + plank_shift[plank_idx % n_planks, 1] * 0.8 + grain * 0.78) * plank_edge_ao
    base_rgb[:, :, 2] = (44.0  + plank_shift[plank_idx % n_planks, 2] * 0.6 + grain * 0.55) * plank_edge_ao

    # Dark V-groove plank seams (horizontal along X and staggered butt joints)
    seam_y = (np.mod(y_g, plank_h) < 4.0) | (np.mod(y_g, plank_h) > plank_h - 3.0)
    butt_x = np.mod(x_g + plank_idx * 317.0, 512.0) < 4.0
    seams = seam_y | butt_x
    base_rgb[seams] *= 0.18
    wood_path = os.path.join(TEX_DIR, "block5_wood_plank.png")
    Image.fromarray(np.clip(base_rgb, 0, 255).astype(np.uint8)).save(wood_path)

    # 3. Warm Golden-Caramel Oak Texture (for 10x Tables 419 & 484 and their 20 Wooden Chairs, Photo 14.30.53 (1).jpeg)
    oak_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    yo, xo = np.mgrid[0:512, 0:512].astype(np.float32)
    cathedral = np.sin(xo * 0.045 + np.sin(yo * 0.035) * 3.2) * 11.5
    fine_pore = np.sin(xo * 0.38 + yo * 0.06) * 4.2 + np.cos(yo * 0.95) * 3.0
    oak_grain = cathedral + fine_pore
    # Bake curved self-shading along V (yo) so chair legs/rails & table bevels have natural dark underside contrast
    v_oak = 1.0 - (yo / 512.0)
    oak_shade = 0.56 + 0.48 * np.sin(np.clip(v_oak, 0.03, 0.97) * math.pi)
    oak_rgb[:, :, 0] = (146.0 + oak_grain) * oak_shade
    oak_rgb[:, :, 1] = (106.0 + oak_grain * 0.84) * oak_shade
    oak_rgb[:, :, 2] = (68.0  + oak_grain * 0.65) * oak_shade
    oak_path = os.path.join(TEX_DIR, "block5_light_oak.png")
    Image.fromarray(np.clip(oak_rgb, 0, 255).astype(np.uint8)).save(oak_path)

    # 4. Deep Espresso/Wenge Wood Tabletop Texture (for Block 5 2x and 4x Tables, Photo 14.30.44 (2).jpeg)
    dk_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    dk_grain = (
        np.sin(xo * 0.07 + np.sin(yo * 0.08) * 1.8) * 4.2
        + np.sin(xo * 0.42) * 1.6
        + np.cos(yo * 0.95) * 1.4
    )
    dk_rgb[:, :, 0] = 30.0 + dk_grain
    dk_rgb[:, :, 1] = 24.0 + dk_grain * 0.85
    dk_rgb[:, :, 2] = 21.0 + dk_grain * 0.76
    dk_path = os.path.join(TEX_DIR, "block5_dark_wood_top.png")
    Image.fromarray(np.clip(dk_rgb, 0, 255).astype(np.uint8)).save(dk_path)

    # 4A-bis. Shaded Upholstery & Wall Panel Textures with Deep Baked Self-Occlusion (so Material Preview & Rendered have rich dark sides!)
    # (i) Mushroom-Taupe / Warm Greige Outer Chair Shell Texture (block5_chair_ivory_shell.png)
    sh_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    u_sh = xo / 512.0
    v_sh = 1.0 - (yo / 512.0)
    rng_sh = np.random.default_rng(311)
    pebble = (
        np.sin(xo * 0.55 + np.cos(yo * 0.45) * 2.0) * 2.5
        + np.cos(yo * 0.60 - np.sin(xo * 0.50) * 2.0) * 2.5
        + rng_sh.normal(0, 2.0, (512, 512))
    )
    # Strong vertical + side-wrap shading: lower shell/legs darken to (42, 38, 34), upper crown rises to (142, 132, 120)
    vert_grad = 0.28 + 0.74 * (np.clip(v_sh, 0.0, 1.0) ** 0.72)
    seam_darken = 1.0 - 0.58 * np.exp(-((v_sh - 0.985) / 0.024) ** 2) - 0.48 * np.exp(-((v_sh - 0.02) / 0.035) ** 2)
    side_wrap = 0.74 + 0.26 * np.sin(u_sh * math.pi)
    sh_mult = vert_grad * seam_darken * side_wrap
    sh_rgb[:, :, 0] = 142.0 * sh_mult + pebble
    sh_rgb[:, :, 1] = 132.0 * sh_mult + pebble * 0.95
    sh_rgb[:, :, 2] = 118.0 * sh_mult + pebble * 0.88
    ivory_shell_path = os.path.join(TEX_DIR, "block5_chair_ivory_shell.png")
    Image.fromarray(np.clip(sh_rgb, 0, 255).astype(np.uint8)).save(ivory_shell_path)

    # (ii) Deep Prussian/Petrol Teal Leather Chair Inner Cushion Texture (block5_chair_teal_leather.png)
    tl_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    tl_grad = 0.24 + 0.78 * (np.clip(v_sh, 0.0, 1.0) ** 0.68)
    tl_seam = 1.0 - 0.58 * np.exp(-((v_sh - 0.985) / 0.025) ** 2) - 0.52 * np.exp(-((v_sh - 0.02) / 0.04) ** 2)
    tl_mult = tl_grad * tl_seam * (0.75 + 0.25 * np.sin(u_sh * math.pi))
    tl_rgb[:, :, 0] = 20.0  * tl_mult + pebble * 0.45
    tl_rgb[:, :, 1] = 72.0  * tl_mult + pebble * 0.75
    tl_rgb[:, :, 2] = 98.0  * tl_mult + pebble * 0.90
    teal_leather_path = os.path.join(TEX_DIR, "block5_chair_teal_leather.png")
    Image.fromarray(np.clip(tl_rgb, 0, 255).astype(np.uint8)).save(teal_leather_path)

    # (iii) Smoky Olive-Sage Architectural Wall Panel Texture with Deep Corner & Edge Vignette AO (block5_sage_wall_panel.png)
    sw_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    edge_x = np.sin(np.clip(u_sh, 0.015, 0.985) * math.pi) ** 0.42
    edge_y = np.sin(np.clip(v_sh, 0.015, 0.985) * math.pi) ** 0.42
    panel_ao = (0.48 + 0.52 * (edge_x * edge_y)) * (0.76 + 0.24 * np.sin(v_sh * math.pi * 0.85))
    stucco = rng_sh.normal(0, 2.4, (512, 512)) + np.sin(xo * 0.25) * np.cos(yo * 0.25) * 1.8
    sw_rgb[:, :, 0] = 86.0  * panel_ao + stucco
    sw_rgb[:, :, 1] = 92.0  * panel_ao + stucco * 1.02
    sw_rgb[:, :, 2] = 82.0  * panel_ao + stucco * 0.94
    sage_wall_path = os.path.join(TEX_DIR, "block5_sage_wall_panel.png")
    Image.fromarray(np.clip(sw_rgb, 0, 255).astype(np.uint8)).save(sage_wall_path)

    # (iv) Deep Muted Sage-Olive Leather Banquette Seat Texture (block5_sofa_sage_leather.png)
    sf_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    sf_ao = (0.38 + 0.62 * np.sin(np.clip(v_sh, 0.02, 0.98) * math.pi) ** 0.52)
    sf_rgb[:, :, 0] = 86.0  * sf_ao + pebble * 0.8
    sf_rgb[:, :, 1] = 100.0 * sf_ao + pebble * 0.9
    sf_rgb[:, :, 2] = 90.0  * sf_ao + pebble * 0.85
    sofa_sage_path = os.path.join(TEX_DIR, "block5_sofa_sage_leather.png")
    Image.fromarray(np.clip(sf_rgb, 0, 255).astype(np.uint8)).save(sofa_sage_path)

    # (v) Soft Feathered Contact-Shadow AO Decal Texture (block5_contact_ao.png) for under-table/chair floor grounding in Material Preview & Rendered!
    ao_w = 256
    ay, ax = np.mgrid[0:ao_w, 0:ao_w].astype(np.float32)
    nx_ao = (ax - ao_w * 0.5) / (ao_w * 0.5)
    ny_ao = (ay - ao_w * 0.5) / (ao_w * 0.5)
    r_sq = nx_ao ** 2 + ny_ao ** 2
    alpha_ao = np.clip(np.exp(-r_sq * 2.8) * (1.0 - np.clip(r_sq, 0.0, 1.0) ** 1.5), 0.0, 1.0)
    ao_rgba = np.zeros((ao_w, ao_w, 4), dtype=np.uint8)
    ao_rgba[:, :, 0] = 6
    ao_rgba[:, :, 1] = 8
    ao_rgba[:, :, 2] = 10
    ao_rgba[:, :, 3] = np.clip(alpha_ao * 175.0, 0, 255).astype(np.uint8)
    contact_ao_path = os.path.join(TEX_DIR, "block5_contact_ao.png")
    Image.fromarray(ao_rgba).save(contact_ao_path)

    # 4B. Venetian Murano Ribbed Blown-Glass Lathe Textures (Deep Jewel-Toned Emerald & Cognac Amber)
    #     u (0..1 around circumference) -> 24 vertical optic glass flutes/ribs
    #     v (0..1 from bottom finial z=0 to top tulip cup z=1.10m) -> warm radial bulb glow at v=0.335
    mw, mh = 512, 512
    vv, uu = np.mgrid[0:mh, 0:mw].astype(np.float32)
    u_norm = uu / mw
    v_norm = 1.0 - (vv / mh)  # v_norm=0 at bottom finial, v_norm=1 at top crown

    rib_wave = np.cos(u_norm * 24.0 * 2.0 * math.pi)
    rib_spec = np.power(np.clip(0.5 + 0.5 * np.sin(u_norm * 24.0 * 2.0 * math.pi + 0.6), 0.0, 1.0), 4.5)

    # Warm internal filament bulb glow concentrated in the main lantern bowl (v_norm = 0.335)
    bulb_glow = np.exp(-((v_norm - 0.335) / 0.078) ** 2)
    brim_highlight = np.exp(-((v_norm - 0.465) / 0.026) ** 2) * 0.32
    cup1_rim = np.exp(-((v_norm - 0.835) / 0.024) ** 2) * 0.22
    cup2_rim = np.exp(-((v_norm - 0.975) / 0.024) ** 2) * 0.22
    neck_shadow = (
        np.exp(-((v_norm - 0.205) / 0.024) ** 2)
        + np.exp(-((v_norm - 0.615) / 0.024) ** 2)
        + np.exp(-((v_norm - 0.755) / 0.022) ** 2)
        + np.exp(-((v_norm - 0.875) / 0.022) ** 2)
    ) * 0.52

    def build_murano_tex(base_col, deep_col, glow_tint, out_name):
        rgb = np.zeros((mh, mw, 3), dtype=np.float32)
        for c_i in range(3):
            glass_body = base_col[c_i] * (0.72 + 0.28 * rib_wave) + deep_col[c_i] * neck_shadow
            spec_add = (240.0 - glass_body) * (0.32 * rib_spec + brim_highlight + cup1_rim + cup2_rim)
            body_with_spec = np.clip(glass_body + spec_add, 8.0, 245.0)
            core_col = glow_tint[c_i] * 0.62 + 255.0 * 0.38
            rgb[:, :, c_i] = body_with_spec * (1.0 - 0.72 * bulb_glow) + core_col * (0.72 * bulb_glow)
        out_p = os.path.join(TEX_DIR, out_name)
        Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(out_p)
        return out_p

    murano_green_path = build_murano_tex(
        base_col=(24.0, 118.0, 92.0),
        deep_col=(-18.0, -68.0, -52.0),
        glow_tint=(165.0, 250.0, 205.0),
        out_name="block5_murano_green.png",
    )
    murano_amber_path = build_murano_tex(
        base_col=(138.0, 74.0, 48.0),
        deep_col=(-62.0, -38.0, -26.0),
        glow_tint=(255.0, 195.0, 130.0),
        out_name="block5_murano_amber.png",
    )

    # 5. High-Contrast Smoked & Frosted Geometric Patterned Glass Texture (matching Photo 14.31.15 (3).jpeg)
    gw, gh = 1024, 512
    img_g = Image.new("RGBA", (gw, gh), (24, 30, 34, 228))
    draw_g = ImageDraw.Draw(img_g)
    frosted = (188, 184, 174, 246)
    semi_frost = (118, 124, 122, 232)
    g_cols, g_rows = 8, 5
    gcw = gw / g_cols
    gch = gh / g_rows
    for gr in range(g_rows):
        for gc in range(g_cols):
            gx0, gy0 = gc * gcw, gr * gch
            gx1, gy1 = gx0 + gcw, gy0 + gch
            gxm = 0.5 * (gx0 + gx1)
            gym = 0.5 * (gy0 + gy1)
            if (gr + gc) % 2 == 0:
                draw_g.polygon([(gx0, gy1), (gxm, gy0), (gx1, gy1)], fill=frosted, outline=(42, 48, 52, 240))
                draw_g.polygon([(gx0, gy0), (gxm, gym), (gx0, gy1)], fill=semi_frost, outline=(42, 48, 52, 240))
            else:
                draw_g.polygon([(gx0, gy0), (gx1, gy0), (gxm, gy1)], fill=frosted, outline=(42, 48, 52, 240))
                draw_g.polygon([(gx1, gy0), (gx1, gy1), (gxm, gym)], fill=semi_frost, outline=(42, 48, 52, 240))
        draw_g.line([(0, gr * gch), (gw, gr * gch)], fill=(195, 190, 180, 240), width=3)
    glass_path = os.path.join(TEX_DIR, "block5_patterned_glass.png")
    img_g.save(glass_path)

    # 6. Crop real framed artworks from Block 5 photos
    p_rope = Image.open(os.path.join(PHOTO_B5_DIR, "WhatsApp Image 2026-10-27 at 14.30.44.jpeg"))
    wr, hr = p_rope.size
    art_rope = p_rope.crop((int(wr * 0.755), int(hr * 0.318), int(wr * 0.880), int(hr * 0.545)))
    art_rope_path = os.path.join(TEX_DIR, "block5_art_rope.png")
    art_rope.save(art_rope_path)

    p_shoes = Image.open(os.path.join(PHOTO_B5_DIR, "WhatsApp Image 2026-10-27 at 14.30.45.jpeg"))
    ws, hs = p_shoes.size
    art_shoes = p_shoes.crop((int(ws * 0.356), int(hs * 0.178), int(ws * 0.415), int(hs * 0.318)))
    art_shoes_path = os.path.join(TEX_DIR, "block5_art_shoes.png")
    art_shoes.save(art_shoes_path)

    # 7. Crisp Single Fornasetti Plate Texture (cropped from Photo 14.30.44 (1).jpeg + porcelain rim)
    p_niche = Image.open(os.path.join(PHOTO_B5_DIR, "WhatsApp Image 2026-10-27 at 14.30.44 (1).jpeg"))
    wn, hn = p_niche.size
    plate_crop = p_niche.crop((int(wn * 0.722), int(hn * 0.344), int(wn * 0.766), int(hn * 0.432))).resize((512, 512), Image.Resampling.LANCZOS)
    draw_p = ImageDraw.Draw(plate_crop)
    draw_p.ellipse([4, 4, 507, 507], outline=(228, 224, 216), width=14)
    draw_p.ellipse([18, 18, 493, 493], outline=(32, 34, 36), width=6)
    plate_single_path = os.path.join(TEX_DIR, "block5_fornasetti_plate.png")
    plate_crop.save(plate_single_path)

    return {
        "carpet": carpet_path,
        "wood_plank": wood_path,
        "light_oak": oak_path,
        "dark_wood": dk_path,
        "ivory_shell": ivory_shell_path,
        "teal_leather": teal_leather_path,
        "sage_wall": sage_wall_path,
        "sofa_sage": sofa_sage_path,
        "murano_green": murano_green_path,
        "murano_amber": murano_amber_path,
        "patterned_glass": glass_path,
        "art_rope": art_rope_path,
        "art_shoes": art_shoes_path,
        "plate_single": plate_single_path,
        "contact_ao": contact_ao_path,
    }

if "--gen-tex" in sys.argv:
    generate_block5_textures()
    sys.exit(0)

subprocess.run(["python3", __file__, "--gen-tex"], check=True)
tex_paths = {
    "carpet": os.path.join(TEX_DIR, "block5_green_carpet.png"),
    "wood_plank": os.path.join(TEX_DIR, "block5_wood_plank.png"),
    "light_oak": os.path.join(TEX_DIR, "block5_light_oak.png"),
    "dark_wood": os.path.join(TEX_DIR, "block5_dark_wood_top.png"),
    "ivory_shell": os.path.join(TEX_DIR, "block5_chair_ivory_shell.png"),
    "teal_leather": os.path.join(TEX_DIR, "block5_chair_teal_leather.png"),
    "sage_wall": os.path.join(TEX_DIR, "block5_sage_wall_panel.png"),
    "sofa_sage": os.path.join(TEX_DIR, "block5_sofa_sage_leather.png"),
    "murano_green": os.path.join(TEX_DIR, "block5_murano_green.png"),
    "murano_amber": os.path.join(TEX_DIR, "block5_murano_amber.png"),
    "patterned_glass": os.path.join(TEX_DIR, "block5_patterned_glass.png"),
    "art_rope": os.path.join(TEX_DIR, "block5_art_rope.png"),
    "art_shoes": os.path.join(TEX_DIR, "block5_art_shoes.png"),
    "plate_single": os.path.join(TEX_DIR, "block5_fornasetti_plate.png"),
    "contact_ao": os.path.join(TEX_DIR, "block5_contact_ao.png"),
}

import bpy
import bmesh
from mathutils import Vector, Euler

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
scene = bpy.context.scene
scene_col = scene.collection

# ==============================================================================
# 1. COLLECTIONS, HELPERS & MATERIALS FOR BLOCK 5 (GREEN ZONE)
# ==============================================================================
def get_or_create_collection(name, parent=None):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        scene_col.children.link(col)
    else:
        parent.children.link(col)
    return col

def link_to_collection(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

def apply_box_uv(obj, scale_per_meter=1.0):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    verts = me.vertices
    for poly in me.polygons:
        nx, ny, nz = abs(poly.normal.x), abs(poly.normal.y), abs(poly.normal.z)
        for loop_idx in poly.loop_indices:
            v = obj.location + verts[me.loops[loop_idx].vertex_index].co
            if nz >= nx and nz >= ny:
                u, w = v.y * scale_per_meter, v.x * scale_per_meter
            elif ny >= nx and ny >= nz:
                u, w = v.x * scale_per_meter, v.z * scale_per_meter
            else:
                u, w = v.y * scale_per_meter, v.z * scale_per_meter
            uv_layer[loop_idx].uv = (u, w)

def apply_normalized_top_uv(obj):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx = max(max_x - min_x, 1e-4)
    dy = max(max_y - min_y, 1e-4)
    for poly in me.polygons:
        for loop_idx in poly.loop_indices:
            v = me.vertices[me.loops[loop_idx].vertex_index].co
            u = (v.y - min_y) / dy
            w = (v.x - min_x) / dx
            uv_layer[loop_idx].uv = (u, w)

def apply_normalized_face_uv(obj):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)
    for poly in me.polygons:
        for loop_idx in poly.loop_indices:
            v = me.vertices[me.loops[loop_idx].vertex_index].co
            if dx >= dy:
                u = (v.x - min(xs)) / max(dx, 1e-4)
            else:
                u = (v.y - min(ys)) / max(dy, 1e-4)
            w = (v.z - min(zs)) / max(dz, 1e-4)
            uv_layer[loop_idx].uv = (u, w)

def apply_cylinder_cap_uv(obj):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx = max(max_x - min_x, 1e-4)
    dy = max(max_y - min_y, 1e-4)
    for poly in me.polygons:
        for loop_idx in poly.loop_indices:
            v = me.vertices[me.loops[loop_idx].vertex_index].co
            u = (v.y - min_y) / dy
            w = 1.0 - (v.x - min_x) / dx
            uv_layer[loop_idx].uv = (u, w)

def add_box(name, size, location, mat, col, bevel=0.0, rot=(0, 0, 0), uv_metric=None):
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if bevel > 0.0:
        bmesh.ops.bevel(bm, geom=bm.edges, offset=bevel, segments=2, profile=0.5, affect='EDGES')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    if uv_metric is not None:
        apply_box_uv(obj, uv_metric)
    link_to_collection(obj, col)
    return obj

def add_cylinder(name, radius, depth, location, mat, col, vertices=32, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=vertices, radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    return obj

def make_textured_mat(name, img_path, roughness=0.45, metallic=0.0, alpha_tex=False, coat=0.0, emission_strength=0.0, bump_strength=0.0, bump_dist=0.008):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(img_path, check_existing=True)
    img.reload()
    img.pack()
    tex.image = img
    nt.links.new(bsdf.inputs["Base Color"], tex.outputs["Color"])
    if bump_strength > 0.0:
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = bump_dist
        nt.links.new(bump.inputs["Height"], tex.outputs["Color"])
        nt.links.new(bsdf.inputs["Normal"], bump.outputs["Normal"])
    if emission_strength > 0.0 and "Emission Color" in bsdf.inputs:
        nt.links.new(bsdf.inputs["Emission Color"], tex.outputs["Color"])
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha_tex and "Alpha" in bsdf.inputs:
        nt.links.new(bsdf.inputs["Alpha"], tex.outputs["Alpha"])
        mat.blend_method = 'BLEND'
    else:
        mat.blend_method = 'OPAQUE'
    nt.links.new(out.inputs["Surface"], bsdf.outputs["BSDF"])
    return mat

def make_solid_mat(name, color, roughness=0.4, metallic=0.0, emission_color=None, emission_strength=0.0, alpha=1.0, coat=0.0):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        mat.node_tree.nodes.clear()
        out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        mat.node_tree.links.new(out.inputs["Surface"], bsdf.outputs["BSDF"])
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    if alpha < 1.0 and "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = 'BLEND'
    if emission_color and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission_color
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

# Clean up any previous Block 5 objects if re-running
remove_b5_prefixes = (
    "B5_",
    "Floor_Block5_",
    "Ceiling_Block5_",
    "Niche_B3_",
    "Niche_B4_",
    "TableTop_319", "TableSubTop_319", "PedBase_319", "PedCol_319", "Chair_319",
    "TableTop_317", "TableSubTop_317", "PedBase_317", "PedCol_317", "Chair_317",
    "TableTop_385", "TableSubTop_385", "PedBase_385", "PedCol_385", "Chair_385",
    "TableTop_387", "TableSubTop_387", "PedBase_387", "PedCol_387", "Chair_387",
    "TableTop_415", "TableSubTop_415", "PedBase_415", "PedCol_415", "Chair_415",
    "TableTop_480", "TableSubTop_480", "PedBase_480", "PedCol_480", "Chair_480",
    "TableTop_450", "TableSubTop_450", "PedBase_450", "PedCol_450", "Chair_450",
    "TableTop_448", "TableSubTop_448", "PedBase_448", "PedCol_448", "Chair_448",
    "TableTop_400", "TableSubTop_400", "PedBase_400", "PedCol_400", "Chair_400",
    "TableTop_398", "TableSubTop_398", "PedBase_398", "PedCol_398", "Chair_398",
    "TableTop_321", "TableSubTop_321", "PedBase_321", "PedCol_321", "Chair_321",
    "TableTop_323", "TableSubTop_323", "PedBase_323", "PedCol_323", "Chair_323",
    "TableTop_327", "TableSubTop_327", "PedBase_327", "PedCol_327", "Chair_327",
    "TableTop_325", "TableSubTop_325", "PedBase_325", "PedCol_325", "Chair_325",
    "TableTop_329", "TableSubTop_329", "PedBase_329", "PedCol_329", "Chair_329",
    "TableTop_331", "TableSubTop_331", "PedBase_331", "PedCol_331", "Chair_331",
    "TableTop_404", "TableSubTop_404", "PedBase_404", "PedCol_404", "Chair_404",
    "TableTop_402", "TableSubTop_402", "PedBase_402", "PedCol_402", "Chair_402",
    "TableTop_406", "TableSubTop_406", "PedBase_406", "PedCol_406", "Chair_406",
    "TableTop_408", "TableSubTop_408", "PedBase_408", "PedCol_408", "Chair_408",
    "TableTop_412", "TableSubTop_412", "PedBase_412", "PedCol_412", "Chair_412",
    "TableTop_410", "TableSubTop_410", "PedBase_410", "PedCol_410", "Chair_410",
    "TableTop_383", "TableSubTop_383", "PedBase_383", "PedCol_383", "Chair_383",
    "TableTop_417", "TableSubTop_417", "PedBase_417", "PedCol_417", "Chair_417",
    "TableTop_482", "TableSubTop_482", "PedBase_482", "PedCol_482", "Chair_482",
    "TableTop_446", "TableSubTop_446", "PedBase_446", "PedCol_446", "Chair_446",
    "TableTop_381", "TableSubTop_381", "PedBase_381", "PedCol_381", "Chair_381",
    "TableTop_379", "TableSubTop_379", "PedBase_379", "PedCol_379", "Chair_379",
    "TableTop_444", "TableSubTop_444", "PedBase_444", "PedCol_444", "Chair_444",
    "TableTop_442", "TableSubTop_442", "PedBase_442", "PedCol_442", "Chair_442",
    "TableTop_419", "TableSubTop_419", "PedBase_419", "PedCol_419", "Chair_419",
    "TableTop_484", "TableSubTop_484", "PedBase_484", "PedCol_484", "Chair_484",
)
for obj in list(bpy.data.objects):
    if obj.name.startswith(remove_b5_prefixes):
        bpy.data.objects.remove(obj, do_unlink=True)

arch_col = get_or_create_collection("01_Architecture_Deck6_Arlecchino")
light_col = get_or_create_collection("04_Lighting")
furn_col_b5 = get_or_create_collection("06_Furniture_Block5_GreenZone")

mats = {
    "wall_white": make_solid_mat("Mat_Block5_Arch_WarmWhite", (0.46, 0.43, 0.38, 1.0), roughness=0.46),
    "wall_red": bpy.data.materials.get("Mat_Wainscot_Venetian_Red"),
    "dark_marble": bpy.data.materials.get("Mat_Emperador_Dark_Marble"),
    "black_metal": bpy.data.materials.get("Mat_Black_Powder_Steel"),
    "wood_walnut": bpy.data.materials.get("Mat_Dark_Walnut_Wood"),
    "brass": bpy.data.materials.get("Mat_Polished_Brass"),
    "chrome": bpy.data.materials.get("Mat_Polished_Chrome"),
    "led_warm": bpy.data.materials.get("Mat_LED_Warm_2700K"),
    "window_daylight": bpy.data.materials.get("Mat_Window_Sea_Daylight"),
    "window_glass": bpy.data.materials.get("Mat_Marine_Window_Glass"),
    "plates_wall": bpy.data.materials.get("Mat_Plates_Wall"),
    "exit_green": bpy.data.materials.get("Mat_Exit_Sign_Green"),
    "art_1": bpy.data.materials.get("Mat_Framed_Art_1"),
    "art_2": bpy.data.materials.get("Mat_Framed_Art_2"),
    "art_3": bpy.data.materials.get("Mat_Framed_Art_3"),
    # Block 5 Dedicated Materials (Calibrated Linear RGB + Self-Occlusion & Bump Normal Maps)
    "b5_green_carpet": make_textured_mat("Mat_Block5_Green_Carpet", tex_paths["carpet"], roughness=0.88, bump_strength=0.14, bump_dist=0.012),
    "b5_wood_floor": make_textured_mat("Mat_Block5_Wood_Plank_Floor", tex_paths["wood_plank"], roughness=0.35, coat=0.18, bump_strength=0.12, bump_dist=0.010),
    "b5_light_oak": make_textured_mat("Mat_Block5_Light_Oak_Wood", tex_paths["light_oak"], roughness=0.28, coat=0.35, bump_strength=0.08, bump_dist=0.008),
    "b5_dark_wood_top": make_textured_mat("Mat_Block5_Dark_Wood_Tabletop", tex_paths["dark_wood"], roughness=0.22, coat=0.45, bump_strength=0.06, bump_dist=0.006),
    "b5_patterned_glass": make_textured_mat("Mat_Block5_Patterned_Glass", tex_paths["patterned_glass"], roughness=0.28, alpha_tex=True, coat=0.12, bump_strength=0.06),
    "b5_art_rope": make_textured_mat("Mat_Block5_Art_Rope", tex_paths["art_rope"], roughness=0.32),
    "b5_art_shoes": make_textured_mat("Mat_Block5_Art_Shoes", tex_paths["art_shoes"], roughness=0.32),
    "b5_plate_single": make_textured_mat("Mat_Block5_Fornasetti_Plate", tex_paths["plate_single"], roughness=0.16, coat=0.6),
    "b5_sage_wall": make_textured_mat("Mat_Block5_Sage_Wall", tex_paths["sage_wall"], roughness=0.58, bump_strength=0.07, bump_dist=0.008),
    "b5_turquoise_wall": make_solid_mat("Mat_Block5_Turquoise_Wall", (0.008, 0.11, 0.16, 1.0), roughness=0.32, coat=0.25),
    "b5_teal_metal": make_solid_mat("Mat_Block5_Teal_Metal_Grille", (0.015, 0.12, 0.14, 1.0), roughness=0.28, metallic=0.72),
    "b5_teal_leather": make_textured_mat("Mat_Block5_Teal_Leather", tex_paths["teal_leather"], roughness=0.30, coat=0.22, bump_strength=0.08, bump_dist=0.006),
    "b5_ivory_shell": make_textured_mat("Mat_Block5_Ivory_Shell", tex_paths["ivory_shell"], roughness=0.34, coat=0.18, bump_strength=0.06, bump_dist=0.006),
    "b5_sofa_sage": make_textured_mat("Mat_Block5_Sofa_Sage_Leather", tex_paths["sofa_sage"], roughness=0.36, coat=0.18, bump_strength=0.07, bump_dist=0.006),
    "b5_Bronze_Ped": make_solid_mat("Mat_Block5_Bronze_Pedestal", (0.055, 0.040, 0.028, 1.0), roughness=0.26, metallic=0.82),
    "b5_black_marble_pillar": make_solid_mat("Mat_Block5_Black_Marble_Pillar", (0.018, 0.018, 0.022, 1.0), roughness=0.10, coat=0.95),
    "b5_teal_blind": make_solid_mat("Mat_Block5_Teal_Roman_Blind", (0.025, 0.085, 0.12, 1.0), roughness=0.68),
    "b5_pendant_green": make_textured_mat(
        "Mat_Block5_Murano_Pendant_Green",
        tex_paths["murano_green"], roughness=0.04, metallic=0.10, alpha_tex=False, coat=1.0, emission_strength=0.16, bump_strength=0.10
    ),
    "b5_pendant_amber": make_textured_mat(
        "Mat_Block5_Murano_Pendant_Amber",
        tex_paths["murano_amber"], roughness=0.04, metallic=0.12, alpha_tex=False, coat=1.0, emission_strength=0.16, bump_strength=0.10
    ),
    "b5_glass_shelf": make_solid_mat("Mat_Block5_Glass_Shelf", (0.55, 0.68, 0.65, 1.0), roughness=0.05, alpha=0.42, coat=1.0),
    "coffer_dark": make_solid_mat("Mat_Block5_Coffer_Charcoal_Slate", (0.032, 0.030, 0.028, 1.0), roughness=0.58),
    "coffer_rib": make_solid_mat("Mat_Block5_Coffer_Rib_Dark", (0.018, 0.017, 0.016, 1.0), roughness=0.40, metallic=0.28),
    "mirror_chrome": make_solid_mat("Mat_Block5_Ceiling_DarkChrome", (0.24, 0.25, 0.27, 1.0), roughness=0.06, metallic=0.94),
    "aft_gallery_dark": make_solid_mat("Mat_Block5_Aft_Gallery_Shadow", (0.045, 0.052, 0.048, 1.0), roughness=0.62),
    "vase_ruby": make_solid_mat("Mat_Vase_Ruby_Glass", (0.48, 0.04, 0.10, 1.0), roughness=0.08, coat=1.0),
    "vase_amber": make_solid_mat("Mat_Vase_Amber_Gold", (0.58, 0.34, 0.08, 1.0), roughness=0.12, metallic=0.35, coat=0.8),
    "vase_harlequin": make_solid_mat("Mat_Vase_Harlequin_Yellow", (0.68, 0.48, 0.10, 1.0), roughness=0.25),
    "vase_smoked": make_solid_mat("Mat_Vase_Smoked_Grey", (0.14, 0.16, 0.18, 1.0), roughness=0.10, coat=0.9),
    "niche_smoked_glass": make_solid_mat("Mat_Block5_Niche_SmokedGlass", (0.04, 0.05, 0.06, 1.0), roughness=0.08, alpha=0.36, coat=0.9),
    "b5_contact_ao": make_textured_mat("Mat_Block5_Contact_AO", tex_paths["contact_ao"], roughness=1.0, alpha_tex=True),
}

CEIL_H = 2.78
COFFER_H = 2.96
B34_AFT_WALL_X = 27.350
B5_FWD_WALL_X  = 28.150
B5_GLASS_WALL_X = 37.800
B5_AFT_WALL_X   = 41.200
ROOM_TOTAL_Y    = 17.460
CLOVER_CY       = 8.730

plate_offsets = [
    (-0.36,  0.34, 0.13), (0.0,  0.40, 0.15), (0.36,  0.34, 0.13),
    (-0.38,  0.00, 0.15), (0.0,  0.00, 0.17), (0.38,  0.00, 0.15),
    (-0.34, -0.35, 0.13), (0.0, -0.39, 0.14), (0.34, -0.35, 0.13),
]

# ==============================================================================
# 2. MODIFY BLOCK 3 & BLOCK 4 AFT BOUNDARY (X = 27.35m .. 28.15m)
#    - Open the Central Corridor into Block 5 (per Photo 14.31.16 (2).jpeg)
#    - Cut see-through decorative vase niches above Block 3 & Block 4 Waiter Stations
#      (per Photos 14.30.44 (1).jpeg, 14.31.15 (2).jpeg, 14.31.16.jpeg, 14.31.16 (1).jpeg)
# ==============================================================================
# 2A. Remove temporary corridor end wall at X = 28.15m so Central Corridor opens into Block 5!
for rot_name in ("B3B4_Rotunda_EndWall_Upper", "B3B4_Rotunda_EndWall_Red"):
    obj = bpy.data.objects.get(rot_name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

# Add white service doors & handles on the left/right walls of the short corridor passage (X = 25.90..28.15m)
# plus the overhead green EXIT sign at X = 28.10m (matching Photo 14.31.16 (2).jpeg!)
for side_tag, dy_wall, in_sign in [("Port", 7.58, 1.0), ("Stbd", 9.88, -1.0)]:
    add_box(f"B5_CorrPassage_DoorFrame_{side_tag}", (0.72, 0.025, 2.08), (27.15, dy_wall + in_sign * 0.005, 1.04), mats["wall_white"], arch_col, bevel=0.003)
    add_box(f"B5_CorrPassage_DoorLeaf_{side_tag}",  (0.66, 0.015, 2.02), (27.15, dy_wall + in_sign * 0.012, 1.01), mats["wall_white"], arch_col)
    add_box(f"B5_CorrPassage_DoorHandle_{side_tag}",(0.08, 0.035, 0.02), (26.88, dy_wall + in_sign * 0.025, 1.02), mats["chrome"],     arch_col)
    add_box(f"B5_CorrPassage_ExitPlaque_{side_tag}",(0.22, 0.015, 0.32), (27.15, dy_wall + in_sign * 0.020, 1.62), mats["exit_green"], arch_col)

add_box("B5_CorrExitSign_Frame", (0.05, 0.42, 0.13), (28.12, CLOVER_CY, 2.70), mats["wall_white"], arch_col)
add_box("B5_CorrExitSign_Panel", (0.06, 0.38, 0.10), (28.12, CLOVER_CY, 2.70), mats["exit_green"], arch_col)

# 2B. Replace solid AlcoveBackWall & AlcoveHeader of Block 3 & Block 4 Aft Waiter Stations
# with Lower Backing Wall (Z = 0.00..1.16m) + See-Through Display Niche (Z = 1.16..2.40m) + Upper Header (Z = 2.40..2.78m)!
for ws_tag in ("B3_WaiterStation_1_Rect7", "B4_WaiterStation_1_Rect86"):
    for suffix in ("_AlcoveBackWall", "_AlcoveHeader"):
        old_obj = bpy.data.objects.get(ws_tag + suffix)
        if old_obj:
            bpy.data.objects.remove(old_obj, do_unlink=True)

def build_see_through_vase_niche(niche_tag, y0, y1):
    """
    Builds the see-through decorative wall niche ('dinding bolong berhias vas & pajangan')
    between Block 3/4 (X = 27.35m) and Block 5 Forward Sofa Wall (X = 28.15m).
    Spans Y = [y0, y1], open from Z = 1.16m to Z = 2.40m.
    """
    n_len = y1 - y0  # 3.08m
    n_cy = 0.5 * (y0 + y1)
    x_mid = 0.5 * (B34_AFT_WALL_X + B5_FWD_WALL_X)  # 27.75m
    depth_x = B5_FWD_WALL_X - B34_AFT_WALL_X        # 0.80m

    # 1. Lower Solid Wall behind Waiter Station & Sofa (Z = 0.00 .. 1.16m, X = 27.96 .. 28.15m)
    add_box(f"{niche_tag}_LowerSolidWall", (0.19, n_len + 0.04, 1.16), (28.055, n_cy, 0.58), mats["wall_white"], arch_col)

    # 2. Upper Solid Header Wall above Niche (Z = 2.40 .. 2.86m, spanning full depth X = 27.35 .. 28.15m)
    add_box(f"{niche_tag}_UpperHeaderWall", (depth_x, n_len + 0.04, 0.46), (x_mid, n_cy, 2.63), mats["wall_white"], arch_col)
    uh_s = add_box(f"{niche_tag}_UpperSagePanel", (0.016, n_len - 0.12, 0.28), (B5_FWD_WALL_X + 0.008, n_cy, 2.57), mats["b5_sage_wall"], arch_col)
    apply_normalized_face_uv(uh_s)
    add_box(f"{niche_tag}_UpperCrown", (0.045, n_len + 0.04, 0.08), (B5_FWD_WALL_X + 0.015, n_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.005)

    # 3. Niche Sill (Z = 1.15..1.18m) & Niche Ceiling Soffit (Z = 2.38..2.41m) & Frame Jambs
    niche_x_center = 27.96
    niche_frame_depth = 0.36
    add_box(f"{niche_tag}_Sill",   (niche_frame_depth, n_len, 0.035), (niche_x_center, n_cy, 1.165), mats["wall_white"], arch_col, bevel=0.004)
    add_box(f"{niche_tag}_Soffit", (niche_frame_depth, n_len, 0.035), (niche_x_center, n_cy, 2.395), mats["wall_white"], arch_col, bevel=0.004)

    # Subtle tinted glass backing pane inside the see-through niche for rich depth & reflections while keeping Block 3/4 visible
    add_box(f"{niche_tag}_SmokedPane", (0.008, n_len - 0.06, 1.19), (niche_x_center - 0.14, n_cy, 1.78), mats["niche_smoked_glass"], arch_col)

    # Vertical White Dividers (6 bays: center structural post + 5 thin frame mullions)
    n_bays = 6
    bay_w = n_len / n_bays
    niche_h = 2.38 - 1.18  # 1.20m clear height
    niche_cz = 1.18 + niche_h * 0.5
    for b_i in range(n_bays + 1):
        by = y0 + b_i * bay_w
        post_w = 0.055 if b_i in (0, 3, 6) else 0.026
        add_box(f"{niche_tag}_Mullion_{b_i}", (niche_frame_depth - 0.02, post_w, niche_h), (niche_x_center, by, niche_cz), mats["wall_white"], arch_col, bevel=0.003)

    # 2 Horizontal Glass Shelves + Thin White Guard Rails (at Z = 1.56m and Z = 1.98m)
    for s_idx, sz in enumerate((1.56, 1.98)):
        add_box(f"{niche_tag}_GlassShelf_{s_idx}", (niche_frame_depth - 0.06, n_len - 0.04, 0.012), (niche_x_center, n_cy, sz), mats["b5_glass_shelf"], arch_col)
        for rail_dx in (-0.13, 0.13):
            add_box(f"{niche_tag}_GuardRail_{s_idx}_{rail_dx:.2f}", (0.008, n_len - 0.04, 0.008), (niche_x_center + rail_dx, n_cy, sz + 0.035), mats["wall_white"], arch_col)

    # Populate all 6 bays x 3 shelf levels with colorful Murano Vases, Striped Bowls & Harlequin Boxes!
    vase_mats = [mats["vase_ruby"], mats["vase_amber"], mats["vase_harlequin"], mats["vase_smoked"], mats["b5_pendant_green"]]
    shelf_zs = [1.18, 1.57, 1.99]
    for b_i in range(n_bays):
        bay_cy = y0 + (b_i + 0.5) * bay_w
        # Top pin-spot LED in each bay
        add_cylinder(f"{niche_tag}_Spot_{b_i}", 0.025, 0.008, (niche_x_center, bay_cy, 2.375), mats["led_warm"], arch_col)
        for s_i, sz in enumerate(shelf_zs):
            v_mat = vase_mats[(b_i * 3 + s_i) % len(vase_mats)]
            # Item 1 (left of bay): Tall slender bottle or bulbous vase
            y_item1 = bay_cy - bay_w * 0.22
            if (b_i + s_i) % 2 == 0:
                add_cylinder(f"{niche_tag}_VaseBody_{b_i}_{s_i}", 0.055, 0.18, (niche_x_center, y_item1, sz + 0.09), v_mat, arch_col)
                add_cylinder(f"{niche_tag}_VaseNeck_{b_i}_{s_i}", 0.022, 0.12, (niche_x_center, y_item1, sz + 0.22), v_mat, arch_col)
            else:
                add_cylinder(f"{niche_tag}_HarlequinBox_{b_i}_{s_i}", 0.075, 0.16, (niche_x_center, y_item1, sz + 0.08), mats["vase_harlequin"], arch_col)
                add_cylinder(f"{niche_tag}_HarlequinLid_{b_i}_{s_i}", 0.078, 0.025, (niche_x_center, y_item1, sz + 0.17), mats["wall_red"], arch_col)
            # Item 2 (right of bay): Decorative bowl or goblet
            y_item2 = bay_cy + bay_w * 0.22
            v_mat2 = vase_mats[(b_i + s_i * 2 + 1) % len(vase_mats)]
            add_cylinder(f"{niche_tag}_Bowl_{b_i}_{s_i}", 0.068, 0.11, (niche_x_center, y_item2, sz + 0.055), v_mat2, arch_col)

build_see_through_vase_niche("Niche_B3_Port", 2.25, 5.33)
build_see_through_vase_niche("Niche_B4_Stbd", 12.13, 15.21)

# ==============================================================================
# 3. BLOCK 5 FLOORS: GREEN ARLECCHINO CARPET + SURROUNDING WOOD PLANK WALKWAY
#    (4 Non-Overlapping Wood Slabs + 1 Center Carpet Slab = ZERO Z-FIGHTING!)
# ==============================================================================
CARPET_X0, CARPET_X1 = 30.650, B5_GLASS_WALL_X  # 30.65m .. 37.80m (len = 7.15m)
CARPET_Y0, CARPET_Y1 = 3.360,  14.100           # 3.36m .. 14.10m  (wid = 10.74m)

carpet_obj = add_box(
    "Floor_Block5_Green_Carpet",
    (CARPET_X1 - CARPET_X0, CARPET_Y1 - CARPET_Y0, 0.04),
    (0.5 * (CARPET_X0 + CARPET_X1), 0.5 * (CARPET_Y0 + CARPET_Y1), -0.02),
    mats["b5_green_carpet"],
    arch_col,
)
apply_normalized_top_uv(carpet_obj)

wood_slabs = [
    ("Floor_Block5_Wood_Fwd",  B5_FWD_WALL_X, CARPET_X0,     0.000,     ROOM_TOTAL_Y),
    ("Floor_Block5_Wood_Port", CARPET_X0,     CARPET_X1,     0.000,     CARPET_Y0),
    ("Floor_Block5_Wood_Stbd", CARPET_X0,     CARPET_X1,     CARPET_Y1, ROOM_TOTAL_Y),
    ("Floor_Block5_Wood_Aft",  CARPET_X1,     B5_AFT_WALL_X, 0.000,     ROOM_TOTAL_Y),
]
for w_name, wx0, wx1, wy0, wy1 in wood_slabs:
    add_box(
        w_name,
        (wx1 - wx0, wy1 - wy0, 0.04),
        (0.5 * (wx0 + wx1), 0.5 * (wy0 + wy1), -0.02),
        mats["b5_wood_floor"],
        arch_col,
        uv_metric=0.45,
    )

# ==============================================================================
# 4. BLOCK 5 FORWARD SOFA WALLS, BANQUETTE SOFAS & 9 FORNASETTI PLATES ON BACK
#    (Portside: Y = 0.00..7.58m; Starboardside: Y = 9.88..17.46m at X = 28.15m)
# ==============================================================================
def build_b5_forward_sofa_wall(side_tag, y_start, y_end, niche_y0, niche_y1, plates_cy):
    """
    Builds the Forward wall cladding of Block 5 at X = 28.15m around the see-through vase niche,
    adds the 9 Fornasetti Plates on the solid outer wall segment (facing +X into Block 5!),
    and builds the continuous wooden-slat + sage-leatherette banquette sofa with pitch-black
    recessed shadow backing & vertical bolted metal stiles (matching Photo 14.30.44 (1).jpeg!).
    """
    total_y = y_end - y_start
    mid_y = 0.5 * (y_start + y_end)

    # Solid wall segment 1 (from y_start to niche_y0) & segment 2 (from niche_y1 to y_end)
    for seg_i, (sy0, sy1) in enumerate([(y_start, niche_y0), (niche_y1, y_end)]):
        slen = sy1 - sy0
        scy = 0.5 * (sy0 + sy1)
        # Backing wall fill from Block 3/4 wall to X = 28.15m
        add_box(f"B5_FwdWall_Solid_{side_tag}_{seg_i}", (0.16, slen, CEIL_H), (B5_FWD_WALL_X - 0.08, scy, CEIL_H * 0.5), mats["wall_white"], arch_col)
        # Sage grey-green upper wall panel framed by white stiles (Z = 1.16..2.65m)
        sp = add_box(f"B5_FwdWall_SagePanel_{side_tag}_{seg_i}", (0.015, slen - 0.14, 1.44), (B5_FWD_WALL_X + 0.008, scy, 1.90), mats["b5_sage_wall"], arch_col)
        apply_normalized_face_uv(sp)
        add_box(f"B5_FwdWall_Crown_{side_tag}_{seg_i}", (0.045, slen, 0.08), (B5_FWD_WALL_X + 0.015, scy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.005)

    # 9 Fornasetti Plates facing Block 5 (+X) on the solid outer wall segment (behind 319/317 on Portside, and behind 400/398 on Starboardside!)
    for p_i, (dy, dz, prad) in enumerate(plate_offsets):
        # Dark shadow backing ring behind each plate so it pops off the sage wall
        add_cylinder(
            f"B5_Fwd_{side_tag}_PlateShadow_{p_i}",
            radius=prad * 1.03,
            depth=0.014,
            location=(B5_FWD_WALL_X + 0.018, plates_cy + dy, 1.78 + dz),
            mat=mats["black_metal"],
            col=arch_col,
            rot=(0, math.pi * 0.5, 0),
        )
        p_obj = add_cylinder(
            f"B5_Fwd_{side_tag}_Plate_{p_i}",
            radius=prad,
            depth=0.025,
            location=(B5_FWD_WALL_X + 0.026, plates_cy + dy, 1.78 + dz),
            mat=mats["b5_plate_single"],
            col=arch_col,
            rot=(0, math.pi * 0.5, 0),
        )
        apply_cylinder_cap_uv(p_obj)

    # Also ensure the 9 Fornasetti Plates on the opposite side of this wall (facing Block 3 / Block 4) use the crisp single plate UV & material!
    opp_prefix = "B3_Aft_Plate_" if side_tag == "Port" else "B4_Aft_Plate_"
    for p_i in range(9):
        opp_plate = bpy.data.objects.get(f"{opp_prefix}{p_i}")
        if opp_plate:
            opp_plate.data.materials.clear()
            opp_plate.data.materials.append(mats["b5_plate_single"])
            apply_cylinder_cap_uv(opp_plate)

    # Continuous Chair Rail at Z = 1.14m across the full width [y_start, y_end]
    add_box(f"B5_FwdWall_ChairRail_{side_tag}", (0.045, total_y, 0.055), (B5_FWD_WALL_X + 0.018, mid_y, 1.135), mats["wall_white"], arch_col, bevel=0.005)

    # Continuous Banquette Sofa (X = 28.15m .. 28.77m):
    # - Dark Recessed Toe-Kick Plinth (Z = 0.00 .. 0.055m)
    # - Light Oak Plinth Base (Z = 0.055 .. 0.36m)
    # - Sage-Green Leatherette Seat Cushion (Z = 0.36 .. 0.47m)
    # - Pitch-Black Shadow Backing Panel + Vertical Black Bolted Metal Stiles (Z = 0.47 .. 1.10m)
    # - 5 Horizontal Slatted Light Oak Backrest Rails (Z = 0.47 .. 1.08m)
    sofa_len = total_y - 0.16
    add_box(f"B5_FwdSofa_ToeKick_{side_tag}", (0.52, sofa_len, 0.055), (B5_FWD_WALL_X + 0.26, mid_y, 0.0275), mats["black_metal"], arch_col)
    sb = add_box(f"B5_FwdSofa_Base_{side_tag}", (0.58, sofa_len, 0.305), (B5_FWD_WALL_X + 0.29, mid_y, 0.2075), mats["b5_light_oak"], arch_col, bevel=0.008, uv_metric=0.6)
    apply_normalized_face_uv(sb)
    ss = add_box(f"B5_FwdSofa_Seat_{side_tag}", (0.62, sofa_len, 0.11), (B5_FWD_WALL_X + 0.31, mid_y, 0.415), mats["b5_sofa_sage"], arch_col, bevel=0.022)
    apply_normalized_face_uv(ss)

    # Pitch-black shadow backing behind the oak slats so dark contrast gaps show between every slat!
    add_box(f"B5_FwdSofa_BlackBacking_{side_tag}", (0.018, sofa_len, 0.64), (B5_FWD_WALL_X + 0.012, mid_y, 0.785), mats["black_metal"], arch_col)

    # Vertical black bolted steel stiles every ~0.74m (matching Photo 14.30.44 (1).jpeg!)
    n_stiles = 10
    for st_i in range(n_stiles + 1):
        sty = (y_start + 0.08) + st_i * (sofa_len / n_stiles)
        add_box(f"B5_FwdSofa_VertStile_{side_tag}_{st_i}", (0.032, 0.036, 0.63), (B5_FWD_WALL_X + 0.022, sty, 0.785), mats["black_metal"], arch_col)

    # 5 horizontal wood slats on the backrest (matching Photos 14.30.44 (1).jpeg & 14.31.15 (2).jpeg!)
    for slat_i in range(5):
        sz = 0.54 + slat_i * 0.115
        sl_obj = add_box(f"B5_FwdSofa_Slat_{side_tag}_{slat_i}", (0.038, sofa_len, 0.084), (B5_FWD_WALL_X + 0.034, mid_y, sz), mats["b5_light_oak"], arch_col, bevel=0.004)
        apply_normalized_face_uv(sl_obj)

build_b5_forward_sofa_wall("Port", 0.08, 7.50, 2.25, 5.33, plates_cy=1.15)
build_b5_forward_sofa_wall("Stbd", 9.96, 17.38, 12.13, 15.21, plates_cy=16.31)

# Add upholstered ivory-with-vertical-stripe back cushions aligned with each sofa table seat
sofa_cushion_ys = [
    # Portside: 319 (1), 317 (2), 385 (1), 387 (2), 415 (1)
    0.65, 1.80, 2.50, 3.80, 5.10, 5.80, 6.95,
    # Starboardside: 480 (1), 450 (2), 448 (1), 400 (2), 398 (1)
    10.51, 11.66, 12.36, 13.66, 14.96, 15.66, 16.81,
]
for c_idx, cy in enumerate(sofa_cushion_ys):
    bc = add_box(f"B5_FwdSofa_BackCushion_{c_idx}", (0.10, 0.54, 0.56), (B5_FWD_WALL_X + 0.082, cy, 0.78), mats["b5_ivory_shell"], arch_col, bevel=0.02)
    apply_normalized_face_uv(bc)
    for stripe_dy in (-0.18, 0.18):
        add_box(f"B5_FwdSofa_CushionStripe_{c_idx}_{stripe_dy:.2f}", (0.105, 0.035, 0.55), (B5_FWD_WALL_X + 0.085, cy + stripe_dy, 0.78), mats["black_metal"], arch_col)

# ==============================================================================
# 5. PORTSIDE WINDOW WALL (Y = 0.00m) & STARBOARDSIDE WALL (Y = 17.46m) IN BLOCK 5
# ==============================================================================
b5_len_x = B5_AFT_WALL_X - B5_FWD_WALL_X  # 13.05m
b5_mid_x = 0.5 * (B5_FWD_WALL_X + B5_AFT_WALL_X)  # 34.675m

# 5A. Portside Outer Hull Window Wall (Y = 0.00m, X = 28.15 .. 41.20m)
add_box("B5_PortHull_Plinth",    (b5_len_x, 0.22, 0.16), (b5_mid_x, -0.08, 0.08),  mats["wall_white"],   arch_col)
ph_sl = add_box("B5_PortHull_SageLower", (b5_len_x, 0.18, 0.68), (b5_mid_x, -0.08, 0.50),  mats["b5_sage_wall"], arch_col)
apply_normalized_face_uv(ph_sl)
add_box("B5_PortHull_ChairRail", (b5_len_x, 0.24, 0.06), (b5_mid_x, -0.07, 0.87),  mats["wall_white"],   arch_col, bevel=0.006)
add_box("B5_PortHull_Header",    (b5_len_x, 0.22, 0.30), (b5_mid_x, -0.08, 2.63),  mats["wall_white"],   arch_col)

b5_port_piers = [
    (28.15, 29.85, False, None),
    (32.55, 33.55, True,  mats["art_2"]),
    (35.65, 36.55, True,  mats["b5_art_shoes"]),
    (38.45, 41.20, False, None),
]
for p_i, (px0, px1, has_art, amat) in enumerate(b5_port_piers):
    pw = px1 - px0
    pcx = 0.5 * (px0 + px1)
    add_box(f"B5_PortPier_White_{p_i}", (pw, 0.22, 1.65), (pcx, -0.05, 1.70), mats["wall_white"], arch_col, bevel=0.004)
    pp_s = add_box(f"B5_PortPier_Sage_{p_i}",  (pw - 0.12, 0.02, 1.50), (pcx, 0.065, 1.70), mats["b5_sage_wall"], arch_col)
    apply_normalized_face_uv(pp_s)
    if has_art and amat:
        add_box(f"B5_PortPier_Frame_{p_i}", (0.62, 0.025, 0.72), (pcx, 0.085, 1.68), mats["brass"], arch_col, bevel=0.004)
        add_box(f"B5_PortPier_Mat_{p_i}",   (0.54, 0.028, 0.64), (pcx, 0.088, 1.68), mats["wall_white"], arch_col)
        ao = add_box(f"B5_PortPier_Art_{p_i}", (0.42, 0.032, 0.52), (pcx, 0.092, 1.68), amat, arch_col)
        apply_normalized_face_uv(ao)
        add_cylinder(f"B5_PortPier_Lamp_{p_i}", 0.012, 0.44, (pcx, 0.15, 2.10), mats["brass"], arch_col, rot=(0, math.pi * 0.5, 0))

b5_port_windows = [(29.85, 32.55), (33.55, 35.65), (36.55, 38.45)]
for w_i, (wx0, wx1) in enumerate(b5_port_windows):
    ww = wx1 - wx0
    wcx = 0.5 * (wx0 + wx1)
    add_box(f"B5_Win_Glass_{w_i}", (ww, 0.015, 1.60), (wcx, -0.12, 1.68), mats["window_glass"], arch_col)
    for m_i in (1, 2):
        mx_mull = wx0 + ww * (m_i / 3.0)
        add_box(f"B5_Win_Mullion_{w_i}_{m_i}", (0.045, 0.06, 1.60), (mx_mull, -0.09, 1.68), mats["wall_white"], arch_col)
    sea_obj = add_box(f"B5_Win_Daylight_{w_i}", (ww + 0.4, 0.02, 1.85), (wcx, -0.50, 1.68), mats["window_daylight"], arch_col)
    apply_normalized_face_uv(sea_obj)
    for f_i, fz in enumerate([2.46, 2.34, 2.22, 2.11]):
        add_box(f"B5_TealBlind_Fold_{w_i}_{f_i}", (ww + 0.06, 0.065, 0.13), (wcx, 0.02 + (f_i % 2) * 0.01, fz), mats["b5_teal_blind"], arch_col, bevel=0.015)

# 5B. Starboardside Inboard Wall (Y = 17.46m, X = 28.15 .. 41.20m)
# Includes the framed Block 6 Access Portal between X = 29.85m and X = 31.65m (per Photo 14.30.44.jpeg)
# and the long Starboard wall (X = 31.65 .. 41.20m) with Sage panels & Gold-framed Artworks (per Photo 14.30.45.jpeg)!
stbd_wall_segs = [(28.15, 29.85), (31.65, 41.20)]
for s_i, (sx0, sx1) in enumerate(stbd_wall_segs):
    sw = sx1 - sx0
    scx = 0.5 * (sx0 + sx1)
    add_box(f"B5_StbdWall_Core_{s_i}",      (sw, 0.20, CEIL_H), (scx, ROOM_TOTAL_Y + 0.10, CEIL_H * 0.5), mats["wall_white"], arch_col)
    add_box(f"B5_StbdWall_Plinth_{s_i}",    (sw, 0.04, 0.16),   (scx, ROOM_TOTAL_Y - 0.01, 0.08),         mats["wall_white"], arch_col)
    sw_l = add_box(f"B5_StbdWall_SageLower_{s_i}", (sw - 0.08, 0.02, 0.68), (scx, ROOM_TOTAL_Y - 0.005, 0.50),   mats["b5_sage_wall"], arch_col)
    apply_normalized_face_uv(sw_l)
    add_box(f"B5_StbdWall_ChairRail_{s_i}", (sw, 0.045, 0.065), (scx, ROOM_TOTAL_Y - 0.012, 0.87),        mats["wall_white"], arch_col, bevel=0.005)
    sw_u = add_box(f"B5_StbdWall_SageUpper_{s_i}", (sw - 0.08, 0.018, 1.68), (scx, ROOM_TOTAL_Y - 0.004, 1.76),  mats["b5_sage_wall"], arch_col)
    apply_normalized_face_uv(sw_u)
    add_box(f"B5_StbdWall_Crown_{s_i}",     (sw, 0.05, 0.08),   (scx, ROOM_TOTAL_Y - 0.015, CEIL_H - 0.04), mats["wall_white"], arch_col)

# Portal Header & Recessed Block 6 Backdrop at X = 29.85..31.65m (between 398/400 and 404/402)
add_box("B5_Block6Portal_Header", (1.80, 0.24, 0.42), (30.75, ROOM_TOTAL_Y + 0.08, CEIL_H - 0.21), mats["wall_white"], arch_col)
add_box("B5_Block6Portal_Jamb_0", (0.08, 0.26, CEIL_H), (29.85, ROOM_TOTAL_Y + 0.08, CEIL_H * 0.5), mats["wall_white"], arch_col)
add_box("B5_Block6Portal_Jamb_1", (0.08, 0.26, CEIL_H), (31.65, ROOM_TOTAL_Y + 0.08, CEIL_H * 0.5), mats["wall_white"], arch_col)
b6_bd = add_box("B5_Block6Portal_Backdrop", (2.00, 0.12, CEIL_H), (30.75, ROOM_TOTAL_Y + 0.65, CEIL_H * 0.5), mats["aft_gallery_dark"], arch_col)
apply_normalized_face_uv(b6_bd)

# Vertical white panel stiles & 2 Gold-Framed Artworks on Starboard Wall (matching Photos 14.30.44 & 14.30.45!)
for stile_x in (31.70, 33.40, 35.10, 36.80, 38.50):
    add_box(f"B5_StbdWall_Stile_{stile_x:.1f}", (0.05, 0.03, 1.72), (stile_x, ROOM_TOTAL_Y - 0.01, 1.76), mats["wall_white"], arch_col)

stbd_art_specs = [
    (32.55, mats["b5_art_rope"]),
    (35.95, mats["b5_art_shoes"]),
]
for a_i, (ax, amat) in enumerate(stbd_art_specs):
    add_box(f"B5_StbdArt_Frame_{a_i}", (0.78, 0.025, 0.88), (ax, ROOM_TOTAL_Y - 0.015, 1.66), mats["brass"], arch_col, bevel=0.004)
    add_box(f"B5_StbdArt_Mat_{a_i}",   (0.68, 0.028, 0.78), (ax, ROOM_TOTAL_Y - 0.018, 1.66), mats["wall_white"], arch_col)
    ao = add_box(f"B5_StbdArt_Pic_{a_i}", (0.52, 0.032, 0.62), (ax, ROOM_TOTAL_Y - 0.022, 1.66), amat, arch_col)
    apply_normalized_face_uv(ao)
    add_cylinder(f"B5_StbdArt_Lamp_{a_i}", 0.012, 0.54, (ax, ROOM_TOTAL_Y - 0.08, 2.18), mats["brass"], arch_col, rot=(0, math.pi * 0.5, 0))
    add_box(f"B5_StbdArt_Glow_{a_i}", (0.48, 0.02, 0.015), (ax, ROOM_TOTAL_Y - 0.08, 2.165), mats["led_warm"], arch_col)

# ==============================================================================
# 6. TWO BLACK MARBLE STRUCTURAL PILLARS + AFT GLASS PARTITION WALL & PILASTERS
#    (Per Photos 14.30.45, 14.31.14 (1), 14.31.15, 14.31.15 (3))
# ==============================================================================
# 6A. 2 Freestanding Black Marble Pillars with Brass Corner Trim on the Green Carpet
for p_tag, py in [("Port", 5.95), ("Stbd", 11.51)]:
    px = 33.15
    add_box(f"B5_BlackMarble_Pillar_{p_tag}", (0.46, 0.46, CEIL_H), (px, py, CEIL_H * 0.5), mats["b5_black_marble_pillar"], arch_col, bevel=0.006)
    add_box(f"B5_BlackMarble_Plinth_{p_tag}", (0.50, 0.50, 0.14),   (px, py, 0.07),         mats["black_metal"], arch_col, bevel=0.004)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            add_box(f"B5_Pillar_BrassEdge_{p_tag}_{sx}_{sy}", (0.018, 0.018, CEIL_H - 0.14), (px + sx * 0.228, py + sy * 0.228, 0.07 + (CEIL_H - 0.14) * 0.5), mats["brass"], arch_col)

# 6B. Central Patterned Glass Partition Wall at X = 37.80m (Y = 3.36m .. 14.10m, behind 379, 419, 484, 442)
gw_y0, gw_y1 = CARPET_Y0, CARPET_Y1  # 3.36 .. 14.10m
gw_len = gw_y1 - gw_y0               # 10.74m
gw_cy  = 0.5 * (gw_y0 + gw_y1)       # 8.73m

# Plinth (Z = 0.00..0.12m), Turquoise Wainscot Base (Z = 0.12..0.86m), Black Marble Ledge (Z = 0.86..0.90m)
add_box("B5_GlassWall_Plinth",     (0.18, gw_len, 0.12), (B5_GLASS_WALL_X, gw_cy, 0.06), mats["black_metal"], arch_col)
add_box("B5_GlassWall_Turquoise",  (0.16, gw_len, 0.74), (B5_GLASS_WALL_X, gw_cy, 0.49), mats["b5_turquoise_wall"], arch_col)
add_box("B5_GlassWall_MarbleLedge",(0.24, gw_len + 0.06, 0.045), (B5_GLASS_WALL_X, gw_cy, 0.88), mats["b5_black_marble_pillar"], arch_col, bevel=0.005)

# 4 Bays along the Glass Wall: [3.36..5.95, 5.95..8.73, 8.73..11.51, 11.51..14.10]
gw_splits = [3.36, 5.95, 8.73, 11.51, 14.10]
glass_z0, glass_z1 = 0.90, 2.38
glass_h = glass_z1 - glass_z0  # 1.48m
glass_cz = 0.5 * (glass_z0 + glass_z1)

# Top and bottom continuous brass frame rails
add_box("B5_GlassWall_BrassBotRail", (0.05, gw_len, 0.04), (B5_GLASS_WALL_X, gw_cy, glass_z0 + 0.02), mats["brass"], arch_col, bevel=0.003)
add_box("B5_GlassWall_BrassTopRail", (0.05, gw_len, 0.045),(B5_GLASS_WALL_X, gw_cy, glass_z1 - 0.02), mats["brass"], arch_col, bevel=0.003)

for b_i in range(4):
    by0, by1 = gw_splits[b_i], gw_splits[b_i + 1]
    bw = by1 - by0
    bcy = 0.5 * (by0 + by1)
    # Gold inset molding frame on the lower turquoise wainscot
    frame_w = bw - 0.28
    add_box(f"B5_GlassWall_GoldMolding_Top_{b_i}", (0.015, frame_w, 0.022), (B5_GLASS_WALL_X - 0.082, bcy, 0.74), mats["brass"], arch_col)
    add_box(f"B5_GlassWall_GoldMolding_Bot_{b_i}", (0.015, frame_w, 0.022), (B5_GLASS_WALL_X - 0.082, bcy, 0.24), mats["brass"], arch_col)
    add_box(f"B5_GlassWall_GoldMolding_L_{b_i}",   (0.015, 0.022, 0.52),    (B5_GLASS_WALL_X - 0.082, bcy - frame_w * 0.5, 0.49), mats["brass"], arch_col)
    add_box(f"B5_GlassWall_GoldMolding_R_{b_i}",   (0.015, 0.022, 0.52),    (B5_GLASS_WALL_X - 0.082, bcy + frame_w * 0.5, 0.49), mats["brass"], arch_col)

    # Geometric Frosted Glass Panel (Z = 0.94..2.34m)
    gp = add_box(f"B5_GlassWall_Panel_{b_i}", (0.016, bw - 0.06, glass_h - 0.08), (B5_GLASS_WALL_X, bcy, glass_cz), mats["b5_patterned_glass"], arch_col)
    apply_normalized_face_uv(gp)

    # Ceiling support rods from top of brass frame (Z = 2.38m) to ceiling (Z = 2.78m)
    for rod_y in (by0 + 0.18, bcy, by1 - 0.18):
        add_cylinder(f"B5_GlassWall_CeilRod_{b_i}_{rod_y:.2f}", 0.014, CEIL_H - glass_z1, (B5_GLASS_WALL_X, rod_y, 0.5 * (glass_z1 + CEIL_H)), mats["brass"], arch_col)

for s_i, sy in enumerate(gw_splits):
    add_box(f"B5_GlassWall_BrassMullion_{s_i}", (0.055, 0.055, glass_h), (B5_GLASS_WALL_X, sy, glass_cz), mats["brass"], arch_col, bevel=0.004)
    add_box(f"B5_GlassWall_LowerDivider_{s_i}", (0.175, 0.05, 0.74),     (B5_GLASS_WALL_X, sy, 0.49),     mats["brass"], arch_col)

# ==============================================================================
# 7. PATTERNED METAL GRILLE PARTITIONS & 6 SETS OF L-SHAPED WAITER STATIONS
#    (3 Sets on Portside behind 329/331 + 3 Sets on Starboardside behind 412/410)
# ==============================================================================
def build_metal_grille_partition_and_l_waiter_stations(side_tag, part_x, y_wall, y_inboard, is_portside):
    """
    Builds:
    1. The half-wall + patterned teal metal grille partition ('partisi besi bermotif dengan bagian bawah tembok')
       behind 329/331 (Portside, X = 38.05m) and behind 410/412 (Starboardside, X = 38.55m),
       including its L-corner return along +X (matching Photos 14.30.45, 14.31.14 (1), 14.31.15 (1)).
    2. 3 Sets of L-Shaped Waiter Station behind the partition:
       - 1 Set directly behind the table partition ('1 di belakang meja per sisi')
       - 2 Sets along the wall perpendicular/adjacent ('2 di tembok per sisi') forming an L-shape!
    """
    y0 = min(y_wall, y_inboard)
    y1 = max(y_wall, y_inboard)
    p_len_y = y1 - y0  # 2.45m
    p_cy = 0.5 * (y0 + y1)
    ret_len_x = 0.55   # Short return leg along +X at y_inboard
    ret_cx = part_x + ret_len_x * 0.5

    # --- A. LOWER SOLID HALF-WALL (Z = 0.00 .. 1.25m) ---
    pw_l = add_box(f"B5_PartWall_Lower_{side_tag}",  (0.14, p_len_y, 1.22), (part_x, p_cy, 0.61), mats["b5_sage_wall"], arch_col, bevel=0.004)
    apply_normalized_face_uv(pw_l)
    add_box(f"B5_PartWall_Plinth_{side_tag}", (0.17, p_len_y + 0.02, 0.14), (part_x, p_cy, 0.07), mats["wall_white"], arch_col)
    add_box(f"B5_PartWall_Cap_{side_tag}",    (0.18, p_len_y + 0.04, 0.05), (part_x, p_cy, 1.235), mats["wall_white"], arch_col, bevel=0.005)

    # Return leg along +X at y_inboard
    pw_rl = add_box(f"B5_PartWall_RetLower_{side_tag}",  (ret_len_x, 0.14, 1.22), (ret_cx, y_inboard, 0.61), mats["b5_sage_wall"], arch_col, bevel=0.004)
    apply_normalized_face_uv(pw_rl)
    add_box(f"B5_PartWall_RetPlinth_{side_tag}", (ret_len_x + 0.02, 0.17, 0.14), (ret_cx, y_inboard, 0.07), mats["wall_white"], arch_col)
    add_box(f"B5_PartWall_RetCap_{side_tag}",    (ret_len_x + 0.04, 0.18, 0.05), (ret_cx, y_inboard, 1.235), mats["wall_white"], arch_col, bevel=0.005)
    add_box(f"B5_PartWall_CornerStile_{side_tag}", (0.16, 0.16, 1.24), (part_x, y_inboard, 0.62), mats["wall_white"], arch_col)

    # --- B. UPPER PATTERNED TEAL METAL GRILLE (Z = 1.26 .. 2.66m) ---
    g_z0, g_z1 = 1.26, 2.66
    g_h = g_z1 - g_z0  # 1.40m
    g_cz = 0.5 * (g_z0 + g_z1)
    bar_t = 0.028

    # Horizontal rails (4 rails = 3 tiers) along Y and along +X return
    for r_i in range(4):
        rz = g_z0 + r_i * (g_h / 3.0)
        add_box(f"B5_MetalGrille_HRail_{side_tag}_{r_i}",    (bar_t, p_len_y, bar_t),   (part_x, p_cy, rz),      mats["b5_teal_metal"], arch_col)
        add_box(f"B5_MetalGrille_RetHRail_{side_tag}_{r_i}", (ret_len_x, bar_t, bar_t), (ret_cx, y_inboard, rz), mats["b5_teal_metal"], arch_col)

    # 5 main vertical posts along Y + staggered inner vertical bars in each tier (matching Photo 14.31.15 (1).jpeg!)
    n_cols = 5
    col_w = p_len_y / n_cols
    tier_h = g_h / 3.0
    for c_i in range(n_cols + 1):
        cy = y0 + c_i * col_w
        add_box(f"B5_MetalGrille_VPost_{side_tag}_{c_i}", (bar_t, bar_t, g_h), (part_x, cy, g_cz), mats["b5_teal_metal"], arch_col)
        if c_i < n_cols:
            for t_i in range(3):
                tz = g_z0 + (t_i + 0.5) * tier_h
                offset_frac = 0.32 if (t_i % 2 == 0) else 0.68
                inner_y = y0 + (c_i + offset_frac) * col_w
                add_box(f"B5_MetalGrille_InnerV_{side_tag}_{c_i}_{t_i}", (bar_t * 0.85, bar_t * 0.85, tier_h), (part_x, inner_y, tz), mats["b5_teal_metal"], arch_col)

    # End post of return leg
    add_box(f"B5_MetalGrille_RetEndPost_{side_tag}", (bar_t, bar_t, g_h), (part_x + ret_len_x, y_inboard, g_cz), mats["b5_teal_metal"], arch_col)

    # --- C. 3 SETS OF L-SHAPED WAITER STATION BEHIND THE PARTITION ---
    def build_b5_ws_segment(ws_name, f0_xy, f1_xy, front_normal_xy, n_sets=1):
        f0 = Vector((f0_xy[0], f0_xy[1], 0.0))
        f1 = Vector((f1_xy[0], f1_xy[1], 0.0))
        tang = (f1 - f0).normalized()
        total_len = (f1 - f0).length
        n_front = Vector((front_normal_xy[0], front_normal_xy[1], 0.0)).normalized()
        n_back = -n_front
        normal_yaw = math.atan2(n_front.y, n_front.x)
        station_depth = 0.60
        back_origin = f0 + n_back * station_depth
        s_mid = total_len * 0.5

        def st_pos(d_from_back, s_along, z):
            p = back_origin + n_front * d_from_back + tang * s_along
            return (p.x, p.y, z)

        cab_len = total_len - 0.008
        add_box(f"{ws_name}_Plinth",     (0.56, cab_len, 0.04), st_pos(0.30, s_mid, 0.02),  mats["black_metal"], arch_col, rot=(0, 0, normal_yaw))
        add_box(f"{ws_name}_Carcass",    (0.56, cab_len, 0.84), st_pos(0.30, s_mid, 0.46),  mats["black_metal"], arch_col, rot=(0, 0, normal_yaw))
        add_box(f"{ws_name}_MarbleTop",  (0.59, cab_len, 0.04), st_pos(0.315, s_mid, 0.90), mats["b5_black_marble_pillar"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
        add_box(f"{ws_name}_Backsplash", (0.04, cab_len, 0.22), st_pos(0.04, s_mid, 1.03),  mats["b5_black_marble_pillar"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))

        n_sections = 2 * n_sets
        part_thick = 0.030
        end_stile = 0.022
        avail = total_len - (n_sections - 1) * part_thick - 2 * end_stile
        unit_w = avail / (2.0 * n_sets)
        sec_widths = []
        for _ in range(n_sets):
            sec_widths.extend([unit_w * 0.5, unit_w * 1.5])

        curr_s = end_stile
        for sec_i, sec_w in enumerate(sec_widths):
            sec_cs = curr_s + sec_w * 0.5
            face_w = sec_w - 0.016
            handle_w = min(0.15, face_w * 0.45)
            add_box(f"{ws_name}_LowerCab_{sec_i}",   (0.024, face_w, 0.39),  st_pos(0.585, sec_cs, 0.25),  mats["b5_turquoise_wall"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))
            add_box(f"{ws_name}_LowerHdl_{sec_i}",   (0.018, handle_w, 0.014),st_pos(0.602, sec_cs, 0.40), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))
            add_box(f"{ws_name}_MidDrawer_{sec_i}",  (0.024, face_w, 0.195), st_pos(0.585, sec_cs, 0.565), mats["b5_turquoise_wall"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))
            add_box(f"{ws_name}_MidHdl_{sec_i}",     (0.018, handle_w, 0.014),st_pos(0.602, sec_cs, 0.565),mats["chrome"], arch_col, rot=(0, 0, normal_yaw))
            add_box(f"{ws_name}_TopDrawer_{sec_i}",  (0.024, face_w, 0.195), st_pos(0.585, sec_cs, 0.775), mats["b5_turquoise_wall"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))
            add_box(f"{ws_name}_TopHdl_{sec_i}",     (0.018, handle_w, 0.014),st_pos(0.602, sec_cs, 0.775),mats["chrome"], arch_col, rot=(0, 0, normal_yaw))
            if sec_i < len(sec_widths) - 1:
                part_cs = curr_s + sec_w + part_thick * 0.5
                add_box(f"{ws_name}_Part25cm_{sec_i}", (0.58, part_thick, 0.22), st_pos(0.31, part_cs, 1.03), mats["b5_black_marble_pillar"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))
            curr_s += sec_w + part_thick

    ws1_front_x = part_x + 0.68
    ws2_start_x = part_x + 0.08
    if is_portside:
        build_b5_ws_segment(f"B5_WS_{side_tag}_BehindTable_1Set", (ws1_front_x, 0.684), (ws1_front_x, 2.18), (1.0, 0.0), n_sets=1)
        build_b5_ws_segment(f"B5_WS_{side_tag}_Wall_2Sets",       (ws2_start_x, 0.680), (ws2_start_x + 2.50, 0.680), (0.0, 1.0), n_sets=2)
    else:
        build_b5_ws_segment(f"B5_WS_{side_tag}_BehindTable_1Set", (ws1_front_x, 16.776), (ws1_front_x, 15.28), (1.0, 0.0), n_sets=1)
        build_b5_ws_segment(f"B5_WS_{side_tag}_Wall_2Sets",       (ws2_start_x, 16.780), (ws2_start_x + 2.45, 16.780), (0.0, -1.0), n_sets=2)

# Portside Partition at X = 38.05m (behind 329/331) & Starboardside Partition at X = 38.55m (behind 410/412, shifted Aft!)
build_metal_grille_partition_and_l_waiter_stations("Port", 38.05, 0.10,  2.55,  is_portside=True)
build_metal_grille_partition_and_l_waiter_stations("Stbd", 38.55, 17.36, 14.91, is_portside=False)

# Aft Perimeter Backing Wall of Block 5 at X = 41.20m (Shadowed Service Gallery behind Glass Wall) & Doorway Framing Pilasters
add_box("B5_AftPerimeter_Wall", (0.20, ROOM_TOTAL_Y, CEIL_H), (B5_AFT_WALL_X, CLOVER_CY, CEIL_H * 0.5), mats["aft_gallery_dark"], arch_col)
for cred_tag, cred_y in [("Port", 6.40), ("Stbd", 11.06)]:
    add_box(f"B5_AftGallery_Credenza_{cred_tag}", (0.65, 2.80, 0.90), (39.85, cred_y, 0.45), mats["b5_black_marble_pillar"], arch_col, bevel=0.005)
for pil_tag, pil_y in [("PortDoor", 3.16), ("StbdDoor", 14.30)]:
    dp = add_box(f"B5_Doorway_Pilaster_{pil_tag}", (0.42, 0.42, CEIL_H), (38.05, pil_y, CEIL_H * 0.5), mats["b5_sage_wall"], arch_col, bevel=0.005)
    apply_normalized_face_uv(dp)
    add_box(f"B5_Doorway_PilPlinth_{pil_tag}",(0.46, 0.46, 0.16),   (38.05, pil_y, 0.08),         mats["wall_white"], arch_col)
    add_box(f"B5_Doorway_PilRail_{pil_tag}",  (0.46, 0.46, 0.06),   (38.05, pil_y, 0.87),         mats["wall_white"], arch_col)
    add_box(f"B5_Doorway_ExitSign_{pil_tag}", (0.05, 0.36, 0.12),   (37.82, pil_y + (0.45 if "Stbd" in pil_tag else -0.45), 2.52), mats["exit_green"], arch_col)

# ==============================================================================
# 8. BLOCK 5 DARK COFFERED ACOUSTIC CEILING, 68 SPOTLIGHTS, CHROME MIRROR BANDS,
#    DOUBLE BLACK AC SLOTS, 6 MURANO CHANDELIERS & SCENE LIGHTING
#    (Per Photos 14.30.44 (1), 14.31.14, 14.31.15 (2), 14.31.15 (3))
# ==============================================================================
# 8A. Dark Charcoal-Taupe Coffered Main Ceiling Slab at Z = COFFER_H (2.96m) — matching Blocks 1-4 & Real Photos!
add_box("Ceiling_Block5_MainSlab", (b5_len_x, ROOM_TOTAL_Y, 0.10), (b5_mid_x, CLOVER_CY, COFFER_H + 0.04), mats["coffer_dark"], arch_col)

# 8B. Dropped Warm-White Architectural Soffit Beams at Z = 2.78m with Dark Shadow Reveals
soffit_x_bands = [(28.15, 29.05), (33.00, 33.62), (37.48, 38.12), (40.75, 41.20)]
for sx_i, (sx0, sx1) in enumerate(soffit_x_bands):
    add_box(f"Ceiling_Block5_SoffitX_{sx_i}", (sx1 - sx0, ROOM_TOTAL_Y, 0.18), (0.5 * (sx0 + sx1), CLOVER_CY, CEIL_H + 0.09), mats["wall_white"], arch_col, bevel=0.005)

soffit_y_bands = [(0.00, 0.78), (5.62, 6.28), (11.18, 11.84), (16.68, 17.46)]
for sy_i, (sy0, sy1) in enumerate(soffit_y_bands):
    add_box(f"Ceiling_Block5_SoffitY_{sy_i}", (b5_len_x, sy1 - sy0, 0.18), (b5_mid_x, 0.5 * (sy0 + sy1), CEIL_H + 0.09), mats["wall_white"], arch_col, bevel=0.005)

# Double Black Linear AC Slot Diffusers recessed into the perimeter soffit beams (visible in Photos 14.30.44 (1) & 14.31.14!)
for ac_y in (0.38, 5.95, 11.51, 17.08):
    for slot_off in (-0.045, 0.045):
        add_box(f"Ceiling_Block5_ACSlotY_{ac_y:.2f}_{slot_off:.3f}", (8.20, 0.024, 0.012), (33.25, ac_y + slot_off, CEIL_H + 0.002), mats["black_metal"], arch_col)
for ac_x in (28.60, 33.31, 37.80):
    for slot_off in (-0.045, 0.045):
        add_box(f"Ceiling_Block5_ACSlotX_{ac_x:.2f}_{slot_off:.3f}", (0.024, 15.20, 0.012), (ac_x + slot_off, CLOVER_CY, CEIL_H + 0.002), mats["black_metal"], arch_col)

# 8C. 3D Square Coffered Acoustic Ceiling Tile Grid (0.65m x 0.65m dark T-bar ribs) inside all Recessed Bays
coffer_bays = [
    ("PortFwd", 29.05, 33.00, 0.78, 5.62),
    ("PortAft", 33.62, 37.48, 0.78, 5.62),
    ("CentFwd", 29.05, 33.00, 6.28, 11.18),
    ("CentAft", 33.62, 37.48, 6.28, 11.18),
    ("StbdFwd", 29.05, 33.00, 11.84, 16.68),
    ("StbdAft", 33.62, 37.48, 11.84, 16.68),
    ("GallAft", 38.12, 40.75, 0.78, 16.68),
]
for bay_name, bx0, bx1, by0, by1 in coffer_bays:
    blx = bx1 - bx0
    bly = by1 - by0
    bcx = 0.5 * (bx0 + bx1)
    bcy = 0.5 * (by0 + by1)
    nx_ribs = max(2, int(round(blx / 0.65)))
    ny_ribs = max(2, int(round(bly / 0.65)))
    for ix in range(nx_ribs + 1):
        rx = bx0 + ix * (blx / nx_ribs)
        add_box(f"Ceiling_Block5_RibX_{bay_name}_{ix}", (0.028, bly, 0.024), (rx, bcy, COFFER_H - 0.012), mats["coffer_rib"], arch_col)
    for iy in range(ny_ribs + 1):
        ry = by0 + iy * (bly / ny_ribs)
        add_box(f"Ceiling_Block5_RibY_{bay_name}_{iy}", (blx, 0.028, 0.024), (bcx, ry, COFFER_H - 0.012), mats["coffer_rib"], arch_col)

# 8D. Wide Dark-Chrome Reflective Ceiling Spine Bands above the 6 Murano Chandeliers (matching Photos 14.31.14 & 14.31.15 (3)!)
for spine_tag, spy in [("419", 7.35), ("484", 10.11)]:
    add_box(f"Ceiling_Block5_ChromeSpine_{spine_tag}", (3.86, 0.52, 0.018), (35.55, spy, COFFER_H - 0.010), mats["mirror_chrome"], arch_col, bevel=0.003)
for cross_x in (34.10, 35.55, 37.00):
    add_box(f"Ceiling_Block5_ChromeCross_{cross_x:.2f}", (0.36, 4.90, 0.016), (cross_x, CLOVER_CY, COFFER_H - 0.011), mats["mirror_chrome"], arch_col, bevel=0.003)

# Warm Cove LED glow strips along the ceiling recesses
for cove_y in (0.80, 5.60, 6.30, 11.16, 11.86, 16.66):
    add_box(f"Ceiling_Block5_CoveLED_Y_{cove_y:.2f}", (8.20, 0.032, 0.022), (33.25, cove_y, CEIL_H + 0.14), mats["led_warm"], arch_col)

# 8E. Dense Matrix of 68 Stepped Anti-Glare Recessed Spotlights + 12 Ceiling Speakers (matching Real Photos & Blocks 1-4!)
# Spotlights on Dropped Soffit Beams (Z = CEIL_H = 2.78m)
soffit_spot_xs = (28.60, 33.31, 37.80)
soffit_spot_ys = (1.15, 2.50, 3.80, 5.10, 6.80, 8.73, 10.66, 12.36, 13.66, 14.96, 16.31)
for sp_x in soffit_spot_xs:
    for sp_y in soffit_spot_ys:
        add_cylinder(f"Ceiling_Block5_SoffitBezel_{sp_x:.2f}_{sp_y:.2f}", 0.072, 0.010, (sp_x, sp_y, CEIL_H - 0.002), mats["chrome"], arch_col)
        add_cylinder(f"Ceiling_Block5_SoffitBaffle_{sp_x:.2f}_{sp_y:.2f}", 0.054, 0.014, (sp_x, sp_y, CEIL_H + 0.002), mats["black_metal"], arch_col)
        add_cylinder(f"Ceiling_Block5_SoffitLED_{sp_x:.2f}_{sp_y:.2f}", 0.036, 0.016, (sp_x, sp_y, CEIL_H + 0.004), mats["led_warm"], arch_col)

# Spotlights inside the Dark Coffered Recessed Bays (Z = COFFER_H = 2.96m)
coffer_spot_xs = (29.85, 31.15, 32.35, 34.35, 35.55, 36.75, 39.25)
coffer_spot_ys = (1.45, 3.15, 4.75, 6.70, 8.73, 10.76, 12.71, 14.31, 16.01)
for cx_s in coffer_spot_xs:
    for cy_s in coffer_spot_ys:
        # Skip positions occupied by the 6 Murano chandelier canopies
        if abs(cx_s - 35.55) < 0.25 and (abs(cy_s - 7.35) < 0.45 or abs(cy_s - 10.11) < 0.45):
            continue
        add_cylinder(f"Ceiling_Block5_CofferBezel_{cx_s:.2f}_{cy_s:.2f}", 0.075, 0.012, (cx_s, cy_s, COFFER_H - 0.018), mats["chrome"], arch_col)
        add_cylinder(f"Ceiling_Block5_CofferBaffle_{cx_s:.2f}_{cy_s:.2f}", 0.056, 0.016, (cx_s, cy_s, COFFER_H - 0.014), mats["black_metal"], arch_col)
        add_cylinder(f"Ceiling_Block5_CofferLED_{cx_s:.2f}_{cy_s:.2f}", 0.038, 0.018, (cx_s, cy_s, COFFER_H - 0.012), mats["led_warm"], arch_col)

# 12 Recessed Marine Audio Speaker Grilles & 8 Fire Sprinklers in the ceiling
for spk_x in (30.50, 34.95, 39.85):
    for spk_y in (2.20, 6.00, 11.46, 15.26):
        sz_spk = CEIL_H if spk_y in (6.00, 11.46) else (COFFER_H - 0.016)
        add_cylinder(f"Ceiling_Block5_SpeakerRim_{spk_x:.2f}_{spk_y:.2f}", 0.095, 0.008, (spk_x, spk_y, sz_spk), mats["wall_white"], arch_col)
        add_cylinder(f"Ceiling_Block5_SpeakerMesh_{spk_x:.2f}_{spk_y:.2f}", 0.076, 0.010, (spk_x, spk_y, sz_spk - 0.001), mats["coffer_rib"], arch_col)

# 8F. Physical Downward-Pointing Stepped Baffle SPOT Lights & Shadow-Pool Optimization
#     (Prevents Blender 5.2 EEVEE 'Shadow buffer full' overflow & keeps upper corners dark/moody while casting crisp floor shadows!)
if hasattr(scene.eevee, "shadow_pool_size"):
    scene.eevee.shadow_pool_size = '1024'

# Optimize existing lights in Blocks 1-4 so EEVEE's 1GB shadow pool never overflows
for l_existing in bpy.data.lights:
    if l_existing.name.startswith("WindowPortalLight_"):
        l_existing.use_shadow = False
    elif l_existing.name.startswith(("CeilingWarmFill_", "B3B4_")):
        l_existing.use_custom_distance = True
        l_existing.cutoff_distance = 7.5

# Lower ambient world fill slightly so shadow sides of chairs, tables & corners have deep contrast
world = bpy.data.worlds.get("Arlecchino_World")
if world and world.use_nodes:
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Strength"].default_value = 0.42

def add_b5_spot_downlight(name, location, energy, spot_deg=105.0, spot_blend=0.55, radius=0.16, color=(1.0, 0.85, 0.68)):
    ldata = bpy.data.lights.new(name=name, type='SPOT')
    ldata.energy = energy
    ldata.color = color
    ldata.spot_size = math.radians(spot_deg)
    ldata.spot_blend = spot_blend
    if hasattr(ldata, "shadow_soft_size"):
        ldata.shadow_soft_size = radius
    if hasattr(ldata, "specular_factor"):
        ldata.specular_factor = 0.35
    ldata.use_shadow = True
    ldata.use_custom_distance = True
    ldata.cutoff_distance = 6.2
    lobj = bpy.data.objects.new(name=name, object_data=ldata)
    lobj.location = location
    lobj.rotation_euler = (0.0, 0.0, 0.0)
    link_to_collection(lobj, light_col)
    return lobj

# 15 Focused Downward 2700K Spot Downlights over the Block 5 dining zones (1 shadow cone each -> zero shadow pool overflow!)
b5_spot_zones = [
    # Forward Sofa Row (Portside & Starboardside)
    (29.25, 2.00, 52.0), (29.25, 5.45, 52.0), (29.25, 12.01, 52.0), (29.25, 15.45, 52.0),
    # Forward Carpet Row & Window/Wall Pairs
    (32.10, 1.55, 56.0), (32.10, 5.80, 58.0), (32.10, 11.66, 58.0), (32.85, 15.85, 56.0),
    # Mid/Aft Carpet Row (Tables 419, 484, 381/379, 444/442) & Window/Wall Pairs
    (35.55, 1.55, 56.0), (35.55, 4.55, 56.0), (35.55, 7.35, 64.0), (35.55, 10.11, 64.0), (35.55, 12.91, 56.0), (36.10, 15.85, 56.0),
    # Aft Service & Waiter Station Gallery
    (39.15, 8.73, 42.0),
]
for idx_l, (lx, ly, l_en) in enumerate(b5_spot_zones):
    add_b5_spot_downlight(f"B5_Light_CeilSpot_{idx_l:02d}_{lx:.1f}_{ly:.1f}", (lx, ly, 2.74), energy=l_en)

# 3 Subtle Sea-Window Rim Lights along Portside Windows (shadowless fill so they don't consume shadow tiles)
for w_i, (wx0, wx1) in enumerate(b5_port_windows):
    wcx = 0.5 * (wx0 + wx1)
    ldata = bpy.data.lights.new(name=f"B5_Light_WinPortal_{w_i}", type='AREA')
    ldata.shape = 'DISK'
    ldata.size = 0.85
    ldata.energy = 16.0
    ldata.color = (0.86, 0.94, 1.0)
    ldata.use_shadow = False
    if hasattr(ldata, "specular_factor"):
        ldata.specular_factor = 0.0
    lobj = bpy.data.objects.new(name=f"B5_Light_WinPortal_{w_i}", object_data=ldata)
    lobj.location = (wcx, 0.22, 1.65)
    lobj.rotation_euler = (-math.pi * 0.5, 0.0, 0.0)
    link_to_collection(lobj, light_col)

def build_murano_pendant_lamp(lamp_name, cx, cy, z_bottom, glass_mat):
    """
    Builds the AAA high-detail Venetian Murano blown-glass pendant chandelier over
    the 10-pax oak tables 419 and 484 (matching Photo 14.31.14.jpeg):
    - 64 radial segments x 45 vertical profile stations with 24 smooth optic flutes
    - Explicit (u, v) lathe UVs mapped to the ribbed glass & warm radial inner bulb glow texture
    - Opaque hardware depth sorting (alpha_tex=False) so all 6 lamps sort with 100% physical
      hierarchy from ANY 360° camera angle (zero alpha overlap!)
    - Separate Polished Brass collar rings between the glass tiers & flared trumpet ceiling canopy
    """
    me = bpy.data.meshes.new(lamp_name + "_Glass_mesh")
    bm = bmesh.new()

    total_h = 1.10
    # Smooth high-resolution Venetian Murano profile (r, z_offset_from_bottom)
    profile = [
        # Pointed bottom tear-drop finial & 3 graduated lower ribbed drops (z = 0.00 .. 0.21m)
        (0.000, 0.000), (0.016, 0.012), (0.030, 0.028), (0.018, 0.046),
        (0.044, 0.068), (0.056, 0.088), (0.030, 0.112),
        (0.072, 0.140), (0.092, 0.168), (0.074, 0.192), (0.040, 0.210),
        # Main bulbous ribbed lantern bowl (z = 0.21 .. 0.45m)
        (0.095, 0.232), (0.142, 0.268), (0.168, 0.315), (0.175, 0.365),
        (0.168, 0.410), (0.155, 0.440),
        # Wide flared scalloped Venetian bell brim / shade (z = 0.44 .. 0.54m)
        (0.215, 0.456), (0.258, 0.472), (0.264, 0.484), (0.235, 0.498),
        (0.178, 0.525), (0.132, 0.560), (0.092, 0.592), (0.046, 0.615),
        # Lower stem ribbed sphere / boule #1 (z = 0.615 .. 0.755m)
        (0.078, 0.645), (0.098, 0.685), (0.082, 0.725), (0.042, 0.755),
        # Upper stem ribbed sphere / boule #2 (z = 0.755 .. 0.865m)
        (0.068, 0.785), (0.084, 0.815), (0.068, 0.845), (0.042, 0.868),
        # Lower fluted tulip crown cup (z = 0.868 .. 0.985m)
        (0.062, 0.895), (0.088, 0.935), (0.114, 0.968), (0.106, 0.978), (0.046, 0.988),
        # Upper taller fluted tulip crown cup (z = 0.988 .. 1.100m)
        (0.065, 1.015), (0.092, 1.055), (0.122, 1.088), (0.114, 1.096), (0.038, 1.100),
    ]
    segs = 64
    rings = []
    for r_val, dz in profile:
        ring = []
        v_coord = dz / total_h
        # Scalloped wavy brim modulation on the wide bell rim and tulip cup rims
        is_rim = (0.455 <= dz <= 0.505) or (0.955 <= dz <= 0.982) or (1.075 <= dz <= 1.098)
        for s in range(segs):
            ang = 2.0 * math.pi * s / segs
            flute = 1.0 + (0.032 * math.cos(24.0 * ang) if r_val > 0.048 else 0.0)
            scallop = (0.008 * math.sin(12.0 * ang)) if is_rim else 0.0
            px = cx + r_val * flute * math.cos(ang)
            py = cy + r_val * flute * math.sin(ang)
            pz = z_bottom + dz + scallop
            vtx = bm.verts.new((px, py, pz))
            ring.append((vtx, s / segs, v_coord))
        rings.append(ring)

    uv_layer = bm.loops.layers.uv.new("UVMap")
    for i in range(len(rings) - 1):
        for s in range(segs):
            sn = (s + 1) % segs
            v00, u00, w00 = rings[i][s]
            v10, u10, w10 = rings[i][sn]
            v11, u11, w11 = rings[i + 1][sn]
            v01, u01, w01 = rings[i + 1][s]
            if sn == 0:
                u10 = 1.0
                u11 = 1.0
            f = bm.faces.new((v00, v10, v11, v01))
            f.smooth = True
            f.loops[0][uv_layer].uv = (u00, w00)
            f.loops[1][uv_layer].uv = (u10, w10)
            f.loops[2][uv_layer].uv = (u11, w11)
            f.loops[3][uv_layer].uv = (u01, w01)

    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(glass_mat)
    glass_obj = bpy.data.objects.new(lamp_name + "_Glass", me)
    link_to_collection(glass_obj, arch_col)

    # Polished Brass Collar Rings between the Venetian glass tiers (matching Photo 14.31.14.jpeg)
    for c_idx, (c_r, c_dz) in enumerate([
        (0.045, 0.210),
        (0.050, 0.615),
        (0.046, 0.755),
        (0.046, 0.868),
        (0.050, 0.988),
    ]):
        add_cylinder(f"{lamp_name}_BrassCollar_{c_idx}", c_r, 0.018, (cx, cy, z_bottom + c_dz), mats["brass"], arch_col, vertices=32)

    # Flared Trumpet Polished Brass Ceiling Canopy (CeilCup) & Suspension Rod up to Z = 2.96m
    z_top_glass = z_bottom + total_h
    rod_h = max(0.04, COFFER_H - z_top_glass)
    add_cylinder(lamp_name + "_Rod", 0.011, rod_h, (cx, cy, z_top_glass + rod_h * 0.5), mats["brass"], arch_col, vertices=24)

    # Trumpet-shaped brass ceiling cone (narrow at bottom, wide at ceiling)
    cone_me = bpy.data.meshes.new(lamp_name + "_CeilCup_mesh")
    cbm = bmesh.new()
    cup_prof = [(0.022, -0.13), (0.032, -0.09), (0.048, -0.05), (0.072, -0.015), (0.082, 0.0)]
    c_rings = []
    for cr, cdz in cup_prof:
        c_ring = [cbm.verts.new((cx + cr * math.cos(2.0 * math.pi * s / 32), cy + cr * math.sin(2.0 * math.pi * s / 32), COFFER_H + cdz)) for s in range(32)]
        c_rings.append(c_ring)
    for i in range(len(c_rings) - 1):
        for s in range(32):
            sn = (s + 1) % 32
            f = cbm.faces.new((c_rings[i][s], c_rings[i][sn], c_rings[i + 1][sn], c_rings[i + 1][s]))
            f.smooth = True
    cbm.to_mesh(cone_me)
    cbm.free()
    for p in cone_me.polygons:
        p.use_smooth = True
    cone_me.materials.append(mats["brass"])
    cup_obj = bpy.data.objects.new(lamp_name + "_CeilCup", cone_me)
    link_to_collection(cup_obj, arch_col)

# 3 Murano Pendants over Table 419 (Y = 7.35m) & 3 Murano Pendants over Table 484 (Y = 10.11m)
# All 6 hung at the exact same architectural elevation (z_bottom = 1.66m) and spaced 1.45m apart
# along the 3.60m oak tables, matching Photo 14.31.14.jpeg with zero overlap!
pendant_x_specs = [
    ("FwdGreen", 34.10, 1.66, mats["b5_pendant_green"]),
    ("MidAmber", 35.55, 1.66, mats["b5_pendant_amber"]),
    ("AftGreen", 37.00, 1.66, mats["b5_pendant_green"]),
]
for tbl_tag, py in [("419", 7.35), ("484", 10.11)]:
    for p_tag, px, pz_bot, p_mat in pendant_x_specs:
        build_murano_pendant_lamp(f"B5_Pendant_{tbl_tag}_{p_tag}", px, py, pz_bot, p_mat)

# ==============================================================================
# 9. CREATE BLOCK 5 CUSTOM CHAIR TEMPLATES (100% CONTINUOUS SEAMLESS CURVES!)
# ==============================================================================
def add_smooth_tapered_leg(bm, uv_layer, p_bot, p_top, r_bot, r_top, mat_idx, segs=20, v_range=(0.04, 0.52)):
    """Adds a smooth cylindrical tapered leg between p_bot and p_top with shared smooth normals and vertical AO UVs."""
    v_bot = Vector(p_bot)
    v_top = Vector(p_top)
    axis = v_top - v_bot
    length = axis.length
    if length < 1e-4:
        return
    z_dir = axis.normalized()
    ref = Vector((1.0, 0.0, 0.0)) if abs(z_dir.x) < 0.8 else Vector((0.0, 1.0, 0.0))
    x_dir = z_dir.cross(ref).normalized()
    y_dir = z_dir.cross(x_dir).normalized()

    rings = []
    for t, rad in [(0.0, r_bot), (0.5, 0.5 * (r_bot + r_top)), (1.0, r_top)]:
        center = v_bot.lerp(v_top, t)
        v_uv = v_range[0] + t * (v_range[1] - v_range[0])
        ring = []
        for s in range(segs):
            ang = 2.0 * math.pi * s / segs
            pt = center + (x_dir * math.cos(ang) + y_dir * math.sin(ang)) * rad
            ring.append((bm.verts.new(pt), s / segs, v_uv))
        rings.append(ring)

    for r_i in range(len(rings) - 1):
        for s in range(segs):
            sn = (s + 1) % segs
            v00, u00, w00 = rings[r_i][s]
            v10, u10, w10 = rings[r_i][sn]
            v11, u11, w11 = rings[r_i + 1][sn]
            v01, u01, w01 = rings[r_i + 1][s]
            f = bm.faces.new((v00, v10, v11, v01))
            f.material_index = mat_idx
            f.smooth = True
            f.loops[0][uv_layer].uv = (u00, w00)
            f.loops[1][uv_layer].uv = (u10, w10)
            f.loops[2][uv_layer].uv = (u11, w11)
            f.loops[3][uv_layer].uv = (u01, w01)

    f_cap = bm.faces.new([v for v, _, _ in reversed(rings[0])])
    f_cap.material_index = mat_idx
    f_cap.smooth = False
    for lp in f_cap.loops:
        lp[uv_layer].uv = (0.5, 0.02)

def add_smooth_squircle_cushion(bm, uv_layer, center_xyz, rx, ry, z_bot, z_top, mat_idx, power=3.2, n_ang=36):
    """Creates a plush, seamlessly rounded squircle seat cushion with explicit AO rim-and-crown UVs."""
    cx, cy, _ = center_xyz
    z_mid = 0.5 * (z_bot + z_top)
    half_h = 0.5 * (z_top - z_bot)
    # 5 profile rings from shadowed bottom underside (v_uv=0.05) up over the rounded rim to the lit top (v_uv=0.82)
    prof = [
        (0.86, -half_h,        0.04),
        (0.97, -half_h * 0.65, 0.18),
        (1.00, 0.0,            0.46),
        (0.96, half_h * 0.72,  0.74),
        (0.82, half_h * 0.96,  0.86),
    ]
    rings = []
    for scale_r, dz, v_uv in prof:
        ring = []
        for s in range(n_ang):
            ang = 2.0 * math.pi * s / n_ang
            ca, sa = math.cos(ang), math.sin(ang)
            ux = math.copysign(abs(ca) ** (2.0 / power), ca)
            uy = math.copysign(abs(sa) ** (2.0 / power), sa)
            px = cx + ux * rx * scale_r
            py = cy + uy * ry * scale_r
            pz = z_mid + dz
            ring.append((bm.verts.new((px, py, pz)), s / n_ang, v_uv))
        rings.append(ring)

    for r_i in range(len(rings) - 1):
        for s in range(n_ang):
            sn = (s + 1) % n_ang
            v00, u00, w00 = rings[r_i][s]
            v10, u10, w10 = rings[r_i][sn]
            v11, u11, w11 = rings[r_i + 1][sn]
            v01, u01, w01 = rings[r_i + 1][s]
            f = bm.faces.new((v00, v10, v11, v01))
            f.material_index = mat_idx
            f.smooth = True
            f.loops[0][uv_layer].uv = (u00, w00)
            f.loops[1][uv_layer].uv = (u10, w10)
            f.loops[2][uv_layer].uv = (u11, w11)
            f.loops[3][uv_layer].uv = (u01, w01)

    v_top_c = bm.verts.new((cx, cy, z_top + 0.004))
    v_bot_c = bm.verts.new((cx, cy, z_bot))
    for s in range(n_ang):
        sn = (s + 1) % n_ang
        vt0, ut0, wt0 = rings[-1][s]
        vt1, ut1, wt1 = rings[-1][sn]
        ft = bm.faces.new((vt0, vt1, v_top_c))
        ft.material_index = mat_idx
        ft.smooth = True
        ft.loops[0][uv_layer].uv = (ut0, wt0)
        ft.loops[1][uv_layer].uv = (ut1, wt1)
        ft.loops[2][uv_layer].uv = (0.5, 0.88)

        vb0, ub0, wb0 = rings[0][sn]
        vb1, ub1, wb1 = rings[0][s]
        fb = bm.faces.new((vb0, vb1, v_bot_c))
        fb.material_index = mat_idx
        fb.smooth = True
        fb.loops[0][uv_layer].uv = (ub0, wb0)
        fb.loops[1][uv_layer].uv = (ub1, wb1)
        fb.loops[2][uv_layer].uv = (0.5, 0.02)

def create_b5_teal_ivory_tub_chair_mesh():
    """
    Creates the signature Block 5 two-tone curved tub chair (Photos 14.30.44 (2) & 14.30.53)
    using a SINGLE CONTINUOUS LOFTED SURFACE (41 angular steps x 10 profile points) with
    shared vertices, smooth normals, dark under-seat frame, and explicit self-occlusion UVs!
    - Slot 0: Mat_Block5_Teal_Leather (inner seat cushion, inner concave backrest, front legs)
    - Slot 1: Mat_Block5_Ivory_Shell (outer curved wrap-around mushroom-taupe shell, back legs)
    - Slot 2: Mat_Block5_Bronze_Pedestal (dark under-seat structural chassis & leg glides)
    """
    me = bpy.data.meshes.new("B5_Chair_TealIvory_Mesh")
    me.materials.append(mats["b5_teal_leather"])
    me.materials.append(mats["b5_ivory_shell"])
    me.materials.append(mats["b5_Bronze_Ped"])
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # 0. Dark Recessed Under-Seat Chassis Apron (Slot 2, Z = 0.395 .. 0.415m) for realistic under-chair shadow
    add_smooth_squircle_cushion(bm, uv_layer, (0.0, 0.012, 0.405), rx=0.205, ry=0.198, z_bot=0.394, z_top=0.415, mat_idx=2, power=2.8, n_ang=28)

    # 1. Plush Rounded-Squircle Seat Cushion (Teal leather [0], Z = 0.412 .. 0.476m)
    add_smooth_squircle_cushion(bm, uv_layer, (0.0, 0.015, 0.445), rx=0.228, ry=0.222, z_bot=0.412, z_top=0.476, mat_idx=0, power=3.0, n_ang=36)

    # 2. 4 Smooth Tapered Cylindrical Legs (Front = Teal [0], Rear = Ivory [1], Bottom ferrule = Bronze [2])
    for sx in (-0.192, 0.192):
        add_smooth_tapered_leg(bm, uv_layer, (sx * 1.03, 0.195, 0.0), (sx * 1.02, 0.192, 0.028), r_bot=0.014, r_top=0.015, mat_idx=2, segs=20, v_range=(0.02, 0.08))
        add_smooth_tapered_leg(bm, uv_layer, (sx * 1.02, 0.192, 0.028), (sx * 0.96, 0.175, 0.430), r_bot=0.015, r_top=0.022, mat_idx=0, segs=20, v_range=(0.08, 0.52))
        add_smooth_tapered_leg(bm, uv_layer, (sx * 1.04, -0.215, 0.0), (sx * 1.03, -0.212, 0.028), r_bot=0.015, r_top=0.016, mat_idx=2, segs=20, v_range=(0.02, 0.08))
        add_smooth_tapered_leg(bm, uv_layer, (sx * 1.03, -0.212, 0.028), (sx * 0.96, -0.180, 0.445), r_bot=0.016, r_top=0.023, mat_idx=1, segs=20, v_range=(0.06, 0.48))

    # 3. Single Continuous Lofted Wrap-Around Tub Backrest & Armrest Shell (41 smooth angular stations)
    n_arc = 41
    # (t_h, offset_out, v_uv) -> v_uv maps to our shaded ivory_shell / teal_leather textures (seam at v=0.985, lumbar/bottom crease at v=0.04)
    shell_prof = [
        (0.00,  0.000, 0.02),  # 0: Bottom edge center (dark tuck)
        (0.08,  0.018, 0.14),  # 1: Outer bottom bevel
        (0.35,  0.024, 0.42),  # 2: Outer lower wall
        (0.70,  0.024, 0.74),  # 3: Outer upper wall
        (0.93,  0.019, 0.92),  # 4: Outer top shoulder
        (1.00,  0.002, 0.985), # 5: Top crest stitched seam (Ivory/Teal boundary)
        (0.94, -0.016, 0.90),  # 6: Inner top roll (Teal)
        (0.72, -0.024, 0.72),  # 7: Inner upper cushion
        (0.40, -0.025, 0.38),  # 8: Inner lumbar cushion
        (0.10, -0.018, 0.08),  # 9: Inner lower lumbar crease
    ]
    n_prof = len(shell_prof)
    arc_rings = []

    for i in range(n_arc):
        u = i / (n_arc - 1)
        ang = -1.72 + 3.44 * u
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)

        cx = 0.226 * sin_a
        cy = 0.010 - 0.212 * cos_a
        nx = sin_a
        ny = -cos_a

        side_f = abs(u - 0.5) * 2.0
        z_top = 0.785 - 0.105 * (side_f ** 1.6)
        cutout_bump = 0.130 * (math.sin(min(1.0, side_f * 1.15) * math.pi * 0.5) ** 2.2)
        z_bot = 0.425 + cutout_bump

        tip_taper = math.sin(u * math.pi) ** 0.28
        ring = []
        for t_h, off_r, v_uv in shell_prof:
            pz = z_bot + t_h * (z_top - z_bot)
            rake = (pz - 0.45) * 0.08
            r_disp = off_r * tip_taper + rake
            px = cx + nx * r_disp
            py = cy + ny * r_disp
            ring.append((bm.verts.new((px, py, pz)), u, v_uv))
        arc_rings.append(ring)

    for i in range(n_arc - 1):
        for p_i in range(n_prof):
            pn = (p_i + 1) % n_prof
            v00, u00, w00 = arc_rings[i][p_i]
            v10, u10, w10 = arc_rings[i + 1][p_i]
            v11, u11, w11 = arc_rings[i + 1][pn]
            v01, u01, w01 = arc_rings[i][pn]
            f = bm.faces.new((v00, v10, v11, v01))
            f.material_index = 1 if p_i < 5 else 0
            f.smooth = True
            f.loops[0][uv_layer].uv = (u00, w00)
            f.loops[1][uv_layer].uv = (u10, w10)
            f.loops[2][uv_layer].uv = (u11, w11)
            f.loops[3][uv_layer].uv = (u01, w01)

    for end_idx, rev in [(0, True), (-1, False)]:
        ring = arc_rings[end_idx]
        c_co = sum((v.co for v, _, _ in ring), Vector((0, 0, 0))) / len(ring)
        v_cap = bm.verts.new(c_co)
        u_end = 0.02 if end_idx == 0 else 0.98
        for p_i in range(n_prof):
            pn = (p_i + 1) % n_prof
            va, ua, wa = ring[pn] if rev else ring[p_i]
            vb, ub, wb = ring[p_i] if rev else ring[pn]
            ft = bm.faces.new((va, vb, v_cap))
            ft.material_index = 1 if p_i < 5 else 0
            ft.smooth = True
            ft.loops[0][uv_layer].uv = (ua, wa)
            ft.loops[1][uv_layer].uv = (ub, wb)
            ft.loops[2][uv_layer].uv = (u_end, 0.55)

    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me

def create_b5_light_oak_chair_mesh():
    """
    Creates the Block 5 Light Natural Oak wooden armchair (Photo 14.30.53 (1).jpeg)
    for the two 10-pax wooden tables 419 and 484 using a SINGLE CONTINUOUS STEAM-BENT
    CURVED OAK BACKREST with explicit self-occlusion UVs and dark under-seat chassis:
    - Slot 0: Mat_Block5_Light_Oak_Wood (turned tapered legs, seat apron, continuous curved oak backrest)
    - Slot 1: Mat_Block5_Ivory_Shell (plush cream upholstered seat cushion)
    - Slot 2: Mat_Block5_Bronze_Pedestal (dark under-seat shadow chassis & floor glides)
    """
    me = bpy.data.meshes.new("B5_Chair_LightOak_Mesh")
    me.materials.append(mats["b5_light_oak"])
    me.materials.append(mats["b5_ivory_shell"])
    me.materials.append(mats["b5_Bronze_Ped"])
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # 0. Dark Under-Seat Chassis (Slot 2)
    add_smooth_squircle_cushion(bm, uv_layer, (0.0, 0.005, 0.400), rx=0.202, ry=0.195, z_bot=0.390, z_top=0.408, mat_idx=2, power=2.6, n_ang=28)

    # 1. Smooth Light-Oak Seat Frame Apron (mat_idx=0) & Plush Cream Cushion (mat_idx=1)
    add_smooth_squircle_cushion(bm, uv_layer, (0.0, 0.005, 0.422), rx=0.226, ry=0.218, z_bot=0.405, z_top=0.440, mat_idx=0, power=2.6, n_ang=36)
    add_smooth_squircle_cushion(bm, uv_layer, (0.0, 0.010, 0.456), rx=0.216, ry=0.210, z_bot=0.436, z_top=0.478, mat_idx=1, power=2.6, n_ang=36)

    # 2. 4 Smooth Turned Light-Oak Legs rising to support the continuous curved oak backrest
    for sx in (-1.0, 1.0):
        add_smooth_tapered_leg(bm, uv_layer, (sx * 0.215, 0.165, 0.0), (sx * 0.220, 0.145, 0.685), r_bot=0.014, r_top=0.019, mat_idx=0, segs=20, v_range=(0.08, 0.78))
        add_smooth_tapered_leg(bm, uv_layer, (sx * 0.195, -0.215, 0.0), (sx * 0.175, -0.185, 0.755), r_bot=0.015, r_top=0.020, mat_idx=0, segs=20, v_range=(0.08, 0.82))

    # 3. Single Continuous Steam-Bent Horseshoe Oak Backrest Band (41 smooth angular stations x 12 profile points)
    n_arc = 41
    n_prof = 12
    band_rings = []
    for i in range(n_arc):
        u = i / (n_arc - 1)
        ang = -1.68 + 3.36 * u
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)

        cx = 0.224 * sin_a
        cy = 0.015 - 0.205 * cos_a
        nx = sin_a
        ny = -cos_a

        side_f = abs(u - 0.5) * 2.0
        z_center = 0.728 - 0.032 * (side_f ** 1.5)
        half_h = 0.054 - 0.012 * (side_f ** 1.4)
        half_t = 0.014

        ring = []
        for p_i in range(n_prof):
            theta = 2.0 * math.pi * p_i / n_prof
            dr = half_t * math.cos(theta)
            dz = half_h * math.sin(theta)
            px = cx + nx * dr
            py = cy + ny * dr
            pz = z_center + dz
            ring.append(bm.verts.new((px, py, pz)))
        band_rings.append(ring)

    for i in range(n_arc - 1):
        u0 = (i / (n_arc - 1)) * 2.0
        u1 = ((i + 1) / (n_arc - 1)) * 2.0
        for p_i in range(n_prof):
            pn = (p_i + 1) % n_prof
            v0 = 0.12 + 0.76 * (0.5 + 0.5 * math.sin(2.0 * math.pi * p_i / n_prof))
            v1 = 0.12 + 0.76 * (0.5 + 0.5 * math.sin(2.0 * math.pi * pn / n_prof))
            f = bm.faces.new((band_rings[i][p_i], band_rings[i + 1][p_i], band_rings[i + 1][pn], band_rings[i][pn]))
            f.material_index = 0
            f.smooth = True
            f.loops[0][uv_layer].uv = (u0, v0)
            f.loops[1][uv_layer].uv = (u1, v0)
            f.loops[2][uv_layer].uv = (u1, v1)
            f.loops[3][uv_layer].uv = (u0, v1)

    for end_idx, rev in [(0, True), (-1, False)]:
        ring = band_rings[end_idx]
        c_co = sum((v.co for v in ring), Vector((0, 0, 0))) / len(ring)
        v_cap = bm.verts.new(c_co)
        for p_i in range(n_prof):
            pn = (p_i + 1) % n_prof
            verts_tri = (ring[pn], ring[p_i], v_cap) if rev else (ring[p_i], ring[pn], v_cap)
            ft = bm.faces.new(verts_tri)
            ft.material_index = 0
            ft.smooth = True
            for lp in ft.loops:
                lp[uv_layer].uv = (0.5, 0.5)

    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me

chair_teal_mesh = create_b5_teal_ivory_tub_chair_mesh()
chair_oak_mesh  = create_b5_light_oak_chair_mesh()

# Shared Tabletop Condiment / Menu Stand / Planter Set Mesh (matching Photos 14.30.44 (2) & 14.30.53 (1))
def create_b5_table_condiment_mesh():
    me = bpy.data.meshes.new("B5_TableCondiment_Mesh")
    me.materials.append(mats["chrome"])      # 0: Chrome shakers & menu holder base
    me.materials.append(mats["wall_white"])  # 1: Menu card & ceramic planter pot
    me.materials.append(mats["b5_pendant_green"])  # 2: Green succulent leaves
    bm = bmesh.new()

    def add_c(r1, r2, h, loc, mat_idx, segs=16):
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h)
        verts = ret["verts"]
        bmesh.ops.translate(bm, vec=loc, verts=verts)
        for f in bm.faces:
            if all(v in verts for v in f.verts):
                f.material_index = mat_idx
                f.smooth = True

    # Two sleek chrome & glass Salt & Pepper shakers
    add_c(0.014, 0.012, 0.068, (-0.032, -0.018, 0.034), mat_idx=0)
    add_c(0.014, 0.012, 0.068, (-0.002, -0.022, 0.034), mat_idx=0)

    # Upright Acrylic/Menu Card Stand
    ret = bmesh.ops.create_cube(bm, size=1.0)
    v_card = ret["verts"]
    bmesh.ops.scale(bm, vec=(0.006, 0.105, 0.165), verts=v_card)
    bmesh.ops.translate(bm, vec=(0.022, 0.0, 0.085), verts=v_card)
    for f in bm.faces:
        if all(v in v_card for v in f.verts):
            f.material_index = 1

    bm.to_mesh(me)
    bm.free()
    return me

condiment_mesh = create_b5_table_condiment_mesh()

def spawn_chair(name, chair_mesh, location, yaw_rad, col):
    obj = bpy.data.objects.new(name, chair_mesh)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, yaw_rad)
    link_to_collection(obj, col)
    return obj

def build_b5_table_assembly(table_id, center_xy, length_x, width_y, yaw_rad, top_mat, chair_mesh, pax_count, col, skip_side_b=False):
    t_col = get_or_create_collection(f"Table_{table_id}", parent=col)
    cx, cy = center_xy
    cos_a = math.cos(yaw_rad)
    sin_a = math.sin(yaw_rad)

    def to_world(lx, ly, lz):
        wx = cx + lx * cos_a - ly * sin_a
        wy = cy + lx * sin_a + ly * cos_a
        return (wx, wy, lz)

    # Soft feathered floor contact-shadow AO decal under the table & chairs (visible in both Material Preview & Rendered modes!)
    ao_obj = add_box(
        f"B5_FloorAO_{table_id}",
        (length_x + 0.72, width_y + 0.92, 0.002),
        to_world(0.0, 0.0, 0.0015),
        mats["b5_contact_ao"],
        t_col,
        rot=(0.0, 0.0, yaw_rad),
    )
    apply_normalized_top_uv(ao_obj)

    top_obj = add_box(
        f"TableTop_{table_id}",
        (length_x, width_y, 0.034),
        to_world(0.0, 0.0, 0.742),
        top_mat,
        t_col,
        bevel=0.005,
        rot=(0.0, 0.0, yaw_rad),
        uv_metric=0.55,
    )
    add_box(
        f"TableSubTop_{table_id}",
        (length_x - 0.08, width_y - 0.08, 0.022),
        to_world(0.0, 0.0, 0.715),
        mats["b5_Bronze_Ped"],
        t_col,
        rot=(0.0, 0.0, yaw_rad),
    )

    if length_x <= 1.0:
        ped_xs = [0.0]
    elif length_x <= 1.65:
        ped_xs = [-length_x * 0.28, length_x * 0.28]
    else:
        ped_xs = [-length_x * 0.35, -length_x * 0.12, length_x * 0.12, length_x * 0.35]

    for i, px in enumerate(ped_xs):
        add_cylinder(
            f"PedBase_{table_id}_{i}",
            radius=0.23,
            depth=0.016,
            location=to_world(px, 0.0, 0.008),
            mat=mats["b5_Bronze_Ped"],
            col=t_col,
        )
        add_cylinder(
            f"PedCol_{table_id}_{i}",
            radius=0.042,
            depth=0.70,
            location=to_world(px, 0.0, 0.36),
            mat=mats["b5_Bronze_Ped"],
            col=t_col,
        )

    chairs_per_side = max(1, pax_count // 2)
    if chairs_per_side == 1:
        chair_xs = [0.0]
    elif chairs_per_side == 2:
        chair_xs = [-length_x * 0.27, length_x * 0.27]
    else:
        span = length_x * 0.80
        chair_xs = [-span * 0.5 + span * (k / (chairs_per_side - 1)) for k in range(chairs_per_side)]

    chair_offset_y = width_y * 0.5 + 0.18
    for c_i, ch_x in enumerate(chair_xs):
        spawn_chair(
            f"Chair_{table_id}_A{c_i+1}",
            chair_mesh,
            to_world(ch_x, -chair_offset_y, 0.0),
            yaw_rad,
            t_col,
        )
        if not skip_side_b:
            spawn_chair(
                f"Chair_{table_id}_B{c_i+1}",
                chair_mesh,
                to_world(ch_x, chair_offset_y, 0.0),
                yaw_rad + math.pi,
                t_col,
            )

    # Spawn tabletop Salt & Pepper shakers + Acrylic Menu Stand (matching Photos 14.30.44 (2) & 14.30.53 (1))
    cond_xs = [-1.05, 0.0, 1.05] if length_x > 2.0 else [0.0]
    for cd_i, cd_x in enumerate(cond_xs):
        c_obj = bpy.data.objects.new(f"B5_Condiment_{table_id}_{cd_i}", condiment_mesh)
        c_obj.location = to_world(cd_x, 0.0, 0.759)
        c_obj.rotation_euler = (0.0, 0.0, yaw_rad)
        link_to_collection(c_obj, t_col)

    return top_obj

# ------------------------------------------------------------------------------
# A. BARIS SOFA FORWARD — PORTSIDE (5 Tables: 319 [2x], 317 [4x], 385 [2x], 387 [4x], 415 [2x])
#    At X = 29.18m, yaw = +pi/2 so Side A (+X) has chairs facing -X toward the sofa, Side B (-X) skipped!
# ------------------------------------------------------------------------------
b5_sofa_port_specs = [
    ("319_B5_SofaPort_2Pax", 0.65, 0.78, 2),
    ("317_B5_SofaPort_4Pax", 2.15, 1.40, 4),
    ("385_B5_SofaPort_2Pax", 3.80, 0.78, 2),
    ("387_B5_SofaPort_4Pax", 5.45, 1.40, 4),
    ("415_B5_SofaPort_2Pax", 6.95, 0.78, 2),
]
for tid, ty, tlen, tpax in b5_sofa_port_specs:
    build_b5_table_assembly(tid, (29.18, ty), tlen, 0.78, math.pi * 0.5, mats["b5_dark_wood_top"], chair_teal_mesh, tpax, furn_col_b5, skip_side_b=True)

# ------------------------------------------------------------------------------
# B. BARIS SOFA FORWARD — STARBOARDSIDE (5 Tables: 480 [2x], 450 [4x], 448 [2x], 400 [4x], 398 [2x])
# ------------------------------------------------------------------------------
b5_sofa_stbd_specs = [
    ("480_B5_SofaStbd_2Pax", 10.51, 0.78, 2),
    ("450_B5_SofaStbd_4Pax", 12.01, 1.40, 4),
    ("448_B5_SofaStbd_2Pax", 13.66, 0.78, 2),
    ("400_B5_SofaStbd_4Pax", 15.31, 1.40, 4),
    ("398_B5_SofaStbd_2Pax", 16.81, 0.78, 2),
]
for tid, ty, tlen, tpax in b5_sofa_stbd_specs:
    build_b5_table_assembly(tid, (29.18, ty), tlen, 0.78, math.pi * 0.5, mats["b5_dark_wood_top"], chair_teal_mesh, tpax, furn_col_b5, skip_side_b=True)

# ------------------------------------------------------------------------------
# C. BARIS MEJA JENDELA PORTSIDE (6 Tables: 321/323, 327/325, 329/331)
#    Each pair has a 4x table near window (Y = 0.92m) + a 2x table attached inboard (Y = 1.99m)
# ------------------------------------------------------------------------------
b5_port_win_pairs = [
    (31.85, "321_B5_WinPort_4Pax", "323_B5_WinPort_2Pax"),
    (34.35, "327_B5_WinPort_4Pax", "325_B5_WinPort_2Pax"),
    (36.85, "329_B5_WinPort_4Pax", "331_B5_WinPort_2Pax"),
]
for tx, tid_4x, tid_2x in b5_port_win_pairs:
    build_b5_table_assembly(tid_4x, (tx, 0.92), 1.36, 0.80, math.pi * 0.5, mats["b5_dark_wood_top"], chair_teal_mesh, 4, furn_col_b5)
    build_b5_table_assembly(tid_2x, (tx, 1.99), 0.74, 0.80, math.pi * 0.5, mats["b5_dark_wood_top"], chair_teal_mesh, 2, furn_col_b5)

# ------------------------------------------------------------------------------
# D. BARIS MEJA TEMBOK STARBOARDSIDE (6 Tables: 404/402, 406/408, 412/410)
#    Shifted +1.00m toward Aft (+X) relative to Portside window tables for Block 6 access!
# ------------------------------------------------------------------------------
b5_stbd_wall_pairs = [
    (32.85, "404_B5_WallStbd_4Pax", "402_B5_WallStbd_2Pax"),
    (35.10, "406_B5_WallStbd_4Pax", "408_B5_WallStbd_2Pax"),
    (37.35, "412_B5_WallStbd_4Pax", "410_B5_WallStbd_2Pax"),
]
for tx, tid_4x, tid_2x in b5_stbd_wall_pairs:
    build_b5_table_assembly(tid_4x, (tx, 16.54), 1.36, 0.80, math.pi * 0.5, mats["b5_dark_wood_top"], chair_teal_mesh, 4, furn_col_b5)
    build_b5_table_assembly(tid_2x, (tx, 15.47), 0.74, 0.80, math.pi * 0.5, mats["b5_dark_wood_top"], chair_teal_mesh, 2, furn_col_b5)

# ------------------------------------------------------------------------------
# E. AREA MEJA TENGAH DI ATAS KARPET HIJAU (10 Tables)
#    1. 4 Forward 4x Tables at X = 31.85m: 383, 417, 482, 446
#    2. 2 Long Light-Oak 10x Tables at X = 35.55m (length = 3.60m -> X = 33.75m .. 37.35m): 419 & 484
#    3. 4 Side 4x Tables (length = 1.45m):
#       - 381 & 444 at X = 34.475m -> Forward edge = 34.475 - 0.725 = 33.750m (EXACTLY aligned with 419 & 484!)
#       - 379 & 442 at X = 36.625m -> Aft edge = 36.625 + 0.725 = 37.350m (EXACTLY aligned with 419 & 484!)
# ------------------------------------------------------------------------------
b5_center_fwd_4x = [
    ("383_B5_CenterFwd_4Pax", 4.55),
    ("417_B5_CenterFwd_4Pax", 7.35),
    ("482_B5_CenterFwd_4Pax", 10.11),
    ("446_B5_CenterFwd_4Pax", 12.91),
]
for tid, ty in b5_center_fwd_4x:
    build_b5_table_assembly(tid, (31.85, ty), 1.45, 0.82, 0.0, mats["b5_dark_wood_top"], chair_teal_mesh, 4, furn_col_b5)

# 2 Long Light-Oak Wooden 10-Pax Tables (419 & 484) with Light-Oak Wooden Chairs!
build_b5_table_assembly("419_B5_CenterWood_10Pax", (35.55, 7.35),  3.60, 0.92, 0.0, mats["b5_light_oak"], chair_oak_mesh, 10, furn_col_b5)
build_b5_table_assembly("484_B5_CenterWood_10Pax", (35.55, 10.11), 3.60, 0.92, 0.0, mats["b5_light_oak"], chair_oak_mesh, 10, furn_col_b5)

# 4 Side 4-Pax Tables flanking 419 and 484 (381, 379 on Portside; 444, 442 on Starboardside)
b5_center_side_4x = [
    ("381_B5_CenterSide_4Pax", 34.475, 4.55),
    ("379_B5_CenterSide_4Pax", 36.625, 4.55),
    ("444_B5_CenterSide_4Pax", 34.475, 12.91),
    ("442_B5_CenterSide_4Pax", 36.625, 12.91),
]
for tid, tx, ty in b5_center_side_4x:
    build_b5_table_assembly(tid, (tx, ty), 1.45, 0.82, 0.0, mats["b5_dark_wood_top"], chair_teal_mesh, 4, furn_col_b5)

# ==============================================================================
# 10. CONFIGURE VIEWPORT SHADING / COLOR MANAGEMENT, SAVE .BLEND AND EXPORT .GLB
# ==============================================================================
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = -0.15
except Exception:
    pass

for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.show_cavity = True
                    sp.shading.cavity_type = 'BOTH'
                    sp.shading.cavity_ridge_factor = 1.25
                    sp.shading.cavity_valley_factor = 1.45
                    sp.shading.use_scene_lights = True
                    sp.shading.use_scene_world = False

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format='GLB',
    export_apply=True,
    export_materials='EXPORT',
)
print("SUCCESS: Built Block 5 (Green Zone) with dark coffered ceiling, 68 spotlights, calibrated Linear RGB & AO textures, and 32 tables!")
