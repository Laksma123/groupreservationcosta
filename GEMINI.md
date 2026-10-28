# INSTRUCTIONS FOR ALL AI AGENTS (GEMINI ARGON & CO.)

> **CRITICAL REQUIREMENT AT CONVERSATION START:**
> Every time you start a conversation or receive a new task in this workspace, you **MUST IMMEDIATELY READ** the master plan and specifications file:
> 📄 [PLAN_RESERVASI_COSTA_SMERALDA_3D.md](file:///Users/dianjulie/Documents/Map%20Project/PLAN_RESERVASI_COSTA_SMERALDA_3D.md)
> 
> Do **NOT** assume this is a standard public cruise website or a generic 3D demo. It is a specialized **B2B Group Dining Reservation System (DRS Portal)** for Costa Cruises.

---

## 1. Project Context & Background (Why this exists)
* **The Client/Company:** Costa Cruises (specifically *Costa Smeralda* / Excellence Class).
* **The Origin & Problem:**
  Shoreside office and onboard DRS (Dining Reservation System) currently use a 2008-era manual workflow for Group Bookings (corporate groups, large families, incentive travel with 20–100+ pax who want tables close to each other):
  1. User previously created a 2D floor plan map in Microsoft Excel using shapes for a corporate contact.
  2. Shoreside emails this Excel/PDF map via Outlook to Group Leaders.
  3. Group Leaders manually draw transparent shapes in Outlook to highlight requested tables.
  4. Group Leaders email back the screenshot.
  5. Shoreside / onboard DRS team manually enters it into the ship database.
* **The Solution Being Built:**
  A modern, sleek **Costa Group DRS Web Portal**:
  * Group Leader inputs a secret access code provided by the ship's DRS team (e.g., `A98XKJ90`).
  * The code automatically loads the designated restaurant and blocks unavailable/already booked tables.
  * Features a **Dual View**:
    1. **3D Interactive Model:** Cutaway view of the ship zooming into the restaurant with glassmorphic hover effects, sea-view simulation, and clickable 3D tables.
    2. **2D Interactive Floor Plan:** A modernized, interactive web version of the user's Excel map where tables can be clicked/toggled seamlessly.
* **Current Active Phase & Priority:**
  1. **PHASE 1 (CURRENT FOCUS):** 100% focus on creating the **3D Model in Blender** (*Ristorante Arlecchino Deck 6 Mid-Ship* — Block 1 Portside, Block 2 Starboardside, and the Aft Crossroads with the Clover Table & Chandelier).
  2. **2D Excel Map Status:** The user is currently finalizing the 2D floor plan manually and will export it as PDF later. Do NOT attempt to build the 2D map yet.
  3. **Phase 2:** Web 3D integration & interactive portal.

---

## 1B. Mandatory Spatial Orientation & Coordinate Convention (ARLECCHINO)
All agents MUST use this exact terminology and coordinate convention without exception:
* **Block 1 = Portside Forward (Left Side of Ship / Kiri Kapal — Forward of Clover):**
  * Blender `X = -1.55m .. +10.40m`, `Y = 0.00m .. 7.58m` (Three.js `Z = 0.00m .. -7.58m`).
  * 10 Tables (52 Seats): Window Row (`301, 303, 305, 307`), Center Row (`399, 397, 393`), Railing Row (`403, 405, 407`).
* **Block 2 = Starboardside Forward (Right Side of Ship / Kanan Kapal — Forward of Clover):**
  * Blender `X = -1.95m .. +10.40m`, `Y = 9.88m .. 17.46m` (Three.js `Z = -9.88m .. -17.46m`).
  * 14 Tables (60 Seats): Railing Row (`468, 470, 472`), Center Row (`462, 460, 458`), Forward Entrance 2 Booths (`466, 464`), Inboard Sofa Wall (`374, 376, 378, 380, 382, 384`).
* **Block 3 = Portside Aft (Left Side of Ship / Kiri Kapal — Aft of Clover, exact mirror of Block 1 across `X = 12.90m` via $M(x) = 25.80 - x$):**
  * Blender `X = 15.40m .. 27.35m`, `Y = 0.00m .. 7.58m` (Three.js `Z = 0.00m .. -7.58m`).
  * 9 Tables (54 Seats): 4 Freestanding Window Tables without sofa (`309, 311, 313, 315`), 2 Long Maroon Velvet Center Tables shifted +50 cm Aft (`391` for 8 chairs at `X = 19.05m`, `389` for 10 chairs at `X = 23.45m`), 3 Railing Row Tables (`409, 411, 413` centered on the 3 wide pillars).
  * 2 Waiter Stations: Station #1 (`Rect 7`) mirrored at Aft Entrance 2 wall (`X = 27.35m`), and 1-Set Station #2 (`Rect 5`, long left + 1 center partition + short right, bounded by walls on left & right) behind Pintu Masuk Pertama wall (`X = 15.40m .. 16.05m, Y = 2.39m .. 4.15m`), with the window-corner wall (`Y = 0.00m .. 2.25m`) recessed inward to `X = 15.45m` (`tikungan kecil` at `Y = 2.25m`, no sofa) so Table `309`'s Forward chairs have ample clearance.
* **Block 4 = Starboardside Aft (Right Side of Ship / Kanan Kapal — Aft of Clover, aligned with Block 2):**
  * Blender `X = 15.40m .. 27.35m`, `Y = 9.88m .. 17.46m` (Three.js `Z = -9.88m .. -17.46m`).
  * 12 Tables (54 Seats): 3 Railing Row Tables (`474, 476, 478` centered on the 3 wide pillars), 3 Maroon Velvet Center Tables (`456, 454, 452`, no Entrance 2 sofa tables, shifted +50 cm toward Aft relative to Railing Row), 6 Inboard Sofa Wall 4-Pax Tables (`386, 388, 390, 392, 394, 396`, all 4-pax without any 2-pax tables).
  * 2 Waiter Stations: Identical layout to Block 3 (Station #1 `Rect 8/6` at Aft Entrance 2 wall `X = 27.35m`, Station #2 `Rect 6` behind Pintu Masuk Pertama wall `X = 15.40m .. 16.05m`).
* **Block 5 = Area Hijau / Green Zone Aft (Unified Full-Width Dining Room Behind Block 3 & Block 4):**
  * Blender `X = 28.15m .. 41.20m`, `Y = 0.00m .. 17.46m` (Three.js `Z = 0.00m .. -17.46m`), spanning the full width of 2 blocks + 1 corridor without a dividing central corridor.
  * Floor Transition: Surrounding wood plank walkway (`Mat_Block5_Wood_Plank_Floor`) around the central Green Arlecchino pattern carpet (`Mat_Block5_Green_Carpet`, `X = 30.65m .. 37.80m, Y = 3.36m .. 14.10m`).
  * 32 Tables (116 Seats) in Collection `06_Furniture_Block5_GreenZone`:
    * Forward Sofa Row — Portside (`X = 29.18m`): `319` (`2x`) ➔ `317` (`4x`) ➔ `385` (`2x`) ➔ `387` (`4x`) ➔ `415` (`2x`), with a see-through decorative vase niche (`Niche_B3_Port`, `Y = 2.25..5.33m`) backing Block 3's Waiter Station and 9 Fornasetti plates on both sides of the solid outer wall (`Y = 0.00..2.25m`).
    * Forward Sofa Row — Starboardside (`X = 29.18m`): `480` (`2x`) ➔ `450` (`4x`) ➔ `448` (`2x`) ➔ `400` (`4x`) ➔ `398` (`2x`), with a see-through decorative vase niche (`Niche_B4_Stbd`, `Y = 12.13..15.21m`) backing Block 4's Waiter Station and 9 Fornasetti plates on both sides of the solid wall (`Y = 15.21..17.46m`).
    * Portside Window Pairs (`4x` at `Y = 0.92m` + attached inboard `2x` at `Y = 1.99m`): `321/323` (`X = 31.85m`), `327/325` (`X = 34.35m`), `329/331` (`X = 36.85m`).
    * Starboardside Wall Pairs (`4x` at `Y = 16.54m` + attached inboard `2x` at `Y = 15.47m`, shifted +1.00m Aft relative to Portside to leave the Block 6 access portal between `398/400` and `404/402`): `404/402` (`X = 32.85m`), `406/408` (`X = 35.10m`), `412/410` (`X = 37.35m`).
    * Central Green Carpet Tables: 4 Forward `4x` tables (`383, 417, 482, 446` at `X = 31.85m`), 2 Long `10x` Light-Oak Wooden Tables (`419` at `Y = 7.35m` & `484` at `Y = 10.11m`, `X = 33.75..37.35m`) with 6 Murano glass pendant chandeliers above them, and 4 Side `4x` tables (`381, 379` on Portside `Y = 4.55m`; `444, 442` on Starboardside `Y = 12.91m`, with the Forward edge of `381` & `444` aligned at `X = 33.75m` with `419` & `484`).
    * Aft Patterned Glass Partition Wall (`X = 37.80m, Y = 3.36..14.10m`), plus Patterned Metal Grille Partitions & 6 Sets of L-Shaped Waiter Stations (`3 sets per side: 1 set behind the table + 2 sets along the wall`) behind `329/331` (Portside) and `410/412` (Starboardside).
* **Central Corridor (Garis Koridor Tengah):**
  * Blender `Y = 7.58m .. 9.88m` (Centerline at `Y = 8.73m`). Uses the black-bordered geometric runner tile (`Mat_Corridor_Geometric_Tile`) between Block 1 & 2 (`X = -1.95m .. 10.40m`) and between Block 3 & 4 (`X = 15.40m .. 28.15m`).
* **Pintu Masuk Pertama (Entrance 1):**
  * All entrances adjacent to the **L-shaped corner railings (`pagar siku`)** (`407` & `472` at `X = 10.15m`, and `409` & `474` at `X = 15.65m`).
* **Aft Corridor Crossroads (`Perempatan Koridor`, `X = 10.40m .. 15.40m`):**
  * Centered at `X = 12.90m, Y = 8.73m` with equal symmetry to Blocks 1–2 and Blocks 3–4, featuring the **4-Leaf Clover Table (`Meja Clover`, 4 × Ø100cm discs with Portside & Starboardside leaves higher than Forward & Aft leaves)** and the **Grand Murano Chandelier** inside a circular recessed dome ceiling.

---

## 1C. Mandatory Visual Consistency, Lighting & Contrast Rules (ALL ROOMS & RESTAURANTS)
To prevent wasted rework across any block or restaurant room, all agents MUST strictly enforce these rules:
1. **Bright Room Illumination + Deep Object Contrast (WAJIB SERAGAM DI SEMUA RUANGAN):**
   * **Never make a room dark or gloomy.** Every dining block/room must have bright, inviting, even illumination in both Blender `Material Preview` and `Rendered` modes (`Arlecchino_World` strength `~0.92`, `AgX - Medium High Contrast`, `exposure = +0.22`, `use_scene_lights = True`, `use_scene_world = True`).
   * Combine downward shadow-casting ceiling `SPOT` lights (`88W–108W`, `cutoff_distance = 8.5m`, `shadow_pool_size = '1024'`) with **shadowless warm `AREA` room-bounce fill lights** (`62W–75W`, `use_shadow = False`, `specular_factor = 0.0`) so walls, ceilings, and furniture are brightly lit without overflowing EEVEE's shadow buffer or causing white specular orbs on glass/windows.
   * **Never crush base texture midtones/highlights to create contrast.** Keep base material/texture colors bright and true-to-life; achieve 3D depth and contrast via **baked underside/crevice self-occlusion gradients, crisp plank/seam bevels, bump normal maps, and soft feathered contact-shadow AO decals (`block5_contact_ao.png`)** under tables, chairs, and pillars.
2. **Clean Empty Tabletops (`Meja Kosong Tanpa Menaje`):**
   * All dining tables across all blocks (`Block 1` through `Block 5` and future blocks) must have **100% clean, empty tabletops** (no salt/pepper shakers, menus, tableware, or planters on the tables).
3. **Continuous Seamless Curved Furniture Geometry:**
   * All curved chairs (such as Block 5's two-tone tub chairs and steam-bent oak chairs) must use continuous lofted `BMesh` / `Subsurf` geometry with smooth normals—never faceted low-poly segments.
4. **Block 5 Specific Architectural Rules Verified:**
   * The 2 middle Amber/Orange Murano chandeliers (`MidAmber` at `X = 35.55m`) extend **30 cm lower** (`z_bottom = 1.42m`, `total_h = 1.40m` with 4 stem boules) than the 4 Green chandeliers (`z_bottom = 1.72m`, `total_h = 1.10m`), staying `~68 cm` clear above the `0.74m` tabletop.
   * Both see-through vase niches (`Niche_B3_Port` and `Niche_B4_Stbd`) are **100% open hollow wall openings without any glass panes (`dinding bolong tanpa kaca`)** on both the Block 3/4 side and the Block 5 side.
5. **Separated Blender Asset Files for Heavy Dynamic Systems (NPCs):**
   * Keep the restaurant architecture in `arlecchino_block1.blend` / `arlecchino_block1.glb`, and build the **15 European-proportioned rigged & animated 3D human NPCs** (5 adult men, 5 adult women, 5 children ages 3–5) in a **separate Blender file & GLB (`arlecchino_npcs_european.blend` / `arlecchino_npcs_european.glb`)** so the main architectural scene stays lightweight and fast.

---

## 2. Key Local References in This Repo
1. **Master Plan:** [PLAN_RESERVASI_COSTA_SMERALDA_3D.md](file:///Users/dianjulie/Documents/Map%20Project/PLAN_RESERVASI_COSTA_SMERALDA_3D.md)
2. **Shipyard GA Blueprints:** [SHIP MAP.pdf](file:///Users/dianjulie/Documents/Map%20Project/SHIP%20MAP.pdf) — **Sheet 4 (Page 4) covers Deck 6 & 61** (*Meyer Turku General Arrangement*).
3. **Official Booklet:** [SHIP PLAN OVERVIEW BOOKLET.pdf](file:///Users/dianjulie/Documents/Map%20Project/SHIP%20PLAN%20OVERVIEW%20BOOKLET.pdf) (Arlecchino 652 seats on Deck 6, Il Meneghino 886 seats on Deck 5, Il Rugantino 546 seats on Deck 7).
4. **Passenger Map:** [SHIP MAP SMERALDA.pdf](file:///Users/dianjulie/Documents/Map%20Project/SHIP%20MAP%20SMERALDA.pdf) (Deck 6 "Roma").
5. **Real On-Site Photos:** [Arlecchino 1st Block Starboardside/](file:///Users/dianjulie/Documents/Map%20Project/Arlecchino%201st%20Block%20Starboardside) (8 high-res photos of tables, chairs, carpets, lighting, windows).

---

## 3. Tooling Environment & Git Tracking Rule
* **Blender 5.2.3 LTS:** Installed at `/Applications/Blender.app/Contents/MacOS/Blender`.
* **Blender MCP Server:** Installed globally (`@three-ws/blender-mcp`) and configured in `~/.gemini/config/mcp_config.json`.
* **Node.js:** v22.17.0.
* **Python:** 3.13 with `fitz` (PyMuPDF) and Tesseract OCR installed.
* **GitHub Repository & Project Tracker (MANDATORY):**
  * **Repo URL:** `https://github.com/Laksma123/groupreservationcosta`
  * **Rule:** Always commit and push changes (`git add`, `git commit`, `git push`) to `https://github.com/Laksma123/groupreservationcosta` after meaningful 3D model updates or web milestones so the repository serves as an up-to-date project tracker, backup, and GitHub Pages web preview domain.
