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
* **Block 1 = Portside (Left Side of Ship / Kiri Kapal):**
  * Blender `Y = 0.00m .. 7.58m` (Three.js `Z = 0.00m .. -7.58m`).
  * 10 Tables (52 Seats): Window Row (`301, 303, 305, 307`), Center Row (`399, 397, 393`), Railing Row (`403, 405, 407`).
* **Block 2 = Starboardside (Right Side of Ship / Kanan Kapal):**
  * Blender `Y = 9.88m .. 17.46m` (Three.js `Z = -9.88m .. -17.46m`).
  * 14 Tables (60 Seats): Railing Row (`468, 470, 472`), Center Row (`462, 460, 458`), Forward Entrance 2 Booths (`466, 464`), Inboard Sofa Wall (`374, 376, 378, 380, 382, 384`).
* **Central Corridor (Garis Koridor Tengah):**
  * Blender `Y = 7.58m .. 9.88m` (Centerline at `Y = 8.73m`).
* **Forward (Arah Depan Kapal):**
  * Blender `-X` (`X = -1.55m .. -1.95m`): Side where **Entrance 2 (Pintu Kedua)** is located in both Block 1 (near `301` & Double Waiter Station) and Block 2 (near `466, 464` & Waiter Station 1).
* **Aft (Arah Belakang Kapal):**
  * Blender `+X` (`X = +10.15m` and beyond): Side where **Entrance 1 (Pintu Masuk Pertama)** and the **L-shaped corner railings (`pagar siku`)** (`407` & `472`) are located.
  * Behind (Aft of) Block 1 and Block 2 with a ~2m gap (`X ≈ 12.90m, Y = 8.73m`) is the **Aft Corridor Crossroads (`Perempatan Koridor`)** featuring the **4-Leaf Clover Table (`Meja Clover`, 4 × Ø100cm discs with Portside & Starboardside leaves higher than Forward & Aft leaves)** and the **Grand Murano Chandelier** inside a circular recessed dome ceiling. (Blocks 3 & 4 lie further Aft behind this crossroads).

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
