# COSTA GROUP DINING RESERVATION SYSTEM (DRS PORTAL)
## Master Plan, Business Architecture & Technical Specification
**Ship Target:** *Costa Smeralda* (Excellence Class)  
**Pilot Dining Venue:** *Ristorante Arlecchino* — Ponte/Deck 6 (Roma), Mid-Ship Starboard Block 1  
**Project Objective:** Modernizing Group Dining Reservations for Costa Shoreside & Onboard DRS

---

> [!IMPORTANT]
> **STATUS PRIORITAS SAAT INI (FASE 1: 100% 3D MODELING DI BLENDER):**
> 1. **Fokus Penuh pada 3D Model di Blender:** Pembuatan model 3D realistis *Ristorante Arlecchino Deck 6 Mid-Ship Starboard Block 1*.
> 2. **Denah 2D Excel:** Sedang diselesaikan secara manual oleh user dan akan diekspor ke PDF saat final. Agent **TIDAK PERLU** membuat denah 2D sekarang.
> 3. **Website Development:** Ditunda terlebih dahulu (*Hold*). Semua fokus saat ini tertuju pada kualitas hasil visual 3D model di Blender sampai disetujui.

---

## 1. Executive Summary & Latar Belakang (The Origin Story)

### A. Masalah Nyata yang Dihadapi Costa Saat Ini (The 2008-Era Pain Point)
Costa Cruises memiliki ribuan tamu grup setiap pekannya (rombongan keluarga besar, grup insentif korporat, *Costa Club Diamond groups*, agen perjalanan) yang membutuhkan **meja makan malam yang berdekatan atau dalam satu blok yang sama** di restoran utama.

Saat ini (menuju 2027 di era AI), alur kerja reservasi grup antara kantor darat (*shoreside office*) dan kapal (*onboard DRS team*) masih sangat manual dan kuno:
1. Pihak *corporate / shoreside* menggunakan denah restoran 2D sederhana yang dibuat di Microsoft Excel menggunakan fitur *shapes*.
2. Kantor darat mengirimkan denah Excel/PDF ini kepada **Group Leader** melalui email Microsoft Outlook.
3. Group Leader membuka email, mencoba menerka situasi restoran, lalu menggambar secara manual *shapes* transparan di Outlook untuk menandai meja yang diinginkan.
4. Group Leader membalas email dengan *screenshot* denah yang telah dicoret/di-highlight secara manual.
5. Tim reservasi darat dan tim DRS di kapal harus membaca hasil coretan tersebut satu per satu dan menginputnya secara manual ke dalam sistem restoran kapal.

**Dampak Negatif Sistem Manual:**
* Memakan waktu berhari-hari hanya untuk mencocokkan meja grup.
* Risiko tinggi salah catat nomor meja, bentrok meja (*double booking*), atau meja terpisah.
* Pengalaman pelanggan (*guest experience*) terasa sangat kuno untuk kapal mewah kelas dunia seperti Costa Smeralda.

### B. Solusi Jangka Panjang: "Costa Group DRS Web Portal"
Sebuah portal web modern, cepat, dan presisi tinggi khusus untuk **Reservasi Grup (Group Dining)**:
* **Token Akses Rahasia (Secret Access Code):** Diberikan oleh tim DRS kapal / shoreside kepada Group Leader (misal: `A98XKJ90`).
* **Otomasi Blok Meja:** Ketika kode dimasukkan, sistem otomatis memuat restoran yang ditentukan, mengunci meja yang sudah terisi (*blocked/unavailable*), dan hanya membuka area/blok meja yang dialokasikan untuk grup tersebut.
* **Dual-View Interaktif (3D + 2D):**
  1. **3D Interactive Digital Twin:** Model 3D nyata restoran dengan efek potong kapal (*cutaway*), efek melayang halus (*glassmorphism hover*), simulasi pemandangan jendela laut (*sea-view*), dan klik meja untuk memilih kursi.
  2. **2D Interactive Web Schematic:** Evolusi modern dari denah Excel yang interaktif di web, di mana Group Leader bisa klik meja secara langsung. *(Catatan: Denah 2D saat ini sedang diselesaikan manual oleh user via Excel/PDF).*
* **Live Group Pax Counter:** Menghitung kapasitas secara langsung (misal: *Target Grup: 28 Pax | Terpilih: 24/28 Pax | Sisa: 4 Kursi*).
* **Konfirmasi Seketika:** Begitu Group Leader menekan tombol *"Confirm Group Seating"*, data langsung terekam rapi, menghasilkan kode reservasi resmi dan dokumen ringkasan untuk tim DRS kapal.

---

## 2. Aset & Bahan Baku Referensi Lokal

Seluruh file referensi teknis dan visual sudah tersedia di folder lokal:

### 1. Cetak Biru Resmi Galangan (*Shipyard GA Drawing - Meyer Turku*)
* **File:** [SHIP MAP.pdf](file:///Users/dianjulie/Documents/Map%20Project/SHIP%20MAP.pdf)
* **Lembar Utama: Halaman 4 (Sheet 4/10: `DECKS 6 AND 61`)**
  * Dokumen asli arsitektur dari galangan Meyer Turku Oy (Finlandia) untuk pembuatan kapal Costa Smeralda (NB-1394).
  * **Deck 6 (Roma) Mid-Ship:** Memuat denah teknis presisi *Ristorante Arlecchino* (kode ruangan 06... / Flex Restaurant), posisi kolom/pilar struktural, jendela lambung kanan (*starboard side*), pintu masuk koridor tamu, serta jalur servis *kitchen/galley*.

### 2. Panduan Kapasitas & Denah Publik
* **File:** [SHIP PLAN OVERVIEW BOOKLET.pdf](file:///Users/dianjulie/Documents/Map%20Project/SHIP%20PLAN%20OVERVIEW%20BOOKLET.pdf)
  * Rektorat restoran utama Costa Smeralda:
    * **Deck 6 (Roma):** *Ristorante Arlecchino* (Kapasitas: 652 kursi) & *Il Rugantino* (546 kursi).
    * **Deck 5 (Matera):** *Il Meneghino* (886 kursi).
    * **Deck 7 (Positano):** *La Sagra dei Sapori Buffet* (832 kursi).
* **File:** [SHIP MAP SMERALDA.pdf](file:///Users/dianjulie/Documents/Map%20Project/SHIP%20MAP%20SMERALDA.pdf)
  * Peta publik Costa Smeralda untuk cross-check nomor deck dan area publik (Deck 6 "Roma").

### 3. Dokumentasi Foto Asli Interior (8 Foto Resolusi Tinggi 4032 x 2268 px)
* **Folder:** [Arlecchino 1st Block Starboardside/](file:///Users/dianjulie/Documents/Map%20Project/Arlecchino%201st%20Block%20Starboardside)
* **Detail Visual Nyata:**
  * **Meja Makan:** Meja persegi panjang marmer putih dengan urat abu-abu elegan (*white Carrara marble style*), penyangga kaki besi hitam.
  * **Kursi Tamu:**
    * *Varian A:* Kursi beludru merah marun (*rich burgundy velvet*).
    * *Varian B:* Kursi kulit lembut warna gading/krem terang (*ivory leatherette / upholstered*).
  * **Lantai/Karpet:** Karpet motif geometris motif kipas segitiga merah marun, hitam, dan putih (tema Arlecchino / Venetian).
  * **Dinding & Jendela:** Jendela laut panorama dengan tirai lipat Romawi (*Roman blinds*) krem bergaris merah; pilar putih klasik dengan *red wainscoting* di bagian bawah.
  * **Plafon:** *Coffered ceiling* berpetak kayu gelap dengan *cove LED lighting* dan lampu aksen merah.
  * **Railing:** Pegangan kayu cokelat tua dengan kisi-kisi silang *X-cross baluster*.

---

## 3. Kondisi Tool, Git Tracker & Persiapan Lingkungan di Mac

* **Blender 5.2.3 LTS:** `/Applications/Blender.app/Contents/MacOS/Blender`.
* **Blender MCP Server (`@three-ws/blender-mcp`):** Terpasang secara global (`npm -g`) dan terdaftar di `~/.gemini/config/mcp_config.json`.
* **Direct Scripting Headless:** Teruji dan dapat mengeksekusi script Python `bpy` untuk mengolah mesh, memotong geometri, dan meng-export file `.glb`.
* **GitHub Repository & Backup Tracker (WAJIB PUSH COMMIT):**
  * **Repository:** `https://github.com/Laksma123/groupreservationcosta`
  * Setiap progres 3D model maupun pengembangan web wajib di-*commit* dan di-*push* ke GitHub sebagai *project tracker*, *backup*, serta untuk *deployment* percobaan via GitHub Pages.

---

## 4. Rencana Tahap Eksekusi & Konvensi Orientasi Spasial

### Konvensi Orientasi Kapal (Wajib Dipatuhi):
* **Block 1 = Portside Forward (Kiri Kapal — Depan Clover):** Blender `X = -1.55m .. +10.40m`, `Y = 0.00m .. 7.58m` (`301, 303, 305, 307`, `399, 397, 393`, `403, 405, 407`).
* **Block 2 = Starboardside Forward (Kanan Kapal — Depan Clover):** Blender `X = -1.95m .. +10.40m`, `Y = 9.88m .. 17.46m` (`468, 470, 472`, `462, 460, 458`, `466, 464`, `374, 376, 378, 380, 382, 384`).
* **Block 3 = Portside Aft (Kiri Kapal — Belakang Clover, mirror presisi dari Block 1 terhadap `X = 12.90m`):** Blender `X = 15.40m .. 27.35m`, `Y = 0.00m .. 7.58m` (9 meja / 54 kursi: 4 meja jendela tanpa sofa `309, 311, 313, 315`, 2 meja merah panjang `391` [8 kursi] & `389` [10 kursi], 3 meja pagar `409, 411, 413`, serta 2 Waiter Station: `Rect 7` mirror di dinding Entrance 2 Aft dan `Rect 5` di belakang tembok Pintu Masuk Pertama).
* **Block 4 = Starboardside Aft (Kanan Kapal — Belakang Clover, sejajar Block 2):** Blender `X = 15.40m .. 27.35m`, `Y = 9.88m .. 17.46m` (12 meja / 54 kursi: 3 meja pagar `474, 476, 478` center pilar, 3 meja merah `456, 454, 452` tanpa meja sofa Entrance 2 dan bergeser +50 cm ke Aft dari center meja pagar, 6 meja sofa dinding `386, 388, 390, 392, 394, 396` semuanya 4-pax tanpa meja 2-pax, serta 2 Waiter Station yang sama persis layoutnya dengan Block 3).
* **Garis Koridor Tengah:** Blender `Y = 7.58m .. 9.88m` (Tengah: `Y = 8.73m`).
* **Pintu Masuk Pertama (Entrance 1):** Semua pintu masuk di dekat **pagar siku (L-shaped railing)** (`407` & `472` di `X = 10.15m`, serta `409` & `474` di `X = 15.65m`).
* **Perempatan Koridor & Meja Clover (`X = 10.40m .. 15.40m`):** Tepat di tengah antara Block 1–2 dan Block 3–4 (`X = 12.90m, Y = 8.73m`), terdapat perempatan koridor dengan **Meja Clover (4 daun bundar Ø100cm; sisi Portside & Starboardside lebih tinggi daripada sisi Forward & Aft)** serta **Lampu Hias Besar (Grand Murano Chandelier)** di bawah kubah plafon bundar.

### Fase 1: 3D Modeling Presisi di Blender (*Ristorante Arlecchino Deck 6*)
1. **Modular Components & Interior Architecture:**
   * Meja Marmer Carrara (`301, 303, 305, 307` di sisi jendela; `393, 397, 399` di baris tengah; `403, 405, 407` di sisi pagar koridor) dengan permukaan meja bersih (*clean marble top*).
   * Kursi Beludru Marun (*Burgundy Velvet*) di baris tengah & Kursi Gading (*Ivory Leatherette*) di baris jendela dan pagar.
   * *Double Waiter Station* (`0.5m > Partisi > 1.5m > Partisi > 0.5m > Partisi > 1.5m > Partisi` dengan 4 partisi pendek 25 cm, 4 kabinet bawah, dan 8 laci atas/tengah) + Sofa Banquette Merah + 9 Piring Fornasetti di dinding `X = -0.85m`.
   * Karpet pola geometris Arlecchino di ruang makan & lantai keramik koridor bermotif medali geometris hitam-putih yang simetris di tengah koridor.

### Fase 2: Arsitektur Web 3D Interaktif & UI Portal (`groupreservationcosta`)
1. **Hero Ship Cutaway ➔ Deck 6 Zoom-In:**
   * Halaman utama menampilkan visual/cutaway kapal *Costa Smeralda* utuh. Saat user mengklik area **Deck 6 (Ristorante Arlecchino)**, kamera melakukan transisi *zoom-in* mulus masuk ke model 3D blok restoran.
2. **3 Mode Navigasi Kamera Interaktif:**
   * **Walk Mode (First-Person View):** Navigasi jalan kaki (`WASD` / klik-tarik) menyusuri koridor dan sela-sela meja.
   * **Bird's-Eye Mode (Roof-Cutaway):** Sudut pandang miring dari atas dengan fitur *auto-hide ceiling* (atap/plafon otomatis transparan atau *one-sided backface culling* saat dilihat dari atas).
   * **Top-View 2D Mode (Orthographic 3D Render):** Tampilan lurus 90° dari atas (*orthographic projection*) layaknya peta 2D namun tetap mempertahankan kualitas render, tekstur karpet, dan pencahayaan 3D yang sama.
3. **Tombol Toggle `View / Hide Table Number`:**
   * Ketika **Hide**: Semua meja marmer tampil bersih seperti aslinya.
   * Ketika **View**: Menampilkan label nomor meja akurat (`301`, `303`, `305`, `307`, `393`, `397`, `399`, `403`, `405`, `407`) berukuran besar, tajam, dan jelas di atas tiap meja dengan tipografi modern yang indah dan universal.
4. **Efek Hover Pre-Selection Glassmorphism:**
   * Saat kursor diarahkan (*hover*) ke salah satu meja, muncul efek visual *glassmorphism* (lapisan *frosted glass* bercahaya lembut di atas meja + *outline highlight* + *floating glass card* berisi nomor meja dan kapasitas kursi).
