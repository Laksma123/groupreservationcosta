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
// 1. DRS TABLE METADATA & ACCESS CODE PRESETS
// ============================================================================
const TABLE_CATALOG = [
  {
    num: '301',
    nodeKey: '301_Window_Booth',
    pax: 4,
    zone: 'Row A • Jendela Laut (Sofa Booth)',
    chairDesc: 'Sofa Banquette Merah + 2 Kursi Ivory',
  },
  {
    num: '303',
    nodeKey: '303_Window_Bay1',
    pax: 6,
    zone: 'Row A • Jendela Laut (Bay 1)',
    chairDesc: '6 Kursi Ivory Leatherette • Panorama Laut',
  },
  {
    num: '305',
    nodeKey: '305_Window_Bay2',
    pax: 6,
    zone: 'Row A • Jendela Laut (Bay 2)',
    chairDesc: '6 Kursi Ivory Leatherette • Panorama Laut',
  },
  {
    num: '307',
    nodeKey: '307_Window_Bay3',
    pax: 6,
    zone: 'Row A • Jendela Laut (Bay 3)',
    chairDesc: '6 Kursi Ivory Leatherette • Dekat Lukisan',
  },
  {
    num: '399',
    nodeKey: '399_Center_Fwd',
    pax: 6,
    zone: 'Row B • Baris Tengah (Dekat Station)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Baru',
  },
  {
    num: '397',
    nodeKey: '397_Center_Mid',
    pax: 6,
    zone: 'Row B • Baris Tengah (Sentral)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Baru',
  },
  {
    num: '393',
    nodeKey: '393_Center_Aft',
    pax: 6,
    zone: 'Row B • Baris Tengah (Dekat Pintu)',
    chairDesc: '6 Kursi Burgundy Velvet • Orientasi Baru',
  },
  {
    num: '403',
    nodeKey: '403_Railing_FwdBay',
    pax: 4,
    zone: 'Row C • Sisi Pagar X-Cross (Bay 1)',
    chairDesc: '4 Kursi Ivory Leatherette • Jalur Lega Station',
  },
  {
    num: '405',
    nodeKey: '405_Railing_MidBay',
    pax: 4,
    zone: 'Row C • Sisi Pagar X-Cross (Bay 2)',
    chairDesc: '4 Kursi Ivory Leatherette • Koridor Medali',
  },
  {
    num: '407',
    nodeKey: '407_Railing_AftBay',
    pax: 4,
    zone: 'Row C • Sisi Pagar X-Cross (Pintu Masuk)',
    chairDesc: '4 Kursi Ivory Leatherette • Dekat Pintu Masuk',
  },
];

const ACCESS_PRESETS = {
  A98XKJ90: {
    code: 'A98XKJ90',
    groupName: 'Milano Tech Incentive Group',
    targetPax: 28,
    lockedTables: ['301', '407'],
    recommended: ['303', '305', '399', '397', '403'],
  },
  DIAMOND16: {
    code: 'DIAMOND16',
    groupName: 'Costa Club Diamond Family',
    targetPax: 16,
    lockedTables: ['393', '405', '407'],
    recommended: ['301', '303', '399'],
  },
  FAM52ALL: {
    code: 'FAM52ALL',
    groupName: 'Full Starboard Block 1 Charter',
    targetPax: 52,
    lockedTables: [],
    recommended: ['301', '303', '305', '307', '399', '397', '393', '403', '405', '407'],
  },
};

// Walk Mode Viewpoint Presets (Three.js Y-up coordinates)
const WALK_SPOTS = {
  entrance: {
    pos: new THREE.Vector3(9.55, 1.62, -7.85),
    yaw: Math.PI * 0.26, // Looking from Bay 3 entrance into the dining room
    pitch: -0.06,
  },
  corridor: {
    pos: new THREE.Vector3(1.20, 1.62, -7.97),
    yaw: -Math.PI * 0.48, // Looking along the symmetrical medallion corridor
    pitch: -0.08,
  },
  center: {
    pos: new THREE.Vector3(7.60, 1.62, -4.85),
    yaw: Math.PI * 0.38, // Looking across maroon velvet chairs & ocean windows
    pitch: -0.05,
  },
  station: {
    pos: new THREE.Vector3(1.15, 1.62, -2.55),
    yaw: -Math.PI * 0.38, // Looking from Double Waiter Station & Sofa across Block 1
    pitch: -0.05,
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
scene.fog = new THREE.FogExp2(0x071426, 0.008);

// Perspective Camera (Used in Hero Ship, Bird's-Eye Mode, and Walk Mode)
const perspCamera = new THREE.PerspectiveCamera(44, window.innerWidth / window.innerHeight, 0.1, 400);

// Orthographic Camera (Used in Top-View 2D Mode with 3D Render)
const orthoFrustumH = 11.2;
const aspect = window.innerWidth / window.innerHeight;
const orthoCamera = new THREE.OrthographicCamera(
  (-orthoFrustumH * aspect) / 2,
  (orthoFrustumH * aspect) / 2,
  orthoFrustumH / 2,
  -orthoFrustumH / 2,
  0.1,
  100
);

let activeCamera = perspCamera;

const controls = new OrbitControls(perspCamera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxDistance = 120;
controls.minDistance = 1.2;

// Lighting for both Ship Exterior and Interior Restaurant
const ambientLight = new THREE.AmbientLight(0xfff6e8, 1.45);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0xdbeafe, 0x3b2314, 1.15);
hemiLight.position.set(0, 25, 0);
scene.add(hemiLight);

const sunLight = new THREE.DirectionalLight(0xfffbeb, 2.2);
sunLight.position.set(18, 28, 22);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
scene.add(sunLight);

// Warm interior fill lights positioned over Block 1 (X: 0..10, Y: 2.6, Z: -1..-7)
const interiorLightGroup = new THREE.Group();
scene.add(interiorLightGroup);
[
  [2.2, 2.55, -2.0, 0xffe4b5, 4.5],
  [6.0, 2.55, -2.0, 0xffe4b5, 4.5],
  [8.8, 2.55, -2.0, 0xffe4b5, 4.5],
  [2.5, 2.55, -5.2, 0xffd6a5, 4.0],
  [6.0, 2.55, -5.2, 0xffd6a5, 4.0],
  [8.8, 2.55, -5.2, 0xffd6a5, 4.0],
  [4.8, 2.55, -7.9, 0xfff0d4, 3.8],
].forEach(([lx, ly, lz, col, intensity]) => {
  const pt = new THREE.PointLight(col, intensity, 9.5, 1.4);
  pt.position.set(lx, ly, lz);
  interiorLightGroup.add(pt);
});
interiorLightGroup.visible = false;

// ============================================================================
// 3. STAGE 1: 3D HERO CRUISE SHIP (COSTA SMERALDA CUTAWAY MODEL)
// ============================================================================
const shipStageGroup = new THREE.Group();
const shipUpperDecksGroup = new THREE.Group(); // Lifts up during cutaway zoom-in!
scene.add(shipStageGroup);

let deck6CutawayMesh = null;
let shipHotspotLabel = null;
let oceanMesh = null;

function buildHeroCruiseShip() {
  // 1. Mediterranean Sea Surface
  const seaGeo = new THREE.PlaneGeometry(260, 260, 64, 64);
  seaGeo.rotateX(-Math.PI / 2);
  const seaMat = new THREE.MeshStandardMaterial({
    color: 0x0a4b78,
    roughness: 0.22,
    metalness: 0.35,
  });
  oceanMesh = new THREE.Mesh(seaGeo, seaMat);
  oceanMesh.position.y = -2.2;
  shipStageGroup.add(oceanMesh);

  // Helper to create elongated ship hull/deck profiles along X axis
  function makeShipDeckLayer(length, width, height, yPos, colorHex, emissiveHex = 0x000000, emissiveInt = 0) {
    const shape = new THREE.Shape();
    const hw = width / 2;
    const hl = length / 2;
    const bowLen = length * 0.24;
    const sternLen = length * 0.08;

    shape.moveTo(-hl + sternLen, -hw);
    shape.lineTo(hl - bowLen, -hw);
    shape.quadraticCurveTo(hl, -hw * 0.35, hl, 0);
    shape.quadraticCurveTo(hl, hw * 0.35, hl - bowLen, hw);
    shape.lineTo(-hl + sternLen, hw);
    shape.quadraticCurveTo(-hl, hw * 0.85, -hl, 0);
    shape.quadraticCurveTo(-hl, -hw * 0.85, -hl + sternLen, -hw);

    const extrude = new THREE.ExtrudeGeometry(shape, {
      depth: height,
      bevelEnabled: true,
      bevelThickness: 0.08,
      bevelSize: 0.08,
      bevelSegments: 2,
    });
    extrude.rotateX(-Math.PI / 2);
    const mat = new THREE.MeshStandardMaterial({
      color: colorHex,
      roughness: 0.3,
      metalness: 0.15,
      emissive: emissiveHex,
      emissiveIntensity: emissiveInt,
      transparent: true,
      opacity: 1.0,
    });
    const mesh = new THREE.Mesh(extrude, mat);
    mesh.position.y = yPos;
    return mesh;
  }

  // Lower Dark Navy Hull (Decks 1-3)
  shipStageGroup.add(makeShipDeckLayer(44, 6.8, 2.2, -2.2, 0x0a1931));
  // Gold Costa Ribbon Line
  shipStageGroup.add(makeShipDeckLayer(44.4, 6.88, 0.18, -0.05, 0xf5c443, 0xf5c443, 0.25));
  // Lower White Hull (Decks 4-5)
  shipStageGroup.add(makeShipDeckLayer(45.2, 7.0, 1.3, 0.1, 0xf8fafc));

  // DECK 6 (ROMA) BASE LAYER — Where Ristorante Arlecchino lives!
  const deck6Base = makeShipDeckLayer(45.6, 7.1, 0.95, 1.4, 0xe2e8f0);
  shipStageGroup.add(deck6Base);

  // Interactive Glowing Cutaway Bay on Deck 6 Mid-Ship Starboard (+Z side of ship)
  const cutawayGeo = new THREE.BoxGeometry(10.5, 1.02, 2.4);
  const cutawayMat = new THREE.MeshPhysicalMaterial({
    color: 0xf5c443,
    emissive: 0xf59e0b,
    emissiveIntensity: 0.55,
    roughness: 0.15,
    transmission: 0.45,
    transparent: true,
    opacity: 0.92,
  });
  deck6CutawayMesh = new THREE.Mesh(cutawayGeo, cutawayMat);
  deck6CutawayMesh.position.set(1.5, 1.92, 2.65);
  deck6CutawayMesh.name = 'Deck6_Arlecchino_Cutaway_Zone';
  shipStageGroup.add(deck6CutawayMesh);

  // Glowing wireframe border around Deck 6 Cutaway Zone
  const cutEdges = new THREE.LineSegments(
    new THREE.EdgesGeometry(cutawayGeo),
    new THREE.LineBasicMaterial({ color: 0xffffff })
  );
  deck6CutawayMesh.add(cutEdges);

  // CSS2D Hotspot Button anchored directly to Deck 6 Starboard on the 3D Ship
  const hsDiv = document.createElement('button');
  hsDiv.type = 'button';
  hsDiv.className = 'ship-hotspot-marker';
  hsDiv.innerHTML = '<span>📍 DECK 6 • RISTORANTE ARLECCHINO (KLIK ZOOM-IN)</span>';
  hsDiv.addEventListener('click', (e) => {
    e.stopPropagation();
    enterInteriorBlock1();
  });
  shipHotspotLabel = new CSS2DObject(hsDiv);
  shipHotspotLabel.position.set(0, 1.35, 0);
  deck6CutawayMesh.add(shipHotspotLabel);

  // Upper Passenger Balcony Decks (Decks 7 to 17) — Placed in shipUpperDecksGroup for Cutaway lift!
  for (let d = 0; d < 7; d++) {
    const y = 2.4 + d * 0.72;
    const len = 43.5 - d * 1.4;
    const wid = 6.7 - d * 0.12;
    const deckSlab = makeShipDeckLayer(len, wid, 0.46, y, 0xffffff);
    const glassStrip = makeShipDeckLayer(len - 0.5, wid + 0.06, 0.24, y + 0.46, 0x38bdf8, 0x0284c7, 0.35);
    shipUpperDecksGroup.add(deckSlab, glassStrip);
  }

  // Iconic Costa Yellow Funnel with Blue 'C' Crest at Mid-Aft
  const funnelGeo = new THREE.CylinderGeometry(1.15, 1.55, 4.2, 24);
  funnelGeo.scale(1.6, 1.0, 0.85);
  const funnelMat = new THREE.MeshStandardMaterial({
    color: 0xf5c443,
    roughness: 0.25,
    metalness: 0.1,
    transparent: true,
    opacity: 1.0,
  });
  const funnelMesh = new THREE.Mesh(funnelGeo, funnelMat);
  funnelMesh.position.set(-5.5, 9.2, 0);
  funnelMesh.rotation.z = 0.18;
  shipUpperDecksGroup.add(funnelMesh);

  // Dark Navy Funnel Cap
  const capGeo = new THREE.CylinderGeometry(1.12, 1.16, 0.55, 24);
  capGeo.scale(1.6, 1.0, 0.85);
  const capMesh = new THREE.Mesh(
    capGeo,
    new THREE.MeshStandardMaterial({ color: 0x0a1931, transparent: true, opacity: 1.0 })
  );
  capMesh.position.set(-5.85, 11.2, 0);
  capMesh.rotation.z = 0.18;
  shipUpperDecksGroup.add(capMesh);

  shipStageGroup.add(shipUpperDecksGroup);
}

buildHeroCruiseShip();

// ============================================================================
// 4. STAGE 2: LOAD BLENDER GLB & BUILD INTERACTIVE TABLE OVERLAYS
// ============================================================================
const restaurantGroup = new THREE.Group();
restaurantGroup.visible = false;
scene.add(restaurantGroup);

const ceilingMeshes = [];
const tableRegistry = new Map(); // num -> { meta, meshes, topMesh, glassPad, glassBorder, labelObj, boxCenter, boxSize }
const interactiveMeshes = []; // All meshes that trigger table hover/click

const loaderOverlay = document.getElementById('loading-overlay');
const gltfLoader = new GLTFLoader();

gltfLoader.load(
  './arlecchino_block1.glb',
  (gltf) => {
    const model = gltf.scene;
    restaurantGroup.add(model);

    // 1. Classify meshes inside the loaded Blender .glb
    model.traverse((child) => {
      if (!child.isMesh) return;
      child.castShadow = true;
      child.receiveShadow = true;

      const n = child.name || '';
      // Ceiling & overhead lighting objects (hidden in Bird's-Eye & Top-2D modes; shown in Walk mode)
      if (
        n.startsWith('Ceiling_') ||
        n.startsWith('CeilBeam_') ||
        n.startsWith('RedSpot_') ||
        n.startsWith('Corr_Downlight_')
      ) {
        ceilingMeshes.push(child);
      }

      // Associate table & chair meshes with their DRS table number
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

    // 2. Build 3D Glassmorphism Pre-Selection Pads & Floating Typography Labels for each of the 10 tables
    model.updateMatrixWorld(true);

    for (const meta of TABLE_CATALOG) {
      const entry = tableRegistry.get(meta.num);
      if (!entry || !entry.topMesh) continue;

      const box = new THREE.Box3().setFromObject(entry.topMesh);
      box.getCenter(entry.center);
      box.getSize(entry.size);

      // Glassmorphic Pad hovering 10mm above the clean Carrara marble tabletop
      const padW = Math.max(entry.size.x - 0.03, 0.5);
      const padD = Math.max(entry.size.z - 0.03, 0.5);
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

    // Apply initial preset & hide loading screen
    applyAccessPreset(currentPresetKey);
    loaderOverlay.classList.add('is-hidden');
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
  shipUpperDecksGroup.position.y = 0;
  if (shipHotspotLabel) shipHotspotLabel.element.style.display = 'flex';

  restaurantGroup.visible = false;
  interiorLightGroup.visible = false;
  updateTableMarkersVisibility();

  document.getElementById('hero-ship-ui').hidden = false;
  document.getElementById('interior-ui').hidden = true;
  document.getElementById('btn-back-ship').hidden = true;
  document.getElementById('stage-title').textContent =
    'Kapal Utuh Costa Smeralda — Pilih Deck Restoran';

  const shipCamPos = new THREE.Vector3(24, 14, 34);
  const shipTarget = new THREE.Vector3(0, 2.5, 0);
  if (instant) {
    perspCamera.position.copy(shipCamPos);
    controls.target.copy(shipTarget);
    controls.update();
  } else {
    animateCameraTo(shipCamPos, shipTarget, 900);
  }
}

setHeroShipCamera(true);

// Trigger Cutaway Animation on Hero Ship -> Zoom-In to Deck 6 Block 1
function enterInteriorBlock1() {
  if (currentStage === 'interior') return;
  if (shipHotspotLabel) shipHotspotLabel.element.style.display = 'none';

  // Animate upper ship decks lifting up while camera zooms into Deck 6 Starboard cutaway
  const startLift = performance.now();
  const liftDur = 750;

  function stepCutaway(now) {
    const t = Math.min(1, (now - startLift) / liftDur);
    const ease = 1 - Math.pow(1 - t, 3);
    shipUpperDecksGroup.position.y = ease * 9.5;
    if (t < 1) {
      requestAnimationFrame(stepCutaway);
    }
  }
  requestAnimationFrame(stepCutaway);

  animateCameraTo(
    new THREE.Vector3(4.5, 3.2, 6.2),
    new THREE.Vector3(1.5, 1.9, 2.6),
    750,
    () => {
      // Switch to Stage 2: Interior Ristorante Arlecchino Block 1
      currentStage = 'interior';
      shipStageGroup.visible = false;
      restaurantGroup.visible = true;
      interiorLightGroup.visible = true;

      document.getElementById('hero-ship-ui').hidden = true;
      document.getElementById('interior-ui').hidden = false;
      document.getElementById('btn-back-ship').hidden = false;
      document.getElementById('stage-title').textContent =
        'Deck 6 "Roma" • Ristorante Arlecchino (Starboard Block 1)';

      setInteriorCameraMode('bird');
      updateTableMarkersVisibility();
    }
  );
}

// Toggle Ceiling / Roof visibility (Hidden in Bird's-Eye & Top-2D, Visible in Walk Mode)
function setCeilingVisible(vis) {
  for (const m of ceilingMeshes) {
    m.visible = vis;
  }
}

function updateTableMarkersVisibility() {
  const shouldShow = currentStage === 'interior' && showTableNumbers;
  for (const [, entry] of tableRegistry) {
    if (!entry.labelEl) continue;
    entry.labelEl.classList.toggle('is-hidden', !shouldShow);
  }
}

// ============================================================================
// 6. THREE INTERIOR CAMERA MODES: BIRD'S-EYE, TOP-VIEW 2D, WALK MODE
// ============================================================================
let walkYaw = WALK_SPOTS.entrance.yaw;
let walkPitch = WALK_SPOTS.entrance.pitch;
const walkKeys = { forward: false, backward: false, left: false, right: false };
let isDraggingLook = false;
let prevPointer = { x: 0, y: 0 };

function setInteriorCameraMode(mode) {
  currentCamMode = mode;

  // Update active button UI
  document.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.camMode === mode);
  });

  const walkHud = document.getElementById('walk-hud');
  walkHud.hidden = mode !== 'walk';

  if (mode === 'bird') {
    // 1. BIRD'S-EYE MODE (Roof Hidden + 3D Perspective Orbit)
    setCeilingVisible(false);
    activeCamera = perspCamera;
    perspCamera.fov = 42;
    perspCamera.updateProjectionMatrix();

    controls.object = perspCamera;
    controls.enabled = true;
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.maxPolarAngle = Math.PI * 0.47;

    const zSign = top2dFlipped ? 1 : -1;
    const targetPos = top2dFlipped
      ? new THREE.Vector3(4.75, 10.5, 6.2)
      : new THREE.Vector3(11.8, 9.6, -12.4);
    const lookTarget = new THREE.Vector3(4.75, 0.65, -4.35);
    animateCameraTo(targetPos, lookTarget, 750);
  } else if (mode === 'top2d') {
    // 2. TOP-VIEW 2D MODE (Orthographic 90° Overhead with identical 3D Render & Roof Hidden)
    setCeilingVisible(false);
    camAnim = null;
    activeCamera = orthoCamera;

    const centerX = 4.65;
    const centerZ = -4.45;
    orthoCamera.position.set(centerX, 16.0, centerZ);
    orthoCamera.up.set(0, 0, top2dFlipped ? -1 : 1);
    orthoCamera.lookAt(centerX, 0.0, centerZ);
    orthoCamera.zoom = 1.05;
    orthoCamera.updateProjectionMatrix();

    controls.object = orthoCamera;
    controls.target.set(centerX, 0.0, centerZ);
    controls.enabled = true;
    controls.enableRotate = false; // Locked strictly to 2D top-down plane
    controls.enablePan = true;
    controls.update();
  } else if (mode === 'walk') {
    // 3. WALK MODE (First-Person Eye-Level 1.62m + Ceiling Restored!)
    setCeilingVisible(true);
    camAnim = null;
    activeCamera = perspCamera;
    perspCamera.fov = 62;
    perspCamera.up.set(0, 1, 0);
    perspCamera.updateProjectionMatrix();

    controls.enabled = false;
    teleportWalkTo('entrance');
  }
}

function teleportWalkTo(spotKey) {
  const spot = WALK_SPOTS[spotKey] || WALK_SPOTS.entrance;
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
// 7. GLASSMORPHISM PRE-SELECTION HOVER & TABLE SELECTION LOGIC
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
  const preset = ACCESS_PRESETS[currentPresetKey];
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

  // Update Sidebar Pax Metrics
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

  // Rebuild Sidebar Table List
  const listEl = document.getElementById('sidebar-table-list');
  listEl.innerHTML = '';
  for (const meta of TABLE_CATALOG) {
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
// 8. RAYCASTING (3D HOVER & CLICK FOR BOTH SHIP & INTERIOR TABLES)
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

  if (currentStage === 'ship' && deck6CutawayMesh) {
    const hits = raycaster.intersectObject(deck6CutawayMesh, false);
    const hitDeck6 = hits.length > 0;
    canvas.style.cursor = hitDeck6 ? 'pointer' : 'grab';
    deck6CutawayMesh.material.emissiveIntensity = hitDeck6 ? 0.95 : 0.55;
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

  if (currentStage === 'ship' && deck6CutawayMesh) {
    const hits = raycaster.intersectObject(deck6CutawayMesh, false);
    if (hits.length > 0) {
      enterInteriorBlock1();
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
// 9. UI EVENT LISTENERS (BUTTONS, SWITCH, KEYBOARD WALK, DIALOG)
// ============================================================================
document.getElementById('btn-enter-deck6').addEventListener('click', enterInteriorBlock1);
document.getElementById('btn-back-ship').addEventListener('click', () => setHeroShipCamera(false));

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
  const preset = ACCESS_PRESETS[currentPresetKey];
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

// Confirm Booking Modal Dialog (Opened with showModal() per modern-web-guidance)
document.getElementById('btn-confirm-booking').addEventListener('click', () => {
  const preset = ACCESS_PRESETS[currentPresetKey];
  const chosenList = TABLE_CATALOG.filter((t) => selectedTables.has(t.num));
  const totalSeats = chosenList.reduce((acc, t) => acc + t.pax, 0);
  const tableNumsStr = chosenList.map((t) => `#${t.num} (${t.pax}P)`).join(', ');

  document.getElementById('dialog-summary-content').innerHTML = `
    <div><strong>Kode Akses DRS:</strong> ${preset.code} — ${preset.groupName}</div>
    <div><strong>Restoran &amp; Lokasi:</strong> Ristorante Arlecchino • Deck 6 (Roma) Starboard Block 1</div>
    <div><strong>Daftar Meja Terpilih (${chosenList.length} Meja):</strong> ${tableNumsStr}</div>
    <div><strong>Total Kapasitas Kursi:</strong> ${totalSeats} Kursi (Target Grup: ${preset.targetPax} Pax)</div>
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

  // 2. Stage 1: Subtle ship & ocean animation
  if (currentStage === 'ship') {
    shipStageGroup.position.y = Math.sin(now * 0.0015) * 0.12;
    controls.update();
  }

  // 3. Stage 2: Interior Walk Mode movement or OrbitControls update
  if (currentStage === 'interior') {
    if (currentCamMode === 'walk') {
      const speed = 3.2 * dt;
      const forwardFlat = new THREE.Vector3(-Math.sin(walkYaw), 0, -Math.cos(walkYaw));
      const rightFlat = new THREE.Vector3(Math.cos(walkYaw), 0, -Math.sin(walkYaw));

      if (walkKeys.forward) perspCamera.position.addScaledVector(forwardFlat, speed);
      if (walkKeys.backward) perspCamera.position.addScaledVector(forwardFlat, -speed);
      if (walkKeys.right) perspCamera.position.addScaledVector(rightFlat, speed);
      if (walkKeys.left) perspCamera.position.addScaledVector(rightFlat, -speed);

      // Keep walk camera inside Block 1 & Corridor bounds
      perspCamera.position.x = Math.max(-1.2, Math.min(10.1, perspCamera.position.x));
      perspCamera.position.z = Math.max(-8.55, Math.min(-0.55, perspCamera.position.z));
      perspCamera.position.y = 1.62;
      syncWalkCameraLook();
    } else {
      controls.update();
    }

    // 4. Smoothly animate Glassmorphism Pre-Selection & Selection Pads on the 10 tables
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
        // Pre-Selection Glassmorphism Glow!
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
