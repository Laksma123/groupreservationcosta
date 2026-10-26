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
// 1. DRS 4-BLOCK TABLE CATALOG (45 TABLES / 220 SEATS — 100% ENGLISH)
// ============================================================================
const TABLE_CATALOG = [
  // --- BLOCK 1: PORTSIDE FORWARD (10 TABLES · 52 SEATS) ---
  {
    num: '301',
    block: 'B1',
    nodeKey: '301_Window_Booth',
    pax: 4,
    zone: 'Block 1 Port · Window Booth',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '303',
    block: 'B1',
    nodeKey: '303_Window_Bay1',
    pax: 6,
    zone: 'Block 1 Port · Ocean Window (Bay 1)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '305',
    block: 'B1',
    nodeKey: '305_Window_Bay2',
    pax: 6,
    zone: 'Block 1 Port · Ocean Window (Bay 2)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '307',
    block: 'B1',
    nodeKey: '307_Window_Bay3',
    pax: 6,
    zone: 'Block 1 Port · Ocean Window (Bay 3)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '399',
    block: 'B1',
    nodeKey: '399_Center_Fwd',
    pax: 6,
    zone: 'Block 1 Port · Center Row (Forward)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '397',
    block: 'B1',
    nodeKey: '397_Center_Mid',
    pax: 6,
    zone: 'Block 1 Port · Center Row (Mid)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '393',
    block: 'B1',
    nodeKey: '393_Center_Aft',
    pax: 6,
    zone: 'Block 1 Port · Center Row (Aft)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '403',
    block: 'B1',
    nodeKey: '403_Railing_FwdBay',
    pax: 4,
    zone: 'Block 1 Port · Railing Row (Bay 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Corridor Side',
  },
  {
    num: '405',
    block: 'B1',
    nodeKey: '405_Railing_MidBay',
    pax: 4,
    zone: 'Block 1 Port · Railing Row (Bay 2)',
    chairDesc: '4 Ivory Leatherette Chairs · Corridor Side',
  },
  {
    num: '407',
    block: 'B1',
    nodeKey: '407_Railing_AftBay',
    pax: 4,
    zone: 'Block 1 Port · Railing Row (Entrance 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Entrance 1',
  },

  // --- BLOCK 2: STARBOARDSIDE FORWARD (14 TABLES · 60 SEATS) ---
  {
    num: '468',
    block: 'B2',
    nodeKey: '468_B2_Railing_Fwd',
    pax: 4,
    zone: 'Block 2 Stbd · Railing Row (Bay 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Corridor Side',
  },
  {
    num: '470',
    block: 'B2',
    nodeKey: '470_B2_Railing_Mid',
    pax: 4,
    zone: 'Block 2 Stbd · Railing Row (Bay 2)',
    chairDesc: '4 Ivory Leatherette Chairs · Corridor Side',
  },
  {
    num: '472',
    block: 'B2',
    nodeKey: '472_B2_Railing_Aft',
    pax: 4,
    zone: 'Block 2 Stbd · Railing Row (Entrance 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Entrance 1',
  },
  {
    num: '462',
    block: 'B2',
    nodeKey: '462_B2_Center_Fwd',
    pax: 6,
    zone: 'Block 2 Stbd · Center Row (Forward)',
    chairDesc: '6 Burgundy Velvet Chairs · 1.15m Aisle',
  },
  {
    num: '460',
    block: 'B2',
    nodeKey: '460_B2_Center_Mid',
    pax: 6,
    zone: 'Block 2 Stbd · Center Row (Mid)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '458',
    block: 'B2',
    nodeKey: '458_B2_Center_Aft',
    pax: 6,
    zone: 'Block 2 Stbd · Center Row (Aft)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '466',
    block: 'B2',
    nodeKey: '466_B2_Entrance2_Sofa1',
    pax: 4,
    zone: 'Block 2 Stbd · Entrance 2 Booth (#1)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '464',
    block: 'B2',
    nodeKey: '464_B2_Entrance2_Sofa2',
    pax: 4,
    zone: 'Block 2 Stbd · Entrance 2 Booth (#2)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '384',
    block: 'B2',
    nodeKey: '384_B2_Sofa_4Pax_1',
    pax: 4,
    zone: 'Block 2 Stbd · Inboard Sofa Wall (4P #1)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '382',
    block: 'B2',
    nodeKey: '382_B2_Sofa_2Pax_1',
    pax: 2,
    zone: 'Block 2 Stbd · Inboard Sofa Wall (2P #1)',
    chairDesc: 'Red Banquette Sofa + 1 Ivory Chair',
  },
  {
    num: '380',
    block: 'B2',
    nodeKey: '380_B2_Sofa_4Pax_2',
    pax: 4,
    zone: 'Block 2 Stbd · Inboard Sofa Wall (4P #2)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '378',
    block: 'B2',
    nodeKey: '378_B2_Sofa_2Pax_2',
    pax: 2,
    zone: 'Block 2 Stbd · Inboard Sofa Wall (2P #2)',
    chairDesc: 'Red Banquette Sofa + 1 Ivory Chair',
  },
  {
    num: '376',
    block: 'B2',
    nodeKey: '376_B2_Sofa_2Pax_3',
    pax: 2,
    zone: 'Block 2 Stbd · Inboard Sofa Wall (2P #3)',
    chairDesc: 'Red Banquette Sofa + 1 Ivory Chair',
  },
  {
    num: '374',
    block: 'B2',
    nodeKey: '374_B2_Sofa_4Pax_3',
    pax: 4,
    zone: 'Block 2 Stbd · Inboard Sofa Wall (4P #3)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },

  // --- BLOCK 3: PORTSIDE AFT (9 TABLES · 54 SEATS) ---
  {
    num: '309',
    block: 'B3',
    nodeKey: '309_B3_Window_1',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (#1)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '311',
    block: 'B3',
    nodeKey: '311_B3_Window_2',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (#2)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '313',
    block: 'B3',
    nodeKey: '313_B3_Window_3',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (#3)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '315',
    block: 'B3',
    nodeKey: '315_B3_Window_4',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (#4)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '391',
    block: 'B3',
    nodeKey: '391_B3_Center_8Pax',
    pax: 8,
    zone: 'Block 3 Port · Center Row (8-Pax Table)',
    chairDesc: '8 Burgundy Velvet Chairs',
  },
  {
    num: '389',
    block: 'B3',
    nodeKey: '389_B3_Center_10Pax',
    pax: 10,
    zone: 'Block 3 Port · Center Row (10-Pax Table)',
    chairDesc: '10 Burgundy Velvet Chairs',
  },
  {
    num: '409',
    block: 'B3',
    nodeKey: '409_B3_Railing_Fwd',
    pax: 4,
    zone: 'Block 3 Port · Railing Row (Entrance 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '411',
    block: 'B3',
    nodeKey: '411_B3_Railing_Mid',
    pax: 4,
    zone: 'Block 3 Port · Railing Row (Mid Bay)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '413',
    block: 'B3',
    nodeKey: '413_B3_Railing_Aft',
    pax: 4,
    zone: 'Block 3 Port · Railing Row (Aft Bay)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },

  // --- BLOCK 4: STARBOARDSIDE AFT (12 TABLES · 54 SEATS) ---
  {
    num: '474',
    block: 'B4',
    nodeKey: '474_B4_Railing_Fwd',
    pax: 4,
    zone: 'Block 4 Stbd · Railing Row (Entrance 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '476',
    block: 'B4',
    nodeKey: '476_B4_Railing_Mid',
    pax: 4,
    zone: 'Block 4 Stbd · Railing Row (Mid Bay)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '478',
    block: 'B4',
    nodeKey: '478_B4_Railing_Aft',
    pax: 4,
    zone: 'Block 4 Stbd · Railing Row (Aft Bay)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '456',
    block: 'B4',
    nodeKey: '456_B4_Center_Fwd',
    pax: 6,
    zone: 'Block 4 Stbd · Center Row (+50cm Aft #1)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '454',
    block: 'B4',
    nodeKey: '454_B4_Center_Mid',
    pax: 6,
    zone: 'Block 4 Stbd · Center Row (+50cm Aft #2)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '452',
    block: 'B4',
    nodeKey: '452_B4_Center_Aft',
    pax: 6,
    zone: 'Block 4 Stbd · Center Row (+50cm Aft #3)',
    chairDesc: '6 Burgundy Velvet Chairs',
  },
  {
    num: '386',
    block: 'B4',
    nodeKey: '386_B4_Sofa_4Pax_1',
    pax: 4,
    zone: 'Block 4 Stbd · Inboard Sofa Wall (4P #1)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '388',
    block: 'B4',
    nodeKey: '388_B4_Sofa_4Pax_2',
    pax: 4,
    zone: 'Block 4 Stbd · Inboard Sofa Wall (4P #2)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '390',
    block: 'B4',
    nodeKey: '390_B4_Sofa_4Pax_3',
    pax: 4,
    zone: 'Block 4 Stbd · Inboard Sofa Wall (4P #3)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '392',
    block: 'B4',
    nodeKey: '392_B4_Sofa_4Pax_4',
    pax: 4,
    zone: 'Block 4 Stbd · Inboard Sofa Wall (4P #4)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '394',
    block: 'B4',
    nodeKey: '394_B4_Sofa_4Pax_5',
    pax: 4,
    zone: 'Block 4 Stbd · Inboard Sofa Wall (4P #5)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
  {
    num: '396',
    block: 'B4',
    nodeKey: '396_B4_Sofa_4Pax_6',
    pax: 4,
    zone: 'Block 4 Stbd · Inboard Sofa Wall (4P #6)',
    chairDesc: 'Red Banquette Sofa + 2 Ivory Chairs',
  },
];

const ACCESS_PRESETS = {
  A98XKJ90: {
    code: 'A98XKJ90',
    groupName: 'Milano Corporate Incentive (4-Block Allocation)',
    targetPax: 44,
    lockedTables: ['301', '407', '374', '376', '409', '474'],
    recommended: ['399', '397', '403', '405', '468', '470', '462', '460'],
  },
  DIAMOND28: {
    code: 'DIAMOND28',
    groupName: 'Costa Club Diamond Family Group',
    targetPax: 28,
    lockedTables: ['393', '407', '472', '458'],
    recommended: ['466', '464', '462', '460', '384', '380'],
  },
  CHARTER112: {
    code: 'CHARTER112',
    groupName: 'Full 4-Block Arlecchino Charter (45 Tables)',
    targetPax: 220,
    lockedTables: [],
    recommended: TABLE_CATALOG.map((t) => t.num),
  },
};

const WALK_SPOTS = {
  crossroads: {
    pos: new THREE.Vector3(14.85, 1.52, -8.73),
    yaw: Math.PI * 0.5,
    pitch: -0.02,
  },
  corridor_b12: {
    pos: new THREE.Vector3(5.2, 1.62, -8.73),
    yaw: Math.PI * 0.5,
    pitch: -0.05,
  },
  corridor_b34: {
    pos: new THREE.Vector3(20.6, 1.62, -8.73),
    yaw: -Math.PI * 0.5,
    pitch: -0.05,
  },
  b1_center: {
    pos: new THREE.Vector3(7.6, 1.62, -4.5),
    yaw: Math.PI * 0.35,
    pitch: -0.05,
  },
  b2_center: {
    pos: new THREE.Vector3(5.2, 1.62, -13.2),
    yaw: -Math.PI * 0.25,
    pitch: -0.05,
  },
  b3_center: {
    pos: new THREE.Vector3(18.2, 1.62, -4.5),
    yaw: -Math.PI * 0.35,
    pitch: -0.05,
  },
  b4_center: {
    pos: new THREE.Vector3(20.6, 1.62, -13.2),
    yaw: -Math.PI * 0.65,
    pitch: -0.05,
  },
};

// ============================================================================
// 2. HIGH-PERFORMANCE SCENE, RENDERERS & CAMERAS
// ============================================================================
const canvas = document.getElementById('webgl-canvas');
const css2dContainer = document.getElementById('css2d-layer');

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight - 57);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
// Performance optimization: Do NOT re-render shadow maps 60 times/sec on static geometry!
renderer.shadowMap.autoUpdate = false;

const maxAnisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());

function requestShadowUpdate() {
  renderer.shadowMap.needsUpdate = true;
}

function fixFloorAndCarpetMesh(child) {
  const n = child.name || '';
  // 1. Eliminate coplanar Z-fighting on red carpet & tile alcoves:
  // Floor_Dining_Carpet already covers X=[-1.55, 10.40], Y=[0, 7.58] up to the Waiter Station face.
  // Floor_Dining_Carpet_Alcove overlapped X=[-1.55, -0.05] at the exact same Z=0.0000 with shifted UVs!
  if (n.includes('Floor_Dining_Carpet_Alcove')) {
    child.visible = false;
    return;
  }
  if (
    n.includes('Floor_Block2_Carpet_Alcove') ||
    n.includes('Floor_Rotunda_Aft_Tile')
  ) {
    child.position.y -= 0.006;
    if (child.material) {
      child.material = child.material.clone();
      child.material.polygonOffset = true;
      child.material.polygonOffsetFactor = 4;
      child.material.polygonOffsetUnits = 4;
    }
  }

  // 2. Ensure uniform rich Venetian crimson color & sharp anisotropic filtering on carpets/tiles
  const mats = Array.isArray(child.material) ? child.material : [child.material];
  for (const mat of mats) {
    if (!mat) continue;
    if (mat.map && mat.map.anisotropy < maxAnisotropy) {
      mat.map.anisotropy = maxAnisotropy;
      mat.map.needsUpdate = true;
    }
    if (mat.bumpMap && mat.bumpMap.anisotropy < maxAnisotropy) {
      mat.bumpMap.anisotropy = maxAnisotropy;
      mat.bumpMap.needsUpdate = true;
    }
    if (
      (mat.name && mat.name.includes('Mat_Arlecchino_Carpet')) ||
      n.includes('Carpet')
    ) {
      // Remove white grazing-angle sheen that washed out carpet color into pale pink
      if ('sheen' in mat) mat.sheen = 0;
      if ('sheenRoughness' in mat) mat.sheenRoughness = 1.0;
      mat.roughness = 0.92;
      mat.metalness = 0.0;
      mat.needsUpdate = true;
    }
  }
}

const labelRenderer = new CSS2DRenderer({ element: css2dContainer });
labelRenderer.setSize(window.innerWidth, window.innerHeight - 57);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07192b);
scene.fog = new THREE.FogExp2(0x07192b, 0.0042);

const viewAspect = window.innerWidth / Math.max(1, window.innerHeight - 57);
const perspCamera = new THREE.PerspectiveCamera(42, viewAspect, 0.1, 450);

const orthoFrustumH = 21.8;
const orthoCamera = new THREE.OrthographicCamera(
  (-orthoFrustumH * viewAspect) / 2,
  (orthoFrustumH * viewAspect) / 2,
  orthoFrustumH / 2,
  -orthoFrustumH / 2,
  0.1,
  120
);

let activeCamera = perspCamera;

const controls = new OrbitControls(perspCamera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.maxDistance = 150;
controls.minDistance = 1.2;

let isOrbitDragging = false;
controls.addEventListener('start', () => {
  isOrbitDragging = true;
});
controls.addEventListener('end', () => {
  isOrbitDragging = false;
});

// Global Lighting
const ambientLight = new THREE.AmbientLight(0xfff7eb, 1.55);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0xe0f2fe, 0x3b2314, 1.25);
hemiLight.position.set(0, 32, 0);
scene.add(hemiLight);

const sunLight = new THREE.DirectionalLight(0xfffbeb, 2.3);
sunLight.position.set(28, 42, 34);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(1024, 1024);
sunLight.shadow.bias = -0.0005;
sunLight.shadow.camera.near = 2;
sunLight.shadow.camera.far = 140;
sunLight.shadow.camera.left = -45;
sunLight.shadow.camera.right = 45;
sunLight.shadow.camera.top = 35;
sunLight.shadow.camera.bottom = -35;
sunLight.shadow.camera.updateProjectionMatrix();
scene.add(sunLight);

// Symmetrical Interior Fill Lighting across all 4 Blocks, Corridors & Crossroads (No harsh hotspots)
const interiorLightGroup = new THREE.Group();
scene.add(interiorLightGroup);
[
  [4.5, 3.2, -3.8, 0xffe8c2, 1.6, 22.0],    // Block 1 Portside Forward fill
  [4.5, 3.2, -8.73, 0xfff0d4, 1.4, 18.0],   // B1–B2 Medallion Corridor
  [4.5, 3.2, -13.68, 0xffe8c2, 1.6, 22.0],  // Block 2 Starboardside Forward fill
  [12.9, 2.7, -8.73, 0xffe8c2, 1.85, 22.0], // Aft Crossroads, Clover Table & Murano Chandelier
  [21.3, 3.2, -3.8, 0xffe8c2, 1.6, 22.0],   // Block 3 Portside Aft fill
  [21.3, 3.2, -8.73, 0xfff0d4, 1.4, 18.0],  // B3–B4 Medallion Corridor
  [21.3, 3.2, -13.68, 0xffe8c2, 1.6, 22.0], // Block 4 Starboardside Aft fill
].forEach(([lx, ly, lz, col, intensity, dist]) => {
  const pt = new THREE.PointLight(col, intensity, dist, 0.9);
  pt.castShadow = false;
  pt.position.set(lx, ly, lz);
  interiorLightGroup.add(pt);
});
interiorLightGroup.visible = false;

// ============================================================================
// 3. STAGE 1: COSTA SMERALDA 3D MODEL & 4-LAYER CUTAWAY SYSTEM
// ============================================================================
const shipStageGroup = new THREE.Group();
scene.add(shipStageGroup);

// Lightweight Mediterranean Sea Plane
const seaGeo = new THREE.PlaneGeometry(360, 360, 8, 8);
seaGeo.rotateX(-Math.PI / 2);
const seaMat = new THREE.MeshStandardMaterial({
  color: 0x063b61,
  roughness: 0.24,
  metalness: 0.32,
});
const oceanMesh = new THREE.Mesh(seaGeo, seaMat);
oceanMesh.position.y = -0.05;
oceanMesh.receiveShadow = true;
shipStageGroup.add(oceanMesh);

const shipLayerNodes = {
  L0: null,
  L1: null,
  L2: null,
  L3: null,
  L4: null,
};

const shipLayerTargetY = { L1: 0, L2: 0, L3: 0, L4: 0 };
let currentCutawayMode = 'full';
let arlecchinoHitboxMesh = null;

// Clean, Minimal 3D English Labels on the Ship
const deckCutawayLabels = {
  colombina: null,
  meneghino: null,
  arlecchinoMain: null,
  rugantino: null,
};

function makeDeckLabel(text, cssClass, posVec3, parentNode, onClick = null) {
  const el = document.createElement(onClick ? 'button' : 'div');
  if (onClick) el.type = 'button';
  el.className = `${cssClass} is-hidden`;
  el.textContent = text;
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
    requestShadowUpdate();
    loaderOverlay.classList.add('is-hidden');
  }
}

gltfLoader.load(
  './costa_smeralda_ship.glb?v=20261026h',
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
        fixFloorAndCarpetMesh(child);
        // Only cast shadows on exterior ship hull/superstructure, not tiny embedded tableware
        const isEmbeddedDetail =
          child.parent &&
          (child.parent.name === 'L2_Arlecchino_2Block_RealModel' ||
            (child.parent.parent && child.parent.parent.name === 'L2_Arlecchino_2Block_RealModel'));
        child.castShadow = !isEmbeddedDetail;
        child.receiveShadow = true;

        if (child.name === 'L2_Arlecchino_2Block_Active_Hitbox') {
          arlecchinoHitboxMesh = child;
        }
      }
    });

    if (shipLayerNodes.L1) {
      deckCutawayLabels.colombina = makeDeckLabel(
        'Deck 5 Aft · La Colombina (Placeholder)',
        'ship-deck-label',
        new THREE.Vector3(-25.5, 2.8, 0.0),
        shipLayerNodes.L1
      );
    }

    if (shipLayerNodes.L2) {
      deckCutawayLabels.meneghino = makeDeckLabel(
        'Deck 6 Aft · Il Meneghino (Placeholder)',
        'ship-deck-label',
        new THREE.Vector3(-25.8, 3.7, 0.0),
        shipLayerNodes.L2
      );
    }

    if (shipLayerNodes.L3) {
      deckCutawayLabels.rugantino = makeDeckLabel(
        'Deck 7 Aft · Il Rugantino (Placeholder)',
        'ship-deck-label',
        new THREE.Vector3(-25.6, 4.5, 0.0),
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

const CUTAWAY_META = {
  full: {
    eyebrow: 'COSTA SMERALDA · EXTERIOR OVERVIEW',
    title: 'Ristorante Arlecchino',
    desc: 'Select a deck layer above or open Deck 6 to inspect the 4 completed blocks of Ristorante Arlecchino.',
    subtitle: 'GROUP DINING RESERVATION SYSTEM',
  },
  deck7: {
    eyebrow: 'CUTAWAY LAYER 3 · DECK 7 POSITANO',
    title: 'Ristorante Il Rugantino',
    desc: 'Deck 8 to upper funnel lifted as one unit. Aft zone shows Il Rugantino (546 seats) placeholder.',
    subtitle: 'DECK 7 CUTAWAY · IL RUGANTINO (PLACEHOLDER)',
  },
  deck6: {
    eyebrow: 'CUTAWAY LAYER 2 · DECK 6 ROMA',
    title: 'Ristorante Arlecchino',
    desc: 'Mid-ship displays the 4 completed blocks of Arlecchino in full 3D detail. Aft shows Il Meneghino placeholder.',
    subtitle: 'DECK 6 CUTAWAY · ARLECCHINO (4 BLOCKS) & MENEGHINO',
  },
  deck5: {
    eyebrow: 'CUTAWAY LAYER 1 · DECK 5 TAORMINA',
    title: 'Ristorante La Colombina',
    desc: 'Decks 6, 7, and 8–Funnel lifted in stepped tiers. Aft shows La Colombina (978 seats) placeholder.',
    subtitle: 'DECK 5 CUTAWAY · LA COLOMBINA (PLACEHOLDER)',
  },
};

function setShipCutawayLayer(layerMode, animateCam = true) {
  currentCutawayMode = layerMode;

  document.querySelectorAll('[data-cutaway-layer]').forEach((btn) => {
    const isAct = btn.dataset.cutawayLayer === layerMode;
    btn.classList.toggle('active', isAct);
    if (btn.hasAttribute('aria-pressed')) {
      btn.setAttribute('aria-pressed', String(isAct));
    }
  });

  const info = CUTAWAY_META[layerMode] || CUTAWAY_META.full;
  document.getElementById('ship-card-eyebrow').textContent = info.eyebrow;
  document.getElementById('ship-card-title').innerHTML = `${info.title}<span class="title-dot">.</span>`;
  document.getElementById('ship-card-desc').textContent = info.desc;
  document.getElementById('stage-subtitle').textContent = info.subtitle;

  if (deckCutawayLabels.colombina) {
    deckCutawayLabels.colombina.el.classList.toggle('is-hidden', layerMode !== 'deck5');
  }
  if (deckCutawayLabels.meneghino) {
    deckCutawayLabels.meneghino.el.classList.toggle('is-hidden', layerMode !== 'deck6');
  }
  if (deckCutawayLabels.rugantino) {
    deckCutawayLabels.rugantino.el.classList.toggle('is-hidden', layerMode !== 'deck7');
  }
  if (deckCutawayLabels.arlecchinoMain) {
    const showArl = currentStage === 'ship' && (layerMode === 'full' || layerMode === 'deck6');
    deckCutawayLabels.arlecchinoMain.el.classList.toggle('is-hidden', !showArl);
  }

  if (layerMode === 'full') {
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 0;
    shipLayerTargetY.L4 = 0;
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(34, 17, 46), new THREE.Vector3(0, 5.2, 0), 850);
    }
  } else if (layerMode === 'deck7') {
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 0;
    shipLayerTargetY.L4 = 8.5;
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(-18, 15.5, 32), new THREE.Vector3(-12, 4.2, 0), 850);
    }
  } else if (layerMode === 'deck6') {
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 6.5;
    shipLayerTargetY.L4 = 13.5;
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(5, 13.5, 24), new THREE.Vector3(-3.5, 3.2, 0), 850);
    }
  } else if (layerMode === 'deck5') {
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 5.5;
    shipLayerTargetY.L3 = 11.0;
    shipLayerTargetY.L4 = 17.5;
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(-18, 14.0, 32), new THREE.Vector3(-14, 2.5, 0), 850);
    }
  }
}

// ============================================================================
// 4. STAGE 2: LOAD 2-BLOCK ARLECCHINO GLB & FAST BOUNDING-BOX RAYCAST PROXIES
// ============================================================================
const restaurantGroup = new THREE.Group();
restaurantGroup.visible = false;
scene.add(restaurantGroup);

const ceilingMeshes = [];
const chandelierMeshes = [];
const tableRegistry = new Map();
// Performance optimization: Raycast ONLY against 24 lightweight bounding-box proxies (288 tris total)!
const interactiveHitProxies = [];

const hitProxyMat = new THREE.MeshBasicMaterial({
  visible: false,
});

gltfLoader.load(
  './arlecchino_block1.glb?v=20261026h',
  (gltf) => {
    const model = gltf.scene;
    restaurantGroup.add(model);

    model.traverse((child) => {
      if (!child.isMesh) return;
      fixFloorAndCarpetMesh(child);
      const n = child.name || '';

      // Only cast shadows on main structural objects, not small plates/glasses/frames
      const isSmallDetail =
        n.includes('Plate') ||
        n.includes('Phone') ||
        n.includes('Spot') ||
        n.includes('Downlight') ||
        n.includes('Art') ||
        n.includes('Chandelier');
      child.castShadow = !isSmallDetail;
      child.receiveShadow = true;

      if (n.startsWith('Ceiling_Chandelier_')) {
        chandelierMeshes.push(child);
      } else if (
        n.startsWith('Ceiling_') ||
        n.startsWith('CeilBeam_') ||
        n.startsWith('B2_CeilBeam_') ||
        n.startsWith('B3_CeilBeam_') ||
        n.startsWith('B4_CeilBeam_') ||
        n.startsWith('B3B4_Ceiling_') ||
        n.startsWith('RedSpot_') ||
        n.startsWith('B2_RedSpot_') ||
        n.startsWith('B3_RedSpot_') ||
        n.startsWith('B4_RedSpot_') ||
        n.startsWith('Corr_Downlight_') ||
        n.startsWith('B3B4_Corr_Downlight_') ||
        n.startsWith('Crossroads_Header_Beam_') ||
        n.startsWith('Crossroads_ExitSign_')
      ) {
        ceilingMeshes.push(child);
      }

      for (const meta of TABLE_CATALOG) {
        if (
          n.includes(meta.nodeKey) ||
          (meta.num === '301' && n.startsWith('Banquette_'))
        ) {
          if (!tableRegistry.has(meta.num)) {
            tableRegistry.set(meta.num, {
              meta,
              meshes: [],
              topMesh: null,
              glassPad: null,
              glassBorder: null,
              labelObj: null,
              labelEl: null,
              rowEl: null,
              rowBadgeEl: null,
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

    model.updateMatrixWorld(true);

    for (const meta of TABLE_CATALOG) {
      const entry = tableRegistry.get(meta.num);
      if (!entry || !entry.topMesh) continue;

      const topBox = new THREE.Box3().setFromObject(entry.topMesh);
      topBox.getCenter(entry.center);
      topBox.getSize(entry.size);

      // Compute full table + chairs bounding box for a single 12-triangle raycast hit proxy
      const fullBox = new THREE.Box3();
      for (const m of entry.meshes) {
        fullBox.expandByObject(m);
      }
      const fullCenter = new THREE.Vector3();
      const fullSize = new THREE.Vector3();
      fullBox.getCenter(fullCenter);
      fullBox.getSize(fullSize);

      const proxyGeo = new THREE.BoxGeometry(
        Math.max(fullSize.x, 0.8),
        Math.max(fullSize.y, 0.8),
        Math.max(fullSize.z, 0.8)
      );
      const proxyMesh = new THREE.Mesh(proxyGeo, hitProxyMat);
      proxyMesh.position.copy(fullCenter);
      proxyMesh.userData.tableNum = meta.num;
      restaurantGroup.add(proxyMesh);
      interactiveHitProxies.push(proxyMesh);

      // Lightweight Selection Pad on the tabletop (MeshStandardMaterial = zero transmission overhead)
      const padW = Math.max(entry.size.x - 0.03, 0.45);
      const padD = Math.max(entry.size.z - 0.03, 0.45);
      const padGeo = new THREE.BoxGeometry(padW, 0.016, padD);

      const padMat = new THREE.MeshStandardMaterial({
        color: 0x0071a3,
        emissive: 0x0071a3,
        emissiveIntensity: 0.35,
        roughness: 0.2,
        metalness: 0.1,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
      });

      const glassPad = new THREE.Mesh(padGeo, padMat);
      glassPad.position.set(entry.center.x, topBox.max.y + 0.012, entry.center.z);
      restaurantGroup.add(glassPad);
      entry.glassPad = glassPad;

      const edgeGeo = new THREE.EdgesGeometry(padGeo);
      const edgeMat = new THREE.LineBasicMaterial({
        color: 0x0071a3,
        transparent: true,
        opacity: 0.0,
      });
      const glassBorder = new THREE.LineSegments(edgeGeo, edgeMat);
      glassPad.add(glassBorder);
      entry.glassBorder = glassBorder;

      // Compact 3D Table Number Pill (Zero backdrop-filter blur)
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
      labelObj.position.set(entry.center.x, topBox.max.y + 0.07, entry.center.z);
      restaurantGroup.add(labelObj);
      entry.labelObj = labelObj;
      entry.labelEl = markerEl;
    }

    buildSidebarTableRowsOnce();
    applyAccessPreset(currentPresetKey);
    interiorGlbLoaded = true;
    checkAllLoaded();
  },
  undefined,
  (err) => {
    console.error('Error loading arlecchino_block1.glb:', err);
    document.getElementById('loader-title').textContent = 'Failed to load 3D model (.glb)';
  }
);

// ============================================================================
// 5. STATE MANAGEMENT: STAGES, CAMERA MODES, HOVER & IN-PLACE DOM UPDATES
// ============================================================================
let currentStage = 'ship';
let currentCamMode = 'bird';
let top2dFlipped = false;
let showTableNumbers = true;
let activeBlockFilter = 'all';

let currentPresetKey = 'A98XKJ90';
let selectedTables = new Set();
let lockedTables = new Set();
let hoveredTableNum = null;

let camAnim = null;

function animateCameraTo(targetPos, targetLookAt, durationMs = 800, onDone = null) {
  const startPos = activeCamera.position.clone();
  const startLook = controls.target.clone();
  const startTime = performance.now();

  camAnim = {
    update(now) {
      const t = Math.min(1, (now - startTime) / durationMs);
      const ease = 1 - Math.pow(1 - t, 3);
      activeCamera.position.lerpVectors(startPos, targetPos, ease);
      controls.target.lerpVectors(startLook, targetLookAt, ease);
      if (t >= 1) {
        camAnim = null;
        if (onDone) onDone();
      }
    },
  };
}

function setHeroShipCamera(instant = false) {
  currentStage = 'ship';
  activeCamera = perspCamera;
  perspCamera.fov = 42;
  perspCamera.up.set(0, 1, 0);
  perspCamera.updateProjectionMatrix();

  controls.object = perspCamera;
  controls.enabled = true;
  controls.enableRotate = true;
  controls.maxPolarAngle = Math.PI * 0.48;

  // Restore exterior ship lighting & shadow map
  sunLight.position.set(28, 42, 34);
  sunLight.intensity = 2.3;
  sunLight.castShadow = true;
  ambientLight.intensity = 1.55;
  hemiLight.intensity = 1.25;

  shipStageGroup.visible = true;
  restaurantGroup.visible = false;
  interiorLightGroup.visible = false;
  updateTableMarkersVisibility();
  requestShadowUpdate();

  document.getElementById('hero-ship-ui').classList.add('is-active');
  document.getElementById('interior-ui').classList.remove('is-active');
  document.getElementById('ship-toolbar').hidden = false;
  document.getElementById('interior-toolbar').hidden = true;

  // Always return to Full Ship view on Dashboard when clicking Costa Smeralda title
  setShipCutawayLayer('full', !instant);
  if (instant) {
    perspCamera.position.set(34, 17, 46);
    controls.target.set(0, 5.2, 0);
    controls.update();
  }
}

setHeroShipCamera(true);

function enterInterior2Blocks() {
  if (currentStage === 'interior') return;

  setShipCutawayLayer('deck6', false);

  Object.values(deckCutawayLabels).forEach((lbl) => {
    if (lbl && lbl.el) lbl.el.classList.add('is-hidden');
  });

  animateCameraTo(
    new THREE.Vector3(-0.5, 5.2, 6.8),
    new THREE.Vector3(-1.5, 3.0, 1.5),
    750,
    () => {
      currentStage = 'interior';
      shipStageGroup.visible = false;
      restaurantGroup.visible = true;
      interiorLightGroup.visible = true;

      // Uniform symmetrical interior lighting (prevents exterior wall shadows or color differences between Blocks 1–4)
      sunLight.position.set(12.9, 48, -8.73);
      sunLight.intensity = 1.15;
      sunLight.castShadow = false;
      ambientLight.intensity = 1.75;
      hemiLight.intensity = 1.3;

      document.getElementById('hero-ship-ui').classList.remove('is-active');
      document.getElementById('interior-ui').classList.add('is-active');
      document.getElementById('ship-toolbar').hidden = true;
      document.getElementById('interior-toolbar').hidden = false;
      document.getElementById('stage-subtitle').textContent =
        'DECK 6 ROMA · RISTORANTE ARLECCHINO (4 BLOCKS · 45 TABLES)';

      setInteriorCameraMode('bird');
      updateTableMarkersVisibility();
    }
  );
}

function setCeilingVisible(vis, showChandelier = vis) {
  for (const m of ceilingMeshes) {
    m.visible = vis;
  }
  for (const m of chandelierMeshes) {
    m.visible = showChandelier;
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
// 6. THREE INTERIOR CAMERA MODES: BIRD'S-EYE, 2D PLAN, WALK MODE
// ============================================================================
let walkYaw = WALK_SPOTS.crossroads.yaw;
let walkPitch = WALK_SPOTS.crossroads.pitch;
const walkKeys = { forward: false, backward: false, left: false, right: false };
let isDraggingLook = false;
let prevPointer = { x: 0, y: 0 };

function setInteriorCameraMode(mode) {
  currentCamMode = mode;

  document.querySelectorAll('.mode-btn').forEach((btn) => {
    const isAct = btn.dataset.camMode === mode;
    btn.classList.toggle('active', isAct);
    btn.setAttribute('aria-pressed', String(isAct));
  });

  const walkHud = document.getElementById('walk-hud');
  walkHud.hidden = mode !== 'walk';

  if (mode === 'bird') {
    setCeilingVisible(false, true);
    activeCamera = perspCamera;
    perspCamera.fov = 42;
    perspCamera.updateProjectionMatrix();

    controls.object = perspCamera;
    controls.enabled = true;
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.maxPolarAngle = Math.PI * 0.47;

    const targetPos = top2dFlipped
      ? new THREE.Vector3(-6.5, 22.0, -8.73)
      : new THREE.Vector3(32.5, 22.0, -8.73);
    const lookTarget = new THREE.Vector3(12.9, 0.55, -8.73);
    animateCameraTo(targetPos, lookTarget, 700);
  } else if (mode === 'top2d') {
    setCeilingVisible(false, false);
    camAnim = null;
    activeCamera = orthoCamera;

    const centerX = 12.9;
    const centerZ = -8.73;
    orthoCamera.position.set(centerX, 26.0, centerZ);
    orthoCamera.up.set(0, 0, top2dFlipped ? -1 : 1);
    orthoCamera.lookAt(centerX, 0.0, centerZ);
    orthoCamera.zoom = 0.72;
    orthoCamera.updateProjectionMatrix();

    controls.object = orthoCamera;
    controls.target.set(centerX, 0.0, centerZ);
    controls.enabled = true;
    controls.enableRotate = false;
    controls.enablePan = true;
    controls.update();
  } else if (mode === 'walk') {
    setCeilingVisible(true, true);
    camAnim = null;
    activeCamera = perspCamera;
    perspCamera.fov = 62;
    perspCamera.up.set(0, 1, 0);
    perspCamera.updateProjectionMatrix();

    controls.enabled = false;
    teleportWalkTo('crossroads');
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
// 7. HOVER PILL & IN-PLACE TABLE SELECTION LOGIC (ZERO DOM REBUILD)
// ============================================================================
const hoverCard = document.getElementById('hover-glass-card');

function buildSidebarTableRowsOnce() {
  const listEl = document.getElementById('sidebar-table-list');
  listEl.innerHTML = '';

  for (const meta of TABLE_CATALOG) {
    const entry = tableRegistry.get(meta.num);
    const row = document.createElement('div');
    row.className = 'table-row-item';
    row.setAttribute('role', 'listitem');
    row.innerHTML = `
      <div class="tri-left">
        <div class="tri-num">${meta.num}</div>
        <div class="tri-meta">
          <strong>Table ${meta.num} · ${meta.pax} Pax</strong>
          <small>${meta.zone}</small>
        </div>
      </div>
      <span class="tri-badge">Available</span>
    `;
    row.addEventListener('mouseenter', () => setHoveredTable(meta.num));
    row.addEventListener('mouseleave', () => setHoveredTable(null));
    row.addEventListener('click', () => toggleTableSelection(meta.num));
    listEl.appendChild(row);

    if (entry) {
      entry.rowEl = row;
      entry.rowBadgeEl = row.querySelector('.tri-badge');
    }
  }
}

function setHoveredTable(tableNum) {
  if (hoveredTableNum === tableNum) return;

  // Clear previous hovered marker
  if (hoveredTableNum && tableRegistry.has(hoveredTableNum)) {
    const prevEntry = tableRegistry.get(hoveredTableNum);
    if (prevEntry.labelEl) prevEntry.labelEl.classList.remove('is-hovered');
  }

  hoveredTableNum = tableNum;
  canvas.style.cursor = tableNum ? 'pointer' : currentCamMode === 'walk' ? 'grab' : 'default';

  if (tableNum && tableRegistry.has(tableNum)) {
    const curEntry = tableRegistry.get(tableNum);
    if (curEntry.labelEl) curEntry.labelEl.classList.add('is-hovered');
  }

  if (!tableNum || currentStage !== 'interior' || currentCamMode === 'walk') {
    hoverCard.hidden = true;
    return;
  }

  const entry = tableRegistry.get(tableNum);
  if (!entry) return;

  const isLocked = lockedTables.has(tableNum);
  const isSel = selectedTables.has(tableNum);

  const statusBadge = document.getElementById('hgc-status');
  if (isLocked) {
    statusBadge.textContent = 'Reserved';
    statusBadge.style.backgroundColor = 'var(--bad-bg)';
    statusBadge.style.color = 'var(--bad-ink)';
    statusBadge.style.border = '1px solid var(--bad-border)';
  } else if (isSel) {
    statusBadge.textContent = 'Selected';
    statusBadge.style.backgroundColor = 'var(--good-bg)';
    statusBadge.style.color = 'var(--good-ink)';
    statusBadge.style.border = '1px solid var(--good-border)';
  } else {
    statusBadge.textContent = 'Available';
    statusBadge.style.backgroundColor = 'var(--brand-dim)';
    statusBadge.style.color = 'var(--brand)';
    statusBadge.style.border = '1px solid var(--brand-border)';
  }

  document.getElementById('hgc-number').textContent = entry.meta.num;
  document.getElementById('hgc-title').textContent = `Table ${entry.meta.num} · ${entry.meta.pax} Seats`;
  document.getElementById('hgc-desc').textContent = `${entry.meta.zone} · ${entry.meta.chairDesc}`;

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
    const tmp = hoveredTableNum;
    hoveredTableNum = null;
    setHoveredTable(tmp);
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

    if (entry.rowEl) {
      const matchFilter =
        activeBlockFilter === 'all' || entry.meta.block === activeBlockFilter;
      entry.rowEl.classList.toggle('is-hidden-by-filter', !matchFilter);
      entry.rowEl.classList.toggle('is-selected', isSel);
      entry.rowEl.classList.toggle('is-locked', isLock);
      if (entry.rowBadgeEl) {
        entry.rowBadgeEl.textContent = isLock
          ? 'Locked'
          : isSel
          ? 'Selected'
          : 'Select';
      }
    }
  }

  document.getElementById('selected-pax-count').textContent = String(totalPax);
  document.getElementById('target-pax-count').textContent = String(preset.targetPax);
  document.getElementById('selected-table-count').textContent =
    `${selectedTables.size} ${selectedTables.size === 1 ? 'Table' : 'Tables'}`;

  const pct = Math.min(100, Math.round((totalPax / preset.targetPax) * 100));
  document.getElementById('pax-progress-fill').style.width = `${pct}%`;
  document.getElementById('pax-progressbar').setAttribute('aria-valuenow', String(totalPax));
  document.getElementById('pax-progressbar').setAttribute('aria-valuemax', String(preset.targetPax));

  const pill = document.getElementById('pax-status-pill');
  const diff = preset.targetPax - totalPax;
  pill.classList.remove('is-warn', 'is-good');
  if (totalPax === 0) {
    pill.textContent = `0 / ${preset.targetPax} Pax`;
  } else if (diff > 0) {
    pill.textContent = `${diff} Seats Short`;
    pill.classList.add('is-warn');
  } else {
    pill.textContent = 'Target Met';
    pill.classList.add('is-good');
  }

  const confirmBtn = document.getElementById('btn-confirm-booking');
  confirmBtn.disabled = selectedTables.size === 0;
  confirmBtn.innerHTML =
    selectedTables.size > 0
      ? `<span>Confirm Group Seating (${totalPax} Pax)</span>`
      : '<span>Confirm Group Seating (0 Pax)</span>';
}

// ============================================================================
// 8. THROTTLED RAYCASTING (1X PER FRAME MAX, FAST BOUNDING-BOX PROXIES)
// ============================================================================
const raycaster = new THREE.Raycaster();
const pointerNDC = new THREE.Vector2();
let pointerDownPos = { x: 0, y: 0 };
let pointerDirty = false;

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

  if (isOrbitDragging) return;
  updatePointerNDC(event);
  pointerDirty = true;
});

function performHoverRaycast() {
  pointerDirty = false;
  raycaster.setFromCamera(pointerNDC, activeCamera);

  if (currentStage === 'ship' && arlecchinoHitboxMesh) {
    const hits = raycaster.intersectObject(arlecchinoHitboxMesh, false);
    const hitArl = hits.length > 0;
    canvas.style.cursor = hitArl ? 'pointer' : 'grab';
    if (arlecchinoHitboxMesh.material) {
      arlecchinoHitboxMesh.material.emissiveIntensity = hitArl ? 1.1 : 0.65;
    }
    return;
  }

  if (currentStage === 'interior') {
    const hits = raycaster.intersectObjects(interactiveHitProxies, false);
    if (hits.length > 0) {
      setHoveredTable(hits[0].object.userData.tableNum || null);
    } else {
      setHoveredTable(null);
    }
  }
}

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

  if (currentStage === 'ship' && arlecchinoHitboxMesh) {
    const hits = raycaster.intersectObject(arlecchinoHitboxMesh, false);
    if (hits.length > 0) {
      enterInterior2Blocks();
    }
    return;
  }

  if (currentStage === 'interior') {
    const hits = raycaster.intersectObjects(interactiveHitProxies, false);
    if (hits.length > 0 && hits[0].object.userData.tableNum) {
      toggleTableSelection(hits[0].object.userData.tableNum);
    }
  }
});

// ============================================================================
// 9. UI EVENT LISTENERS
// ============================================================================
document.getElementById('btn-enter-deck6').addEventListener('click', enterInterior2Blocks);
document.getElementById('btn-brand-home').addEventListener('click', () => setHeroShipCamera(false));

document.querySelectorAll('[data-cutaway-layer]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const layer = btn.dataset.cutawayLayer;
    // If user clicks Deck 6 Arlecchino when already viewing Deck 6 cutaway, open the 2-block interior
    if (layer === 'deck6' && currentStage === 'ship' && currentCutawayMode === 'deck6') {
      enterInterior2Blocks();
      return;
    }
    setShipCutawayLayer(layer, true);
  });
});

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

// Collapsible Right Drawer Toggle
const drawerEl = document.getElementById('drs-drawer');
const drawerToggleBtn = document.getElementById('btn-toggle-drawer');
const drawerToggleLabel = document.getElementById('drawer-toggle-label');
let isDrawerCollapsed = false;

drawerToggleBtn.addEventListener('click', () => {
  isDrawerCollapsed = !isDrawerCollapsed;
  drawerEl.classList.toggle('is-collapsed', isDrawerCollapsed);
  drawerToggleBtn.classList.toggle('is-collapsed', isDrawerCollapsed);
  drawerToggleBtn.setAttribute('aria-expanded', String(!isDrawerCollapsed));
  drawerToggleLabel.textContent = isDrawerCollapsed ? 'Show Panel' : 'Hide Panel';
});

document.querySelectorAll('.mode-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    setInteriorCameraMode(btn.dataset.camMode);
  });
});

const tableNumSwitch = document.getElementById('toggle-table-numbers');
tableNumSwitch.addEventListener('change', () => {
  showTableNumbers = tableNumSwitch.checked;
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

document.getElementById('btn-confirm-booking').addEventListener('click', () => {
  const preset = ACCESS_PRESETS[currentPresetKey] || ACCESS_PRESETS.A98XKJ90;
  const chosenList = TABLE_CATALOG.filter((t) => selectedTables.has(t.num));
  const totalSeats = chosenList.reduce((acc, t) => acc + t.pax, 0);
  const b1List = chosenList.filter((t) => t.block === 'B1').map((t) => `#${t.num} (${t.pax}P)`);
  const b2List = chosenList.filter((t) => t.block === 'B2').map((t) => `#${t.num} (${t.pax}P)`);
  const b3List = chosenList.filter((t) => t.block === 'B3').map((t) => `#${t.num} (${t.pax}P)`);
  const b4List = chosenList.filter((t) => t.block === 'B4').map((t) => `#${t.num} (${t.pax}P)`);

  document.getElementById('dialog-summary-content').innerHTML = `
    <div><strong>Access Token:</strong> <span class="summary-mono">${preset.code}</span> — ${preset.groupName}</div>
    <div><strong>Venue:</strong> Ristorante Arlecchino · Deck 6 Roma (4 Blocks · Port &amp; Starboard)</div>
    <div><strong>Block 1 Portside (${b1List.length}):</strong> <span class="summary-mono">${b1List.join(', ') || 'None'}</span></div>
    <div><strong>Block 2 Starboard (${b2List.length}):</strong> <span class="summary-mono">${b2List.join(', ') || 'None'}</span></div>
    <div><strong>Block 3 Portside (${b3List.length}):</strong> <span class="summary-mono">${b3List.join(', ') || 'None'}</span></div>
    <div><strong>Block 4 Starboard (${b4List.length}):</strong> <span class="summary-mono">${b4List.join(', ') || 'None'}</span></div>
    <div><strong>Total Allocated Seats:</strong> <span class="summary-mono">${totalSeats} / ${preset.targetPax} Pax</span> (${chosenList.length} tables)</div>
    <div><strong>Status:</strong> Handed over to shipboard DRS server</div>
  `;
  bookingDialog.showModal();
});

document.getElementById('btn-copy-manifest').addEventListener('click', (e) => {
  const text = document.getElementById('dialog-summary-content').innerText;
  navigator.clipboard?.writeText(text);
  const btn = e.currentTarget;
  btn.textContent = 'Copied';
  setTimeout(() => {
    btn.textContent = 'Copy Manifest';
  }, 1600);
});

window.addEventListener('resize', () => {
  const w = window.innerWidth;
  const h = Math.max(1, window.innerHeight - 57);
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
// 10. MAIN RENDER & ANIMATION LOOP (PAUSES WHEN TAB IS HIDDEN)
// ============================================================================
let prevTime = performance.now();
let isPageHidden = document.hidden;

document.addEventListener('visibilitychange', () => {
  isPageHidden = document.hidden;
  if (!isPageHidden) {
    prevTime = performance.now();
  }
});

function animate(now) {
  requestAnimationFrame(animate);
  if (isPageHidden) return;

  const dt = Math.min(0.05, (now - prevTime) / 1000);
  prevTime = now;

  if (camAnim) {
    camAnim.update(now);
  }

  if (pointerDirty && !isOrbitDragging) {
    performHoverRaycast();
  }

  if (currentStage === 'ship') {
    const lerpRate = Math.min(1.0, dt * 7.0);
    let layersMoving = false;
    for (const key of ['L1', 'L2', 'L3', 'L4']) {
      const node = shipLayerNodes[key];
      if (node) {
        const diff = shipLayerTargetY[key] - node.position.y;
        if (Math.abs(diff) > 0.005) {
          node.position.y += diff * lerpRate;
          layersMoving = true;
        } else {
          node.position.y = shipLayerTargetY[key];
        }
      }
    }
    if (layersMoving) {
      requestShadowUpdate();
    }
    controls.update();
  } else if (currentStage === 'interior') {
    if (currentCamMode === 'walk') {
      const speed = 3.4 * dt;
      const forwardFlat = new THREE.Vector3(-Math.sin(walkYaw), 0, -Math.cos(walkYaw));
      const rightFlat = new THREE.Vector3(Math.cos(walkYaw), 0, -Math.sin(walkYaw));

      if (walkKeys.forward) perspCamera.position.addScaledVector(forwardFlat, speed);
      if (walkKeys.backward) perspCamera.position.addScaledVector(forwardFlat, -speed);
      if (walkKeys.right) perspCamera.position.addScaledVector(rightFlat, speed);
      if (walkKeys.left) perspCamera.position.addScaledVector(rightFlat, -speed);

      perspCamera.position.x = Math.max(-1.85, Math.min(27.6, perspCamera.position.x));
      perspCamera.position.z = Math.max(-17.0, Math.min(-0.55, perspCamera.position.z));
      perspCamera.position.y = 1.56;
      syncWalkCameraLook();
    } else {
      controls.update();
    }

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
        mat.color.setHex(0xb3402e);
        mat.emissive.setHex(0xb3402e);
        bMat.color.setHex(0xb3402e);
        targetOp = isHov ? 0.35 : 0.18;
        targetBorderOp = isHov ? 0.85 : 0.4;
      } else if (isSel) {
        mat.color.setHex(0x1f7a54);
        mat.emissive.setHex(0x1f7a54);
        bMat.color.setHex(0x1f7a54);
        targetOp = isHov ? 0.55 : 0.42;
        targetBorderOp = 0.95;
      } else if (isHov) {
        mat.color.setHex(0x0071a3);
        mat.emissive.setHex(0x0071a3);
        bMat.color.setHex(0x0071a3);
        targetOp = 0.45;
        targetBorderOp = 1.0;
      }

      if (Math.abs(targetOp - mat.opacity) > 0.002) {
        mat.opacity += (targetOp - mat.opacity) * 0.22;
      } else {
        mat.opacity = targetOp;
      }
      if (Math.abs(targetBorderOp - bMat.opacity) > 0.002) {
        bMat.opacity += (targetBorderOp - bMat.opacity) * 0.22;
      } else {
        bMat.opacity = targetBorderOp;
      }
    }
  }

  renderer.render(scene, activeCamera);
  labelRenderer.render(scene, activeCamera);
}

requestAnimationFrame(animate);
