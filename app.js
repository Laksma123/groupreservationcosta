import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

// ============================================================================
// 0. MODERN WEB GUIDANCE POLYFILLS & FALLBACKS
// ============================================================================
if (!('switch' in HTMLInputElement.prototype)) {
  import('https://cdn.jsdelivr.net/npm/input-switch-polyfill@1.0.2/+esm').catch(() => {});
}

const bookingDialog = document.getElementById('booking-dialog');
if (bookingDialog && !('closedBy' in HTMLDialogElement.prototype)) {
  bookingDialog.addEventListener('click', (event) => {
    if (event.target !== bookingDialog) return;
    const rect = bookingDialog.getBoundingClientRect();
    const isDialogContent = (
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width
    );
    if (isDialogContent) return;
    bookingDialog.close();
  });
}

// ============================================================================
// 1. DRS 2-BLOCK TABLE METADATA (24 TABLES / 112 SEATS TOTAL) & ACCESS PRESETS
//    - Block 1 (Portside): 10 Tables (52 Seats)
//    - Block 2 (Starboardside): 14 Tables (60 Seats)
// ============================================================================
const TABLE_CATALOG = [
  // --- BLOCK 1: PORTSIDE (10 TABLES • 52 SEATS) ---
  {
    num: '301',
    block: 'B1',
    nodeKey: '301_Window_Booth',
    pax: 4,
    zone: 'Block 1 Port • Jendela Laut (Sofa Booth)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory',
  },
  {
    num: '303',
    block: 'B1',
    nodeKey: '303_Window_Bay1',
    pax: 6,
    zone: 'Block 1 Port • Jendela Laut (Bay 1)',
    chairDesc: '6 Kursi Ivory Leatherette • Panorama Laut',
  },
  {
    num: '305',
    block: 'B1',
    nodeKey: '305_Window_Bay2',
    pax: 6,
    zone: 'Block 1 Port • Jendela Laut (Bay 2)',
    chairDesc: '6 Kursi Ivory Leatherette • Panorama Laut',
  },
  {
    num: '307',
    block: 'B1',
    nodeKey: '307_Window_Bay3',
    pax: 6,
    zone: 'Block 1 Port • Jendela Laut (Bay 3)',
    chairDesc: '6 Kursi Ivory Leatherette • Dekat Lukisan',
  },
  {
    num: '399',
    block: 'B1',
    nodeKey: '399_Center_Fwd',
    pax: 6,
    zone: 'Block 1 Port • Baris Tengah (Dekat Station)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Tengah',
  },
  {
    num: '397',
    block: 'B1',
    nodeKey: '397_Center_Mid',
    pax: 6,
    zone: 'Block 1 Port • Baris Tengah (Sentral)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Tengah',
  },
  {
    num: '393',
    block: 'B1',
    nodeKey: '393_Center_Aft',
    pax: 6,
    zone: 'Block 1 Port • Baris Tengah (Dekat Pintu)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Tengah',
  },
  {
    num: '403',
    block: 'B1',
    nodeKey: '403_Railing_FwdBay',
    pax: 4,
    zone: 'Block 1 Port • Sisi Pagar X-Cross (Bay 1)',
    chairDesc: '4 Kursi Ivory Leatherette • Jalur Station',
  },
  {
    num: '405',
    block: 'B1',
    nodeKey: '405_Railing_MidBay',
    pax: 4,
    zone: 'Block 1 Port • Sisi Pagar X-Cross (Bay 2)',
    chairDesc: '4 Kursi Ivory Leatherette • Koridor Medali',
  },
  {
    num: '407',
    block: 'B1',
    nodeKey: '407_Railing_AftBay',
    pax: 4,
    zone: 'Block 1 Port • Sisi Pagar X-Cross (Pintu Masuk)',
    chairDesc: '4 Kursi Ivory Leatherette • Dekat Pintu Masuk',
  },

  // --- BLOCK 2: STARBOARDSIDE (14 TABLES • 60 SEATS) ---
  {
    num: '468',
    block: 'B2',
    nodeKey: '468_B2_Railing_Fwd',
    pax: 4,
    zone: 'Block 2 Stbd • Pagar X-Cross (Bay 1)',
    chairDesc: '4 Kursi Ivory Leatherette • Koridor Medali',
  },
  {
    num: '470',
    block: 'B2',
    nodeKey: '470_B2_Railing_Mid',
    pax: 4,
    zone: 'Block 2 Stbd • Pagar X-Cross (Bay 2)',
    chairDesc: '4 Kursi Ivory Leatherette • Koridor Medali',
  },
  {
    num: '472',
    block: 'B2',
    nodeKey: '472_B2_Railing_Aft',
    pax: 4,
    zone: 'Block 2 Stbd • Pagar X-Cross (Pintu Masuk)',
    chairDesc: '4 Kursi Ivory Leatherette • Dekat Pintu Masuk',
  },
  {
    num: '462',
    block: 'B2',
    nodeKey: '462_B2_Center_Fwd',
    pax: 6,
    zone: 'Block 2 Stbd • Baris Tengah (Depan)',
    chairDesc: '6 Kursi Burgundy Velvet • Jarak Lega 1.15m',
  },
  {
    num: '460',
    block: 'B2',
    nodeKey: '460_B2_Center_Mid',
    pax: 6,
    zone: 'Block 2 Stbd • Baris Tengah (Sentral)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Tengah',
  },
  {
    num: '458',
    block: 'B2',
    nodeKey: '458_B2_Center_Aft',
    pax: 6,
    zone: 'Block 2 Stbd • Baris Tengah (Dekat Pintu)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Tengah',
  },
  {
    num: '466',
    block: 'B2',
    nodeKey: '466_B2_Entrance2_Sofa1',
    pax: 4,
    zone: 'Block 2 Stbd • Sofa Pintu Masuk Kedua (#1)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory Sejajar Dinding',
  },
  {
    num: '464',
    block: 'B2',
    nodeKey: '464_B2_Entrance2_Sofa2',
    pax: 4,
    zone: 'Block 2 Stbd • Sofa Pintu Masuk Kedua (#2)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory Sejajar Dinding',
  },
  {
    num: '384',
    block: 'B2',
    nodeKey: '384_B2_Sofa_4Pax_1',
    pax: 4,
    zone: 'Block 2 Stbd • Dinding Sofa Dalam (4P #1)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory',
  },
  {
    num: '382',
    block: 'B2',
    nodeKey: '382_B2_Sofa_2Pax_1',
    pax: 2,
    zone: 'Block 2 Stbd • Dinding Sofa Dalam (2P #1)',
    chairDesc: 'Sofa Banquette Merah + 1 Kursi Ivory',
  },
  {
    num: '380',
    block: 'B2',
    nodeKey: '380_B2_Sofa_4Pax_2',
    pax: 4,
    zone: 'Block 2 Stbd • Dinding Sofa Dalam (4P #2)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory',
  },
  {
    num: '378',
    block: 'B2',
    nodeKey: '378_B2_Sofa_2Pax_2',
    pax: 2,
    zone: 'Block 2 Stbd • Dinding Sofa Dalam (2P #2)',
    chairDesc: 'Sofa Banquette Merah + 1 Kursi Ivory',
  },
  {
    num: '376',
    block: 'B2',
    nodeKey: '376_B2_Sofa_2Pax_3',
    pax: 2,
    zone: 'Block 2 Stbd • Dinding Sofa Dalam (2P #3)',
    chairDesc: 'Sofa Banquette Merah + 1 Kursi Ivory',
  },
  {
    num: '374',
    block: 'B2',
    nodeKey: '374_B2_Sofa_4Pax_3',
    pax: 4,
    zone: 'Block 2 Stbd • Dinding Sofa Dalam (4P #3)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory • Dekat Piring',
  },
];

const ACCESS_PRESETS = {
  A98XKJ90: {
    code: 'A98XKJ90',
    groupName: 'Milano Tech Incentive Group (2-Block Allocation)',
    targetPax: 44,
    lockedTables: ['301', '407', '374', '376'],
    recommended: ['399', '397', '403', '405', '468', '470', '462', '460'],
  },
  DIAMOND28: {
    code: 'DIAMOND28',
    groupName: 'Costa Club Diamond Family Reunion',
    targetPax: 28,
    lockedTables: ['393', '407', '472', '458'],
    recommended: ['466', '464', '462', '460', '384', '380'],
  },
  CHARTER112: {
    code: 'CHARTER112',
    groupName: 'Full 2-Block Arlecchino Charter (24 Meja)',
    targetPax: 112,
    lockedTables: [],
    recommended: TABLE_CATALOG.map((t) => t.num),
  },
};

// Walk Mode Viewpoint Presets across both Block 1, Central Medallion Corridor, and Block 2
// (Blender Y = 0..17.46m maps to Three.js Z = 0..-17.46m)
const WALK_SPOTS = {
  corridor: {
    pos: new THREE.Vector3(5.2, 1.62, -8.73),
    yaw: Math.PI * 0.5, // Looking down the central black-and-white medallion corridor
    pitch: -0.05,
  },
  entrance2: {
    pos: new THREE.Vector3(0.55, 1.62, -10.2),
    yaw: 0.08, // Looking from Entrance 2 through the 1.15m gap between Sofa 466/464 and Maroon 462
    pitch: -0.06,
  },
  b1_center: {
    pos: new THREE.Vector3(7.6, 1.62, -4.5),
    yaw: Math.PI * 0.35, // Looking across Block 1 maroon velvet chairs & ocean windows
    pitch: -0.05,
  },
  b1_station: {
    pos: new THREE.Vector3(0.4, 1.62, -2.5),
    yaw: -Math.PI * 0.38, // Looking from Block 1 Double Waiter Station & Sofa 301
    pitch: -0.05,
  },
  b2_center: {
    pos: new THREE.Vector3(5.2, 1.62, -13.2),
    yaw: -Math.PI * 0.25, // Looking across Block 2 center maroon tables 462, 460, 458
    pitch: -0.05,
  },
  b2_sofa: {
    pos: new THREE.Vector3(6.8, 1.62, -15.6),
    yaw: Math.PI * 0.72, // Looking along Block 2 inboard banquette sofa tables 384..374
    pitch: -0.06,
  },
};

// ============================================================================
// 2. SCENE, RENDERERS & CAMERAS
// ============================================================================
const canvas = document.getElementById('webgl-canvas');
const css2dContainer = document.getElementById('css2d-layer');

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const labelRenderer = new CSS2DRenderer({ element: css2dContainer });
labelRenderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x071426);
scene.fog = new THREE.FogExp2(0x071426, 0.0045);

// Perspective Camera (Used in Hero Ship, Bird's-Eye Mode, and Walk Mode)
const perspCamera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 500);

// Orthographic Camera (Used in Top-View 2D Mode framing BOTH Block 1 & Block 2)
const orthoFrustumH = 20.4;
const aspect = window.innerWidth / window.innerHeight;
const orthoCamera = new THREE.OrthographicCamera(
  (-orthoFrustumH * aspect) / 2,
  (orthoFrustumH * aspect) / 2,
  orthoFrustumH / 2,
  -orthoFrustumH / 2,
  0.1,
  120
);

let activeCamera = perspCamera;

const controls = new OrbitControls(perspCamera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxDistance = 150;
controls.minDistance = 1.2;

// Exterior & Global Lighting
const ambientLight = new THREE.AmbientLight(0xfff6e8, 1.45);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0xdbeafe, 0x3b2314, 1.2);
hemiLight.position.set(0, 32, 0);
scene.add(hemiLight);

const sunLight = new THREE.DirectionalLight(0xfffbeb, 2.35);
sunLight.position.set(28, 42, 34);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
scene.add(sunLight);

// Warm interior fill lights positioned over BOTH Block 1 (Z: -2..-6), Corridor (Z: -8.73), and Block 2 (Z: -11..-16)
const interiorLightGroup = new THREE.Group();
scene.add(interiorLightGroup);
[
  // Block 1 (Portside)
  [2.2, 2.55, -2.2, 0xffe4b5, 4.2],
  [6.0, 2.55, -2.2, 0xffe4b5, 4.2],
  [8.8, 2.55, -2.2, 0xffe4b5, 4.2],
  [2.5, 2.55, -5.4, 0xffd6a5, 3.8],
  [6.0, 2.55, -5.4, 0xffd6a5, 3.8],
  [8.8, 2.55, -5.4, 0xffd6a5, 3.8],
  // Central Medallion Corridor
  [1.5, 2.55, -8.73, 0xfff0d4, 3.8],
  [6.2, 2.55, -8.73, 0xfff0d4, 3.8],
  // Block 2 (Starboardside)
  [-0.5, 2.55, -13.0, 0xffe4b5, 4.2],
  [3.6, 2.55, -12.2, 0xffe4b5, 4.2],
  [7.6, 2.55, -12.2, 0xffe4b5, 4.2],
  [2.2, 2.55, -15.8, 0xffd6a5, 4.0],
  [6.0, 2.55, -15.8, 0xffd6a5, 4.0],
  [9.2, 2.55, -15.8, 0xffd6a5, 4.0],
].forEach(([lx, ly, lz, col, intensity]) => {
  const pt = new THREE.PointLight(col, intensity, 10.5, 1.35);
  pt.position.set(lx, ly, lz);
  interiorLightGroup.add(pt);
});
interiorLightGroup.visible = false;

// ============================================================================
// 3. STAGE 1: COSTA SMERALDA OUTER 3D MODEL & 4-LAYER CUTAWAY SYSTEM
// ============================================================================
const shipStageGroup = new THREE.Group();
scene.add(shipStageGroup);

// Mediterranean Sea & Wake Foam
const seaGeo = new THREE.PlaneGeometry(380, 380, 64, 64);
seaGeo.rotateX(-Math.PI / 2);
const seaMat = new THREE.MeshStandardMaterial({
  color: 0x083e66,
  roughness: 0.20,
  metalness: 0.38,
});
const oceanMesh = new THREE.Mesh(seaGeo, seaMat);
oceanMesh.position.y = -0.05;
shipStageGroup.add(oceanMesh);

// Named references to the 5 structural ship layer roots loaded from costa_smeralda_ship.glb
const shipLayerNodes = {
  L0: null, // Ship_Layer0_Base_Deck4Down (Not cutaway)
  L1: null, // Ship_Layer1_Deck5 (Colombina Aft)
  L2: null, // Ship_Layer2_Deck6 (Meneghino Aft + Arlecchino 2-Block Mid)
  L3: null, // Ship_Layer3_Deck7 (Rugantino Aft + Colosseo Mid)
  L4: null, // Ship_Layer4_Top_Deck8ToMuffler (Unified top block)
};

// Target Y lift offsets (in Three.js Y-up units) for each cutaway layer
const shipLayerTargetY = { L1: 0, L2: 0, L3: 0, L4: 0 };
let currentCutawayMode = 'full'; // 'full' | 'deck7' | 'deck6' | 'deck5'

const shipClickableArlecchinoMeshes = [];
let arlecchinoHitboxMesh = null;

// Floating 3D CSS2D Labels attached to the cutaway decks
const deckCutawayLabels = {
  colombina: null,
  meneghino: null,
  arlecchinoMain: null,
  arlecchinoPh: null,
  rugantino: null,
};

function makeDeckLabel(htmlText, extraClass, posVec3, parentNode, onClick = null) {
  const el = document.createElement(onClick ? 'button' : 'div');
  if (onClick) el.type = 'button';
  el.className = `${extraClass} is-hidden`;
  el.innerHTML = htmlText;
  if (onClick) {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      onClick();
    });
  }
  const obj = new CSS2DObject(el);
  obj.position.copy(posVec3);
  parentNode.add(obj);
  return { obj, el };
}

const loaderOverlay = document.getElementById('loading-overlay');
const gltfLoader = new GLTFLoader();

let shipGlbLoaded = false;
let interiorGlbLoaded = false;
function checkAllLoaded() {
  if (shipGlbLoaded && interiorGlbLoaded) {
    loaderOverlay.classList.add('is-hidden');
  }
}

// Load the 80%+ accurate Costa Smeralda 4-Layer Cutaway GLB generated by Blender
gltfLoader.load(
  './costa_smeralda_ship.glb',
  (gltf) => {
    const shipModel = gltf.scene;
    shipStageGroup.add(shipModel);

    shipModel.traverse((child) => {
      if (child.name === 'Ship_Layer0_Base_Deck4Down') shipLayerNodes.L0 = child;
      if (child.name === 'Ship_Layer1_Deck5') shipLayerNodes.L1 = child;
      if (child.name === 'Ship_Layer2_Deck6') shipLayerNodes.L2 = child;
      if (child.name === 'Ship_Layer3_Deck7') shipLayerNodes.L3 = child;
      if (child.name === 'Ship_Layer4_Top_Deck8ToMuffler') shipLayerNodes.L4 = child;

      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;

        // Make the 2-Block Arlecchino inside Deck 6 & its golden hitbox clickable!
        if (child.name === 'L2_Arlecchino_2Block_Active_Hitbox') {
          arlecchinoHitboxMesh = child;
          shipClickableArlecchinoMeshes.push(child);
        } else if (
          child.parent &&
          (child.parent.name === 'L2_Arlecchino_2Block_RealModel' ||
            (child.parent.parent && child.parent.parent.name === 'L2_Arlecchino_2Block_RealModel'))
        ) {
          shipClickableArlecchinoMeshes.push(child);
        }
      }
    });

    // Attach 3D CSS2D Labels to each Cutaway Deck Layer
    // Note: Blender (X, Y, Z) -> Three.js (X, Z_up, -Y)
    if (shipLayerNodes.L1) {
      deckCutawayLabels.colombina = makeDeckLabel(
        '📍 DECK 5 BELAKANG • RISTORANTE LA COLOMBINA (Placeholder 978 Kursi)',
        'ship-deck-label sdl-colombina',
        new THREE.Vector3(-25.5, 2.9, 0.0),
        shipLayerNodes.L1
      );
    }

    if (shipLayerNodes.L2) {
      deckCutawayLabels.meneghino = makeDeckLabel(
        '📍 DECK 6 BELAKANG • RISTORANTE IL MENEGHINO (Placeholder 886 Kursi)',
        'ship-deck-label sdl-meneghino',
        new THREE.Vector3(-25.8, 3.8, 0.0),
        shipLayerNodes.L2
      );

      deckCutawayLabels.arlecchinoPh = makeDeckLabel(
        '⏳ Arlecchino Blok Lainnya & Colosseo (Placeholder)',
        'ship-deck-label sdl-placeholder',
        new THREE.Vector3(5.2, 3.8, -1.8),
        shipLayerNodes.L2
      );

      deckCutawayLabels.arlecchinoMain = makeDeckLabel(
        '<span>⭐ DECK 6 TENGAH • RISTORANTE ARLECCHINO (2 BLOK SELESAI — KLIK MASUK)</span>',
        'ship-hotspot-marker',
        new THREE.Vector3(-1.5, 3.95, 1.85),
        shipLayerNodes.L2,
        () => enterInterior2Blocks()
      );
      // Show main hotspot by default
      deckCutawayLabels.arlecchinoMain.el.classList.remove('is-hidden');
    }

    if (shipLayerNodes.L3) {
      deckCutawayLabels.rugantino = makeDeckLabel(
        '📍 DECK 7 BELAKANG • RISTORANTE IL RUGANTINO (Placeholder 546 Kursi)',
        'ship-deck-label sdl-rugantino',
        new THREE.Vector3(-25.6, 4.6, 0.0),
        shipLayerNodes.L3
      );
    }

    shipGlbLoaded = true;
    checkAllLoaded();
  },
  undefined,
  (err) => {
    console.error('Error loading costa_smeralda_ship.glb:', err);
    shipGlbLoaded = true;
    checkAllLoaded();
  }
);

// Set 4-Layer Cutaway State on the Costa Smeralda 3D Model
function setShipCutawayLayer(layerMode, animateCam = true) {
  currentCutawayMode = layerMode;

  document.querySelectorAll('.cutaway-layer-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.cutawayLayer === layerMode);
  });

  // Hide all deck placeholder labels first, then show the active deck's labels
  if (deckCutawayLabels.colombina) {
    deckCutawayLabels.colombina.el.classList.toggle('is-hidden', layerMode !== 'deck5');
  }
  if (deckCutawayLabels.meneghino) {
    deckCutawayLabels.meneghino.el.classList.toggle('is-hidden', layerMode !== 'deck6');
  }
  if (deckCutawayLabels.arlecchinoPh) {
    deckCutawayLabels.arlecchinoPh.el.classList.toggle('is-hidden', layerMode !== 'deck6');
  }
  if (deckCutawayLabels.rugantino) {
    deckCutawayLabels.rugantino.el.classList.toggle('is-hidden', layerMode !== 'deck7');
  }
  if (deckCutawayLabels.arlecchinoMain) {
    const showArl = currentStage === 'ship' && (layerMode === 'full' || layerMode === 'deck6');
    deckCutawayLabels.arlecchinoMain.el.classList.toggle('is-hidden', !showArl);
  }

  if (layerMode === 'full') {
    // All layers closed (Full Costa Smeralda Ship)
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 0;
    shipLayerTargetY.L4 = 0;
    document.getElementById('stage-title').textContent =
      'Kapal Utuh Costa Smeralda — Sistem Cutaway 4 Lapis';
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(34, 17, 46), new THREE.Vector3(0, 5.2, 0), 900);
    }
  } else if (layerMode === 'deck7') {
    // Cutaway Layer 3: Lift Deck 8–Muffler (L4) up to expose Deck 7 (Il Rugantino Aft)
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 0;
    shipLayerTargetY.L4 = 8.5;
    document.getElementById('stage-title').textContent =
      'Cutaway Lapis 3: Deck 7 "Positano" — Ristorante Il Rugantino (Placeholder)';
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(-18, 15.5, 32), new THREE.Vector3(-12, 4.2, 0), 900);
    }
  } else if (layerMode === 'deck6') {
    // Cutaway Layer 2: Lift Deck 7 (L3) & Deck 8–Muffler (L4) to expose Deck 6 (2-Block Arlecchino & Il Meneghino)
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 6.5;
    shipLayerTargetY.L4 = 13.5;
    document.getElementById('stage-title').textContent =
      'Cutaway Lapis 2: Deck 6 "Roma" — 2 Blok Arlecchino (100% Detail) & Il Meneghino';
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(5, 13.5, 24), new THREE.Vector3(-3.5, 3.2, 0), 900);
    }
  } else if (layerMode === 'deck5') {
    // Cutaway Layer 1: Lift Deck 6 (L2), Deck 7 (L3), & Deck 8–Muffler (L4) to expose Deck 5 (La Colombina Aft)
    // Base Deck 4 & Below (L0) stays fixed!
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 5.5;
    shipLayerTargetY.L3 = 11.0;
    shipLayerTargetY.L4 = 17.5;
    document.getElementById('stage-title').textContent =
      'Cutaway Lapis 1: Deck 5 "Taormina" — Ristorante La Colombina (Placeholder)';
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(-18, 14.0, 32), new THREE.Vector3(-14, 2.5, 0), 900);
    }
  }
}

// ============================================================================
// 4. STAGE 2: LOAD 2-BLOCK ARLECCHINO GLB & BUILD 24 INTERACTIVE TABLE OVERLAYS
// ============================================================================
const restaurantGroup = new THREE.Group();
restaurantGroup.visible = false;
scene.add(restaurantGroup);

const ceilingMeshes = [];
const tableRegistry = new Map(); // num -> { meta, meshes, topMesh, glassPad, glassBorder, labelObj, labelEl, center, size }
const interactiveMeshes = []; // All meshes that trigger table hover/click

gltfLoader.load(
  './arlecchino_block1.glb',
  (gltf) => {
    const model = gltf.scene;
    restaurantGroup.add(model);

    // 1. Classify meshes inside the loaded 2-Block Blender .glb
    model.traverse((child) => {
      if (!child.isMesh) return;
      child.castShadow = true;
      child.receiveShadow = true;

      const n = child.name || '';
      // Ceiling & overhead lighting objects for BOTH Block 1 and Block 2
      if (
        n.startsWith('Ceiling_') ||
        n.startsWith('CeilBeam_') ||
        n.startsWith('B2_CeilBeam_') ||
        n.startsWith('RedSpot_') ||
        n.startsWith('B2_RedSpot_') ||
        n.startsWith('Corr_Downlight_')
      ) {
        ceilingMeshes.push(child);
      }

      // Associate table & chair meshes with their DRS table number across all 24 tables
      for (const meta of TABLE_CATALOG) {
        if (
          n.includes(meta.nodeKey) ||
          (meta.num === '301' && n.startsWith('Banquette_'))
        ) {
          child.userData.tableNum = meta.num;
          interactiveMeshes.push(child);

          if (!tableRegistry.has(meta.num)) {
            tableRegistry.set(meta.num, {
              meta,
              meshes: [],
              topMesh: null,
              glassPad: null,
              glassBorder: null,
              labelObj: null,
              labelEl: null,
              center: new THREE.Vector3(),
              size: new THREE.Vector3(),
            });
          }
          const entry = tableRegistry.get(meta.num);
          entry.meshes.push(child);
          if (n.startsWith('TableTop_')) {
            entry.topMesh = child;
          }
        }
      }
    });

    // 2. Build 3D Glassmorphism Pre-Selection Pads & Floating Typography Labels for all 24 tables
    model.updateMatrixWorld(true);

    for (const meta of TABLE_CATALOG) {
      const entry = tableRegistry.get(meta.num);
      if (!entry || !entry.topMesh) continue;

      const box = new THREE.Box3().setFromObject(entry.topMesh);
      box.getCenter(entry.center);
      box.getSize(entry.size);

      const padW = Math.max(entry.size.x - 0.03, 0.45);
      const padD = Math.max(entry.size.z - 0.03, 0.45);
      const padH = 0.018;
      const padGeo = new THREE.BoxGeometry(padW, padH, padD);

      const padMat = new THREE.MeshPhysicalMaterial({
        color: 0x38bdf8,
        emissive: 0x0284c7,
        emissiveIntensity: 0.35,
        roughness: 0.12,
        metalness: 0.05,
        transmission: 0.65,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
      });

      const glassPad = new THREE.Mesh(padGeo, padMat);
      glassPad.position.set(entry.center.x, box.max.y + 0.014, entry.center.z);
      glassPad.userData.tableNum = meta.num;
      restaurantGroup.add(glassPad);
      interactiveMeshes.push(glassPad);
      entry.glassPad = glassPad;

      // Glowing Glassmorphic Rim Border
      const edgeGeo = new THREE.EdgesGeometry(padGeo);
      const edgeMat = new THREE.LineBasicMaterial({
        color: 0x7dd3fc,
        transparent: true,
        opacity: 0.0,
      });
      const glassBorder = new THREE.LineSegments(edgeGeo, edgeMat);
      glassPad.add(glassBorder);
      entry.glassBorder = glassBorder;

      // Floating 3D Table Number Label (View / Hide Table Number)
      const markerEl = document.createElement('div');
      markerEl.className = 'table-num-marker is-hidden';
      markerEl.innerHTML = `
        <div class="tnm-pill">
          <span class="tnm-number">${meta.num}</span>
          <span class="tnm-pax">${meta.pax}P</span>
        </div>
      `;
      markerEl.addEventListener('mouseenter', () => setHoveredTable(meta.num));
      markerEl.addEventListener('mouseleave', () => setHoveredTable(null));
      markerEl.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleTableSelection(meta.num);
      });

      const labelObj = new CSS2DObject(markerEl);
      labelObj.position.set(entry.center.x, box.max.y + 0.08, entry.center.z);
      restaurantGroup.add(labelObj);
      entry.labelObj = labelObj;
      entry.labelEl = markerEl;
    }

    applyAccessPreset(currentPresetKey);
    interiorGlbLoaded = true;
    checkAllLoaded();
  },
  undefined,
  (err) => {
    console.error('Error loading arlecchino_block1.glb:', err);
    document.getElementById('loader-title').textContent = 'Gagal memuat file 3D (.glb)';
  }
);

// ============================================================================
// 5. STATE MANAGEMENT: STAGES, CAMERA MODES, HOVER & TABLE SELECTION
// ============================================================================
let currentStage = 'ship'; // 'ship' | 'interior'
let currentCamMode = 'bird'; // 'bird' | 'top2d' | 'walk'
let top2dFlipped = false;
let showTableNumbers = true;
let activeBlockFilter = 'all'; // 'all' | 'B1' | 'B2'

let currentPresetKey = 'A98XKJ90';
let selectedTables = new Set();
let lockedTables = new Set();
let hoveredTableNum = null;

// Smooth Camera Transition State
let camAnim = null;

function animateCameraTo(targetPos, targetLookAt, durationMs = 950, onDone = null) {
  const startPos = activeCamera.position.clone();
  const startLook = controls.target.clone();
  const startTime = performance.now();

  camAnim = {
    update(now) {
      const t = Math.min(1, (now - startTime) / durationMs);
      const ease = 1 - Math.pow(1 - t, 3); // Cubic ease-out
      activeCamera.position.lerpVectors(startPos, targetPos, ease);
      controls.target.lerpVectors(startLook, targetLookAt, ease);
      if (t >= 1) {
        camAnim = null;
        if (onDone) onDone();
      }
    },
  };
}

// Position camera for Stage 1 (Hero Ship View)
function setHeroShipCamera(instant = false) {
  currentStage = 'ship';
  activeCamera = perspCamera;
  controls.object = perspCamera;
  controls.enabled = true;
  controls.enableRotate = true;
  controls.maxPolarAngle = Math.PI * 0.48;

  shipStageGroup.visible = true;
  restaurantGroup.visible = false;
  interiorLightGroup.visible = false;
  updateTableMarkersVisibility();

  document.getElementById('hero-ship-ui').hidden = false;
  document.getElementById('interior-ui').hidden = true;
  document.getElementById('btn-back-ship').hidden = true;

  if (instant) {
    setShipCutawayLayer('full', false);
    perspCamera.position.set(34, 17, 46);
    controls.target.set(0, 5.2, 0);
    controls.update();
  } else {
    // Return to Deck 6 Cutaway view on the ship so the user sees the 2-Block Arlecchino in context
    setShipCutawayLayer('deck6', true);
  }
}

setHeroShipCamera(true);

// Trigger Cutaway Animation on Hero Ship -> Zoom-In to Deck 6 (2-Block Ristorante Arlecchino)
function enterInterior2Blocks() {
  if (currentStage === 'interior') return;

  // Ensure Deck 6 cutaway is lifted before zooming into the 2-Block Arlecchino bay
  setShipCutawayLayer('deck6', false);

  // Hide ship floating labels during zoom-in
  Object.values(deckCutawayLabels).forEach((lbl) => {
    if (lbl && lbl.el) lbl.el.classList.add('is-hidden');
  });

  animateCameraTo(
    new THREE.Vector3(-0.5, 5.2, 6.8),
    new THREE.Vector3(-1.5, 3.0, 1.5),
    820,
    () => {
      // Switch to Stage 2: Interior Ristorante Arlecchino (Full 2 Blocks: 24 Tables)
      currentStage = 'interior';
      shipStageGroup.visible = false;
      restaurantGroup.visible = true;
      interiorLightGroup.visible = true;

      document.getElementById('hero-ship-ui').hidden = true;
      document.getElementById('interior-ui').hidden = false;
      document.getElementById('btn-back-ship').hidden = false;
      document.getElementById('stage-title').textContent =
        'Deck 6 "Roma" • Ristorante Arlecchino (Block 1 Port & Block 2 Stbd • 24 Meja)';

      setInteriorCameraMode('bird');
      updateTableMarkersVisibility();
    }
  );
}

// Toggle Ceiling / Roof visibility for BOTH Block 1 and Block 2
function setCeilingVisible(vis) {
  for (const m of ceilingMeshes) {
    m.visible = vis;
  }
}

function updateTableMarkersVisibility() {
  const shouldShow = currentStage === 'interior' && showTableNumbers;
  for (const [, entry] of tableRegistry) {
    if (!entry.labelEl) continue;
    const matchBlock =
      activeBlockFilter === 'all' || entry.meta.block === activeBlockFilter;
    entry.labelEl.classList.toggle('is-hidden', !(shouldShow && matchBlock));
  }
}

// ============================================================================
// 6. THREE INTERIOR CAMERA MODES: BIRD'S-EYE, TOP-VIEW 2D, WALK MODE (2 BLOCKS)
// ============================================================================
let walkYaw = WALK_SPOTS.corridor.yaw;
let walkPitch = WALK_SPOTS.corridor.pitch;
const walkKeys = { forward: false, backward: false, left: false, right: false };
let isDraggingLook = false;
let prevPointer = { x: 0, y: 0 };

function setInteriorCameraMode(mode) {
  currentCamMode = mode;

  document.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.camMode === mode);
  });

  const walkHud = document.getElementById('walk-hud');
  walkHud.hidden = mode !== 'walk';

  if (mode === 'bird') {
    // 1. BIRD'S-EYE MODE (Both Block 1 & Block 2 Ceilings Hidden + 3D Perspective Orbit)
    setCeilingVisible(false);
    activeCamera = perspCamera;
    perspCamera.fov = 42;
    perspCamera.updateProjectionMatrix();

    controls.object = perspCamera;
    controls.enabled = true;
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.maxPolarAngle = Math.PI * 0.47;

    const targetPos = top2dFlipped
      ? new THREE.Vector3(-7.8, 14.2, -8.73)
      : new THREE.Vector3(16.8, 14.2, -8.73);
    const lookTarget = new THREE.Vector3(4.35, 0.55, -8.73);
    animateCameraTo(targetPos, lookTarget, 750);
  } else if (mode === 'top2d') {
    // 2. TOP-VIEW 2D MODE (Orthographic 90° Overhead framing BOTH Block 1 & Block 2)
    setCeilingVisible(false);
    camAnim = null;
    activeCamera = orthoCamera;

    const centerX = 4.35;
    const centerZ = -8.73; // Exact midpoint of Central Medallion Corridor!
    orthoCamera.position.set(centerX, 22.0, centerZ);
    orthoCamera.up.set(0, 0, top2dFlipped ? -1 : 1);
    orthoCamera.lookAt(centerX, 0.0, centerZ);
    orthoCamera.zoom = 1.04;
    orthoCamera.updateProjectionMatrix();

    controls.object = orthoCamera;
    controls.target.set(centerX, 0.0, centerZ);
    controls.enabled = true;
    controls.enableRotate = false; // Locked strictly to 2D top-down plane
    controls.enablePan = true;
    controls.update();
  } else if (mode === 'walk') {
    // 3. WALK MODE (First-Person Eye-Level 1.62m + Both Block Ceilings Restored!)
    setCeilingVisible(true);
    camAnim = null;
    activeCamera = perspCamera;
    perspCamera.fov = 62;
    perspCamera.up.set(0, 1, 0);
    perspCamera.updateProjectionMatrix();

    controls.enabled = false;
    teleportWalkTo('corridor');
  }
}

function teleportWalkTo(spotKey) {
  const spot = WALK_SPOTS[spotKey] || WALK_SPOTS.corridor;
  perspCamera.position.copy(spot.pos);
  walkYaw = spot.yaw;
  walkPitch = spot.pitch;
  syncWalkCameraLook();

  document.querySelectorAll('[data-walk-spot]').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.walkSpot === spotKey);
  });
}

function syncWalkCameraLook() {
  const dir = new THREE.Vector3(
    -Math.sin(walkYaw) * Math.cos(walkPitch),
    Math.sin(walkPitch),
    -Math.cos(walkYaw) * Math.cos(walkPitch)
  );
  const lookTarget = perspCamera.position.clone().add(dir);
  perspCamera.lookAt(lookTarget);
}

// ============================================================================
// 7. GLASSMORPHISM PRE-SELECTION HOVER & TABLE SELECTION LOGIC (24 TABLES)
// ============================================================================
const hoverCard = document.getElementById('hover-glass-card');

function setHoveredTable(tableNum) {
  if (hoveredTableNum === tableNum) return;
  hoveredTableNum = tableNum;

  canvas.style.cursor = tableNum ? 'pointer' : currentCamMode === 'walk' ? 'grab' : 'default';

  for (const [num, entry] of tableRegistry) {
    if (!entry.labelEl) continue;
    entry.labelEl.classList.toggle('is-hovered', num === tableNum);
  }

  if (!tableNum || currentStage !== 'interior') {
    hoverCard.hidden = true;
    return;
  }

  const entry = tableRegistry.get(tableNum);
  if (!entry) return;

  const isLocked = lockedTables.has(tableNum);
  const isSel = selectedTables.has(tableNum);

  const statusBadge = document.getElementById('hgc-status');
  if (isLocked) {
    statusBadge.textContent = 'TERKUNCI (SUDAH DIPESAN)';
    statusBadge.style.background = 'rgba(239, 68, 68, 0.25)';
    statusBadge.style.color = '#fca5a5';
    statusBadge.style.borderColor = '#ef4444';
  } else if (isSel) {
    statusBadge.textContent = '✓ TERPILIH UNTUK GRUP';
    statusBadge.style.background = 'rgba(16, 185, 129, 0.25)';
    statusBadge.style.color = '#6ee7b7';
    statusBadge.style.borderColor = '#10b981';
  } else {
    statusBadge.textContent = 'GLASS PRE-SELECTION • TERSEDIA';
    statusBadge.style.background = 'rgba(56, 189, 248, 0.22)';
    statusBadge.style.color = '#7dd3fc';
    statusBadge.style.borderColor = '#38bdf8';
  }

  document.getElementById('hgc-zone').textContent = entry.meta.zone;
  document.getElementById('hgc-number').textContent = entry.meta.num;
  document.getElementById('hgc-title').textContent = `Meja ${entry.meta.num} • ${entry.meta.pax} Kursi`;
  document.getElementById('hgc-desc').textContent = entry.meta.chairDesc;
  document.getElementById('hgc-footer').textContent = isLocked
    ? '🔒 Meja ini telah dialokasikan untuk grup lain pada kode akses ini'
    : isSel
    ? '✓ Klik meja untuk membatalkan pilihan dari daftar grup'
    : '✨ Klik meja untuk memilih meja ini ke dalam reservasi grup';

  hoverCard.hidden = false;
}

function toggleTableSelection(tableNum) {
  if (lockedTables.has(tableNum)) return;
  if (selectedTables.has(tableNum)) {
    selectedTables.delete(tableNum);
  } else {
    selectedTables.add(tableNum);
  }
  syncSelectionUI();
  if (hoveredTableNum === tableNum) {
    setHoveredTable(null);
    setHoveredTable(tableNum);
  }
}

function applyAccessPreset(presetKey) {
  currentPresetKey = presetKey;
  const preset = ACCESS_PRESETS[presetKey] || ACCESS_PRESETS.A98XKJ90;
  lockedTables = new Set(preset.lockedTables);
  selectedTables.clear();
  syncSelectionUI();
}

function syncSelectionUI() {
  const preset = ACCESS_PRESETS[currentPresetKey] || ACCESS_PRESETS.A98XKJ90;
  let totalPax = 0;

  for (const [num, entry] of tableRegistry) {
    const isSel = selectedTables.has(num);
    const isLock = lockedTables.has(num);
    if (isSel) totalPax += entry.meta.pax;

    if (entry.labelEl) {
      entry.labelEl.classList.toggle('is-selected', isSel);
      entry.labelEl.classList.toggle('is-locked', isLock);
    }
  }

  document.getElementById('selected-pax-count').textContent = String(totalPax);
  document.getElementById('target-pax-count').textContent = String(preset.targetPax);
  document.getElementById('selected-table-count').textContent = `${selectedTables.size} Meja`;

  const pct = Math.min(100, Math.round((totalPax / preset.targetPax) * 100));
  document.getElementById('pax-progress-fill').style.width = `${pct}%`;
  document.getElementById('pax-progressbar').setAttribute('aria-valuenow', String(totalPax));
  document.getElementById('pax-progressbar').setAttribute('aria-valuemax', String(preset.targetPax));

  const pill = document.getElementById('pax-status-pill');
  const diff = preset.targetPax - totalPax;
  if (totalPax === 0) {
    pill.textContent = 'Belum Ada Meja';
    pill.style.background = 'rgba(255,255,255,0.1)';
    pill.style.color = '#e2e8f0';
  } else if (diff > 0) {
    pill.textContent = `Kurang ${diff} Kursi`;
    pill.style.background = 'rgba(56, 189, 248, 0.22)';
    pill.style.color = '#7dd3fc';
  } else {
    pill.textContent = '✓ Target Terpenuhi';
    pill.style.background = 'rgba(16, 185, 129, 0.25)';
    pill.style.color = '#6ee7b7';
  }

  // Rebuild Sidebar Table List (Filtered by All / Block 1 / Block 2)
  const listEl = document.getElementById('sidebar-table-list');
  listEl.innerHTML = '';
  const visibleTables = TABLE_CATALOG.filter(
    (meta) => activeBlockFilter === 'all' || meta.block === activeBlockFilter
  );

  for (const meta of visibleTables) {
    const isSel = selectedTables.has(meta.num);
    const isLock = lockedTables.has(meta.num);
    const row = document.createElement('div');
    row.className = `table-row-item ${isSel ? 'is-selected' : ''} ${isLock ? 'is-locked' : ''}`;
    row.setAttribute('role', 'listitem');
    row.innerHTML = `
      <div class="tri-left">
        <div class="tri-num">${meta.num}</div>
        <div class="tri-meta">
          <strong>Meja ${meta.num} • ${meta.pax} Pax</strong>
          <small>${meta.zone}</small>
        </div>
      </div>
      <span class="tri-badge">${isLock ? '🔒 Terkunci' : isSel ? '✓ Terpilih' : 'Pilih'}</span>
    `;
    row.addEventListener('mouseenter', () => setHoveredTable(meta.num));
    row.addEventListener('mouseleave', () => setHoveredTable(null));
    row.addEventListener('click', () => toggleTableSelection(meta.num));
    listEl.appendChild(row);
  }

  const confirmBtn = document.getElementById('btn-confirm-booking');
  confirmBtn.disabled = selectedTables.size === 0;
  confirmBtn.textContent =
    selectedTables.size > 0
      ? `Konfirmasi Reservasi Grup (${totalPax} Pax)`
      : 'Konfirmasi Reservasi Grup (0 Pax)';
}

// ============================================================================
// 8. RAYCASTING (3D HOVER & CLICK FOR BOTH SHIP & 24 INTERIOR TABLES)
// ============================================================================
const raycaster = new THREE.Raycaster();
const pointerNDC = new THREE.Vector2();
let pointerDownPos = { x: 0, y: 0 };

function updatePointerNDC(event) {
  const rect = canvas.getBoundingClientRect();
  pointerNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointerNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

canvas.addEventListener('pointermove', (event) => {
  if (currentStage === 'interior' && currentCamMode === 'walk' && isDraggingLook) {
    const dx = event.clientX - prevPointer.x;
    const dy = event.clientY - prevPointer.y;
    prevPointer = { x: event.clientX, y: event.clientY };
    walkYaw -= dx * 0.0042;
    walkPitch = Math.max(-0.65, Math.min(0.65, walkPitch - dy * 0.0035));
    syncWalkCameraLook();
    return;
  }

  updatePointerNDC(event);
  raycaster.setFromCamera(pointerNDC, activeCamera);

  if (currentStage === 'ship' && shipClickableArlecchinoMeshes.length > 0) {
    const hits = raycaster.intersectObjects(shipClickableArlecchinoMeshes, false);
    const hitArl = hits.length > 0;
    canvas.style.cursor = hitArl ? 'pointer' : 'grab';
    if (arlecchinoHitboxMesh && arlecchinoHitboxMesh.material) {
      arlecchinoHitboxMesh.material.emissiveIntensity = hitArl ? 1.15 : 0.65;
    }
    return;
  }

  if (currentStage === 'interior') {
    const hits = raycaster.intersectObjects(interactiveMeshes, false);
    if (hits.length > 0) {
      const tNum = hits[0].object.userData.tableNum;
      setHoveredTable(tNum || null);
    } else {
      setHoveredTable(null);
    }
  }
});

canvas.addEventListener('pointerdown', (event) => {
  pointerDownPos = { x: event.clientX, y: event.clientY };
  if (currentStage === 'interior' && currentCamMode === 'walk') {
    isDraggingLook = true;
    prevPointer = { x: event.clientX, y: event.clientY };
    canvas.style.cursor = 'grabbing';
  }
});

window.addEventListener('pointerup', (event) => {
  if (isDraggingLook) {
    isDraggingLook = false;
    canvas.style.cursor = 'grab';
  }

  const moveDist = Math.hypot(
    event.clientX - pointerDownPos.x,
    event.clientY - pointerDownPos.y
  );
  if (moveDist > 6 || event.target !== canvas) return;

  updatePointerNDC(event);
  raycaster.setFromCamera(pointerNDC, activeCamera);

  if (currentStage === 'ship' && shipClickableArlecchinoMeshes.length > 0) {
    const hits = raycaster.intersectObjects(shipClickableArlecchinoMeshes, false);
    if (hits.length > 0) {
      enterInterior2Blocks();
    }
    return;
  }

  if (currentStage === 'interior') {
    const hits = raycaster.intersectObjects(interactiveMeshes, false);
    if (hits.length > 0 && hits[0].object.userData.tableNum) {
      toggleTableSelection(hits[0].object.userData.tableNum);
    }
  }
});

// ============================================================================
// 9. UI EVENT LISTENERS (4-LAYER CUTAWAY, BLOCK FILTER, SWITCH, WALK, DIALOG)
// ============================================================================
document.getElementById('btn-enter-deck6').addEventListener('click', enterInterior2Blocks);
document.getElementById('btn-back-ship').addEventListener('click', () => setHeroShipCamera(false));

// 4-Layer Ship Cutaway Selector Buttons
document.querySelectorAll('.cutaway-layer-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    setShipCutawayLayer(btn.dataset.cutawayLayer, true);
  });
});

// Block 1 / Block 2 Filter Buttons in Sidebar
document.querySelectorAll('.block-filter-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    activeBlockFilter = btn.dataset.blockFilter;
    document.querySelectorAll('.block-filter-btn').forEach((b) => {
      b.classList.toggle('active', b === btn);
    });
    syncSelectionUI();
    updateTableMarkersVisibility();
  });
});

document.getElementById('access-preset').addEventListener('change', (e) => {
  applyAccessPreset(e.target.value);
});

document.querySelectorAll('.mode-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    setInteriorCameraMode(btn.dataset.camMode);
  });
});

// View / Hide Table Number Switch Listener
const tableNumSwitch = document.getElementById('toggle-table-numbers');
const tableNumStateText = document.getElementById('table-num-state-text');
tableNumSwitch.addEventListener('change', () => {
  showTableNumbers = tableNumSwitch.checked;
  tableNumStateText.textContent = showTableNumbers
    ? 'View (Tampil Jelas)'
    : 'Hide (Meja Bersih)';
  updateTableMarkersVisibility();
});

document.getElementById('btn-flip-orientation').addEventListener('click', () => {
  top2dFlipped = !top2dFlipped;
  if (currentCamMode === 'top2d' || currentCamMode === 'bird') {
    setInteriorCameraMode(currentCamMode);
  } else {
    walkYaw += Math.PI;
    syncWalkCameraLook();
  }
});

document.getElementById('btn-reset-view').addEventListener('click', () => {
  setInteriorCameraMode(currentCamMode);
});

// Walk Mode Teleport & D-Pad Buttons
document.querySelectorAll('[data-walk-spot]').forEach((btn) => {
  btn.addEventListener('click', () => teleportWalkTo(btn.dataset.walkSpot));
});

document.querySelectorAll('[data-walk-dir]').forEach((btn) => {
  const dir = btn.dataset.walkDir;
  const startMove = () => { walkKeys[dir] = true; };
  const stopMove = () => { walkKeys[dir] = false; };
  btn.addEventListener('pointerdown', startMove);
  btn.addEventListener('pointerup', stopMove);
  btn.addEventListener('pointerleave', stopMove);
});

window.addEventListener('keydown', (e) => {
  if (currentStage !== 'interior' || currentCamMode !== 'walk') return;
  if (e.code === 'KeyW' || e.code === 'ArrowUp') walkKeys.forward = true;
  if (e.code === 'KeyS' || e.code === 'ArrowDown') walkKeys.backward = true;
  if (e.code === 'KeyA' || e.code === 'ArrowLeft') walkKeys.left = true;
  if (e.code === 'KeyD' || e.code === 'ArrowRight') walkKeys.right = true;
});

window.addEventListener('keyup', (e) => {
  if (e.code === 'KeyW' || e.code === 'ArrowUp') walkKeys.forward = false;
  if (e.code === 'KeyS' || e.code === 'ArrowDown') walkKeys.backward = false;
  if (e.code === 'KeyA' || e.code === 'ArrowLeft') walkKeys.left = false;
  if (e.code === 'KeyD' || e.code === 'ArrowRight') walkKeys.right = false;
});

// Auto-Recommend Adjacent Tables & Clear
document.getElementById('btn-auto-recommend').addEventListener('click', () => {
  const preset = ACCESS_PRESETS[currentPresetKey] || ACCESS_PRESETS.A98XKJ90;
  selectedTables.clear();
  for (const tNum of preset.recommended) {
    if (!lockedTables.has(tNum)) selectedTables.add(tNum);
  }
  syncSelectionUI();
});

document.getElementById('btn-clear-selection').addEventListener('click', () => {
  selectedTables.clear();
  syncSelectionUI();
});

// Confirm Booking Modal Dialog
document.getElementById('btn-confirm-booking').addEventListener('click', () => {
  const preset = ACCESS_PRESETS[currentPresetKey] || ACCESS_PRESETS.A98XKJ90;
  const chosenList = TABLE_CATALOG.filter((t) => selectedTables.has(t.num));
  const totalSeats = chosenList.reduce((acc, t) => acc + t.pax, 0);
  const b1List = chosenList.filter((t) => t.block === 'B1').map((t) => `#${t.num} (${t.pax}P)`);
  const b2List = chosenList.filter((t) => t.block === 'B2').map((t) => `#${t.num} (${t.pax}P)`);

  document.getElementById('dialog-summary-content').innerHTML = `
    <div><strong>Kode Akses DRS:</strong> ${preset.code} — ${preset.groupName}</div>
    <div><strong>Restoran &amp; Lokasi:</strong> Ristorante Arlecchino • Deck 6 "Roma" (2 Blok: Portside &amp; Starboardside)</div>
    <div><strong>Meja Block 1 Portside (${b1List.length}):</strong> ${b1List.join(', ') || '-'}</div>
    <div><strong>Meja Block 2 Starboard (${b2List.length}):</strong> ${b2List.join(', ') || '-'}</div>
    <div><strong>Total Kapasitas Kursi:</strong> ${totalSeats} Kursi dari ${chosenList.length} Meja (Target Grup: ${preset.targetPax} Pax)</div>
    <div><strong>Status Sinkronisasi:</strong> Siap dikirim ke Onboard Maitre D' &amp; Costa DRS</div>
  `;
  bookingDialog.showModal();
});

document.getElementById('btn-copy-manifest').addEventListener('click', (e) => {
  const text = document.getElementById('dialog-summary-content').innerText;
  navigator.clipboard?.writeText(text);
  e.target.textContent = '✓ Tersalin ke Clipboard!';
  setTimeout(() => {
    e.target.textContent = '📋 Salin Manifest DRS';
  }, 1800);
});

// Window Resize Handler
window.addEventListener('resize', () => {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const asp = w / h;

  perspCamera.aspect = asp;
  perspCamera.updateProjectionMatrix();

  orthoCamera.left = (-orthoFrustumH * asp) / 2;
  orthoCamera.right = (orthoFrustumH * asp) / 2;
  orthoCamera.top = orthoFrustumH / 2;
  orthoCamera.bottom = -orthoFrustumH / 2;
  orthoCamera.updateProjectionMatrix();

  renderer.setSize(w, h);
  labelRenderer.setSize(w, h);
});

// ============================================================================
// 10. MAIN RENDER & ANIMATION LOOP
// ============================================================================
let prevTime = performance.now();

function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.min(0.05, (now - prevTime) / 1000);
  prevTime = now;

  // 1. Camera transition animation
  if (camAnim) {
    camAnim.update(now);
  }

  // 2. Stage 1: Costa Smeralda 4-Layer Cutaway Smooth Vertical Interpolation & Ocean Motion
  if (currentStage === 'ship') {
    shipStageGroup.position.y = Math.sin(now * 0.0014) * 0.08;

    const lerpRate = Math.min(1.0, dt * 6.5);
    for (const key of ['L1', 'L2', 'L3', 'L4']) {
      const node = shipLayerNodes[key];
      if (node) {
        node.position.y += (shipLayerTargetY[key] - node.position.y) * lerpRate;
      }
    }
    controls.update();
  }

  // 3. Stage 2: Interior Walk Mode movement (across Block 1, Corridor, and Block 2) or OrbitControls
  if (currentStage === 'interior') {
    if (currentCamMode === 'walk') {
      const speed = 3.4 * dt;
      const forwardFlat = new THREE.Vector3(-Math.sin(walkYaw), 0, -Math.cos(walkYaw));
      const rightFlat = new THREE.Vector3(Math.cos(walkYaw), 0, -Math.sin(walkYaw));

      if (walkKeys.forward) perspCamera.position.addScaledVector(forwardFlat, speed);
      if (walkKeys.backward) perspCamera.position.addScaledVector(forwardFlat, -speed);
      if (walkKeys.right) perspCamera.position.addScaledVector(rightFlat, speed);
      if (walkKeys.left) perspCamera.position.addScaledVector(rightFlat, -speed);

      // Keep walk camera inside the 2-Block Arlecchino bounds (X: -1.85..10.1, Z: -17.0..-0.55)
      perspCamera.position.x = Math.max(-1.85, Math.min(10.1, perspCamera.position.x));
      perspCamera.position.z = Math.max(-17.0, Math.min(-0.55, perspCamera.position.z));
      perspCamera.position.y = 1.62;
      syncWalkCameraLook();
    } else {
      controls.update();
    }

    // 4. Smoothly animate Glassmorphism Pre-Selection & Selection Pads on all 24 tables
    for (const [num, entry] of tableRegistry) {
      if (!entry.glassPad) continue;
      const isHov = hoveredTableNum === num;
      const isSel = selectedTables.has(num);
      const isLock = lockedTables.has(num);

      const mat = entry.glassPad.material;
      const bMat = entry.glassBorder.material;

      let targetOp = 0.0;
      let targetBorderOp = 0.0;

      if (isLock) {
        mat.color.setHex(0xef4444);
        mat.emissive.setHex(0x991b1b);
        bMat.color.setHex(0xf87171);
        targetOp = isHov ? 0.42 : 0.22;
        targetBorderOp = isHov ? 0.9 : 0.45;
      } else if (isSel) {
        mat.color.setHex(0x10b981);
        mat.emissive.setHex(0x059669);
        bMat.color.setHex(0x6ee7b7);
        targetOp = isHov ? 0.62 : 0.46;
        targetBorderOp = 0.95;
      } else if (isHov) {
        mat.color.setHex(0x38bdf8);
        mat.emissive.setHex(0x0ea5e9);
        bMat.color.setHex(0xbae6fd);
        targetOp = 0.52;
        targetBorderOp = 1.0;
      }

      mat.opacity += (targetOp - mat.opacity) * 0.18;
      bMat.opacity += (targetBorderOp - bMat.opacity) * 0.18;
    }
  }

  renderer.render(scene, activeCamera);
  labelRenderer.render(scene, activeCamera);
}

requestAnimationFrame(animate);
