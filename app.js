import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

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

// Modern Web Guidance: validate-input-after-interaction fallback & ARIA sync
const UserInvalidFallback = (() => {
  const dirtyState = new WeakMap();
  const updateState = (input) => {
    const isValid = input.checkValidity();
    input.classList.toggle('user-invalid-fallback', !isValid);
    input.classList.toggle('user-valid-fallback', isValid);
    if (!isValid) {
      input.setAttribute('aria-invalid', 'true');
    } else {
      input.removeAttribute('aria-invalid');
    }
  };
  const handleEvent = (event) => {
    const input = event.target;
    if (!input || !input.checkValidity) return;
    if (event.type === 'input' || event.type === 'change') {
      const state = dirtyState.get(input) || { hasInteracted: false, hasBlurred: false };
      state.hasInteracted = true;
      dirtyState.set(input, state);
      if (state.hasBlurred) updateState(input);
    } else if (event.type === 'blur') {
      const state = dirtyState.get(input) || { hasInteracted: false, hasBlurred: false };
      state.hasBlurred = true;
      dirtyState.set(input, state);
      if (state.hasInteracted) updateState(input);
    }
  };
  const init = (root = document) => {
    if (!CSS.supports('selector(:user-invalid)')) {
      root.addEventListener('blur', handleEvent, true);
      root.addEventListener('input', handleEvent);
      root.addEventListener('change', handleEvent);
    }
    const syncAria = (el) => {
      if (el && el.matches && el.setAttribute) {
        try {
          el.setAttribute('aria-invalid', el.matches(':user-invalid') ? 'true' : 'false');
        } catch (_) {}
      }
    };
    root.addEventListener('blur', (e) => syncAria(e.target), true);
    root.addEventListener('input', (e) => {
      if (e.target && e.target.hasAttribute && e.target.hasAttribute('aria-invalid')) {
        syncAria(e.target);
      }
    });
  };
  return { init };
})();

UserInvalidFallback.init(document);

// ============================================================================
// 1. DRS 4-BLOCK TABLE CATALOG (45 TABLES / 220 SEATS — ALL 45 NODE KEYS EXACT)
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

  // --- BLOCK 3: PORTSIDE AFT (9 TABLES · 54 SEATS — FIXED BAY NODE KEYS) ---
  {
    num: '309',
    block: 'B3',
    nodeKey: '309_B3_Window_Bay1',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (Bay 1)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '311',
    block: 'B3',
    nodeKey: '311_B3_Window_Bay2',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (Bay 2)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '313',
    block: 'B3',
    nodeKey: '313_B3_Window_Bay3',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (Bay 3)',
    chairDesc: '6 Ivory Leatherette Chairs · Sea View',
  },
  {
    num: '315',
    block: 'B3',
    nodeKey: '315_B3_Window_Bay4',
    pax: 6,
    zone: 'Block 3 Port · Ocean Window (Bay 4)',
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
    nodeKey: '409_B3_Railing_FwdBay',
    pax: 4,
    zone: 'Block 3 Port · Railing Row (Entrance 1)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '411',
    block: 'B3',
    nodeKey: '411_B3_Railing_MidBay',
    pax: 4,
    zone: 'Block 3 Port · Railing Row (Mid Bay)',
    chairDesc: '4 Ivory Leatherette Chairs · Centered on Pillar',
  },
  {
    num: '413',
    block: 'B3',
    nodeKey: '413_B3_Railing_AftBay',
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

  // --- BLOCK 5: GREEN ZONE AFT (32 TABLES · 116 SEATS) ---
  {
    num: '319',
    block: 'B5',
    nodeKey: '319_B5_SofaPort_2Pax',
    pax: 2,
    zone: 'Block 5 Port · Forward Sofa Row (2P)',
    chairDesc: 'Sage Banquette Sofa + 1 Teal/Ivory Chair',
  },
  {
    num: '317',
    block: 'B5',
    nodeKey: '317_B5_SofaPort_4Pax',
    pax: 4,
    zone: 'Block 5 Port · Forward Sofa Row (4P)',
    chairDesc: 'Sage Banquette Sofa + 2 Teal/Ivory Chairs',
  },
  {
    num: '385',
    block: 'B5',
    nodeKey: '385_B5_SofaPort_2Pax',
    pax: 2,
    zone: 'Block 5 Port · Forward Sofa Niche (2P)',
    chairDesc: 'Sage Banquette Sofa + 1 Teal/Ivory Chair',
  },
  {
    num: '387',
    block: 'B5',
    nodeKey: '387_B5_SofaPort_4Pax',
    pax: 4,
    zone: 'Block 5 Port · Forward Sofa Niche (4P)',
    chairDesc: 'Sage Banquette Sofa + 2 Teal/Ivory Chairs',
  },
  {
    num: '415',
    block: 'B5',
    nodeKey: '415_B5_SofaPort_2Pax',
    pax: 2,
    zone: 'Block 5 Port · Forward Sofa Corridor (2P)',
    chairDesc: 'Sage Banquette Sofa + 1 Teal/Ivory Chair',
  },
  {
    num: '480',
    block: 'B5',
    nodeKey: '480_B5_SofaStbd_2Pax',
    pax: 2,
    zone: 'Block 5 Stbd · Forward Sofa Corridor (2P)',
    chairDesc: 'Sage Banquette Sofa + 1 Teal/Ivory Chair',
  },
  {
    num: '450',
    block: 'B5',
    nodeKey: '450_B5_SofaStbd_4Pax',
    pax: 4,
    zone: 'Block 5 Stbd · Forward Sofa Niche (4P)',
    chairDesc: 'Sage Banquette Sofa + 2 Teal/Ivory Chairs',
  },
  {
    num: '448',
    block: 'B5',
    nodeKey: '448_B5_SofaStbd_2Pax',
    pax: 2,
    zone: 'Block 5 Stbd · Forward Sofa Niche (2P)',
    chairDesc: 'Sage Banquette Sofa + 1 Teal/Ivory Chair',
  },
  {
    num: '400',
    block: 'B5',
    nodeKey: '400_B5_SofaStbd_4Pax',
    pax: 4,
    zone: 'Block 5 Stbd · Forward Sofa Row (4P)',
    chairDesc: 'Sage Banquette Sofa + 2 Teal/Ivory Chairs',
  },
  {
    num: '398',
    block: 'B5',
    nodeKey: '398_B5_SofaStbd_2Pax',
    pax: 2,
    zone: 'Block 5 Stbd · Forward Sofa Row (2P)',
    chairDesc: 'Sage Banquette Sofa + 1 Teal/Ivory Chair',
  },
  {
    num: '321',
    block: 'B5',
    nodeKey: '321_B5_WinPort_4Pax',
    pax: 4,
    zone: 'Block 5 Port · Ocean Window Pair 1 (4P)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs · Sea View',
  },
  {
    num: '323',
    block: 'B5',
    nodeKey: '323_B5_WinPort_2Pax',
    pax: 2,
    zone: 'Block 5 Port · Ocean Window Pair 1 (2P)',
    chairDesc: '2 Teal & Ivory Curved Tub Chairs · Sea View',
  },
  {
    num: '327',
    block: 'B5',
    nodeKey: '327_B5_WinPort_4Pax',
    pax: 4,
    zone: 'Block 5 Port · Ocean Window Pair 2 (4P)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs · Sea View',
  },
  {
    num: '325',
    block: 'B5',
    nodeKey: '325_B5_WinPort_2Pax',
    pax: 2,
    zone: 'Block 5 Port · Ocean Window Pair 2 (2P)',
    chairDesc: '2 Teal & Ivory Curved Tub Chairs · Sea View',
  },
  {
    num: '329',
    block: 'B5',
    nodeKey: '329_B5_WinPort_4Pax',
    pax: 4,
    zone: 'Block 5 Port · Ocean Window Pair 3 (4P)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs · Sea View',
  },
  {
    num: '331',
    block: 'B5',
    nodeKey: '331_B5_WinPort_2Pax',
    pax: 2,
    zone: 'Block 5 Port · Ocean Window Pair 3 (2P)',
    chairDesc: '2 Teal & Ivory Curved Tub Chairs · Sea View',
  },
  {
    num: '404',
    block: 'B5',
    nodeKey: '404_B5_WallStbd_4Pax',
    pax: 4,
    zone: 'Block 5 Stbd · Wall Pair 1 (+1m Aft · 4P)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '402',
    block: 'B5',
    nodeKey: '402_B5_WallStbd_2Pax',
    pax: 2,
    zone: 'Block 5 Stbd · Wall Pair 1 (+1m Aft · 2P)',
    chairDesc: '2 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '406',
    block: 'B5',
    nodeKey: '406_B5_WallStbd_4Pax',
    pax: 4,
    zone: 'Block 5 Stbd · Wall Pair 2 (4P)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '408',
    block: 'B5',
    nodeKey: '408_B5_WallStbd_2Pax',
    pax: 2,
    zone: 'Block 5 Stbd · Wall Pair 2 (2P)',
    chairDesc: '2 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '412',
    block: 'B5',
    nodeKey: '412_B5_WallStbd_4Pax',
    pax: 4,
    zone: 'Block 5 Stbd · Wall Pair 3 (4P)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '410',
    block: 'B5',
    nodeKey: '410_B5_WallStbd_2Pax',
    pax: 2,
    zone: 'Block 5 Stbd · Wall Pair 3 (2P)',
    chairDesc: '2 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '383',
    block: 'B5',
    nodeKey: '383_B5_CenterFwd_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Forward Row (Port)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '417',
    block: 'B5',
    nodeKey: '417_B5_CenterFwd_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Forward Row (Mid-Port)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '482',
    block: 'B5',
    nodeKey: '482_B5_CenterFwd_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Forward Row (Mid-Stbd)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '446',
    block: 'B5',
    nodeKey: '446_B5_CenterFwd_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Forward Row (Stbd)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '381',
    block: 'B5',
    nodeKey: '381_B5_CenterSide_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Port Side (Aligned w/ 419)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '379',
    block: 'B5',
    nodeKey: '379_B5_CenterSide_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Port Side Aft',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '444',
    block: 'B5',
    nodeKey: '444_B5_CenterSide_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Stbd Side (Aligned w/ 484)',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '442',
    block: 'B5',
    nodeKey: '442_B5_CenterSide_4Pax',
    pax: 4,
    zone: 'Block 5 Green Carpet · Stbd Side Aft',
    chairDesc: '4 Teal & Ivory Curved Tub Chairs',
  },
  {
    num: '419',
    block: 'B5',
    nodeKey: '419_B5_CenterWood_10Pax',
    pax: 10,
    zone: 'Block 5 Green Carpet · Grand Oak Table (Port)',
    chairDesc: '10 Light Oak Armchairs · 3 Murano Chandeliers',
  },
  {
    num: '484',
    block: 'B5',
    nodeKey: '484_B5_CenterWood_10Pax',
    pax: 10,
    zone: 'Block 5 Green Carpet · Grand Oak Table (Stbd)',
    chairDesc: '10 Light Oak Armchairs · 3 Murano Chandeliers',
  },
];

const TABLE_IDS = TABLE_CATALOG.map((t) => t.num);
const CODEC_TABLE_IDS = TABLE_IDS.slice(0, 45);

const ACCESS_PRESETS = {
  A98XKJ90: {
    code: 'A98XKJ90',
    groupName: 'Milano Corporate Incentive',
    targetPax: 44,
    lockedTables: ['301', '407', '374', '376', '409', '474'],
    recommended: ['399', '397', '403', '405', '468', '470', '462', '460'],
    expiryLabel: 'Corporate Preset · Active',
    isExpired: false,
  },
  DIAMOND28: {
    code: 'DIAMOND28',
    groupName: 'Costa Club Diamond Family',
    targetPax: 28,
    lockedTables: ['393', '407', '472', '458'],
    recommended: ['466', '464', '462', '460', '384', '380'],
    expiryLabel: 'Diamond Preset · Active',
    isExpired: false,
  },
  CHARTER112: {
    code: 'CHARTER112',
    groupName: 'Full Arlecchino Charter',
    targetPax: 220,
    lockedTables: [],
    recommended: TABLE_CATALOG.map((t) => t.num),
    expiryLabel: 'Charter Preset · Active',
    isExpired: false,
  },
};

// ============================================================================
// 1B. SELF-CONTAINED STATELESS DRS TOKEN CODEC (SHARED WITH BOOKMARKLET)
// ============================================================================
const DRS_CODEC = (() => {
  const SLOT_MS = 30 * 60 * 1000;
  const SLOT_MOD = 1024;
  const TTL_SLOTS = [1, 4, 12, 24, 48, 96, 144, 336];
  const TTL_NAMES = ['30m', '2h', '6h', '12h', '24h', '48h', '72h', '7d'];
  const LABEL_ALPHABET = '_ ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-&./';
  const MASK33 = (1n << 33n) - 1n;
  const MASK66 = (1n << 66n) - 1n;

  function feistelF33(half33, roundKey) {
    let h = (half33 ^ roundKey) & MASK33;
    h = ((h * 0x15A4E357n) ^ (h >> 13n)) & MASK33;
    h = ((h * 0x0D93B713n) ^ (h >> 17n)) & MASK33;
    return h & MASK33;
  }

  function scramble66(raw66) {
    let l = raw66 & MASK33;
    let r = (raw66 >> 33n) & MASK33;
    let r1 = l ^ feistelF33(r, 0x0C057A11n);
    let l1 = r;
    let r2 = l1 ^ feistelF33(r1, 0x15E4A1D9n);
    let l2 = r1;
    let r3 = l2 ^ feistelF33(r2, 0x0A98BA07n);
    let l3 = r2;
    return ((r3 << 33n) | l3) & MASK66;
  }

  function unscramble66(scr66) {
    let l3 = scr66 & MASK33;
    let r3 = (scr66 >> 33n) & MASK33;
    let r2 = l3;
    let l2 = r3 ^ feistelF33(r2, 0x0A98BA07n);
    let r1 = l2;
    let l1 = r2 ^ feistelF33(r1, 0x15E4A1D9n);
    let r0 = l1;
    let l0 = r1 ^ feistelF33(r0, 0x0C057A11n);
    return ((r0 << 33n) | l0) & MASK66;
  }

  function computeChecksum4(header66, labelInt) {
    let x = header66 ^ (labelInt * 0x9E3779B97F4A7C15n) ^ 0x2C057A5E4A1DA9n;
    x ^= x >> 33n;
    x = (x * 0x1A85EC539n) ^ (x >> 19n);
    x ^= x >> 9n;
    x ^= x >> 4n;
    return (x & 0xFn) ^ 0xAn;
  }

  function obfuscateLabelInt(labelInt, scrambledHeader66, chk4) {
    if (labelInt <= 1n) return labelInt;
    const bLen = BigInt(labelInt.toString(2).length);
    const lowBits = bLen - 1n;
    if (lowBits <= 0n) return labelInt;
    let mask = 0n;
    let seed = (scrambledHeader66 ^ (chk4 << 51n) ^ 0x5A3C96E1F4B2n) & MASK66;
    while (mask.toString(2).length < Number(lowBits) + 16) {
      seed = ((seed * 0x2545F4914F6CDD1Dn) ^ (seed >> 17n) ^ 0x1337C057An) & MASK66;
      mask = (mask << 32n) | (seed & 0xFFFFFFFFn);
    }
    const lowMask = mask & ((1n << lowBits) - 1n);
    return labelInt ^ lowMask;
  }

  function normalizeLabel(str) {
    const cleaned = String(str || '')
      .toUpperCase()
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 18);
    let out = '';
    for (let i = 0; i < cleaned.length; i++) {
      const ch = cleaned[i];
      out += LABEL_ALPHABET.indexOf(ch) > 0 ? ch : '-';
    }
    return out;
  }

  function encodeLabelToInt(str) {
    const norm = normalizeLabel(str);
    let val = 0n;
    for (let i = norm.length - 1; i >= 0; i--) {
      const idx = LABEL_ALPHABET.indexOf(norm[i]);
      if (idx > 0) {
        val = val * 42n + BigInt(idx);
      }
    }
    return val;
  }

  function decodeIntToLabel(val) {
    if (val === 0n) return 'VIP Group Guest';
    const chars = [];
    let temp = val;
    let safety = 0;
    while (temp > 0n && safety < 24) {
      const rem = Number(temp % 42n);
      if (rem <= 0 || rem >= LABEL_ALPHABET.length) return null;
      chars.push(LABEL_ALPHABET[rem]);
      temp = temp / 42n;
      safety++;
    }
    if (temp > 0n) return null;
    return chars.join('');
  }

  function buildRecommendedTables(lockedSet, targetPax) {
    const openTables = TABLE_CATALOG.filter((t) => !lockedSet.has(t.num));
    const chosen = [];
    let accPax = 0;
    for (const t of openTables) {
      if (accPax >= targetPax) break;
      chosen.push(t.num);
      accPax += t.pax;
    }
    return chosen;
  }

  function formatDurationRemaining(remainingMs) {
    if (remainingMs <= 0) return 'Expired';
    const totalMins = Math.ceil(remainingMs / 60000);
    if (totalMins < 60) return `${totalMins}m left`;
    const hrs = Math.floor(totalMins / 60);
    const mins = totalMins % 60;
    if (hrs < 48) return mins > 0 ? `${hrs}h ${mins}m left` : `${hrs}h left`;
    const days = Math.floor(hrs / 24);
    const remHrs = hrs % 24;
    return `${days}d ${remHrs}h left`;
  }

  function encodeToken({ lockedTables = [], targetPax = 44, groupName = 'VIP GROUP', ttlIdx = 4, nowMs = Date.now() }) {
    const lockedSet = new Set(lockedTables.map(String));
    let mask45 = 0n;
    for (let i = 0; i < CODEC_TABLE_IDS.length; i++) {
      if (lockedSet.has(CODEC_TABLE_IDS[i])) {
        mask45 |= 1n << BigInt(i);
      }
    }
    const clampedPax = Math.max(1, Math.min(220, Math.round(Number(targetPax) || 44)));
    const issuedSlot = Math.floor(nowMs / SLOT_MS) & (SLOT_MOD - 1);
    const validTtlIdx = Math.max(0, Math.min(7, Number(ttlIdx) || 4));

    const header66 =
      mask45 |
      (BigInt(clampedPax) << 45n) |
      (BigInt(issuedSlot) << 53n) |
      (BigInt(validTtlIdx) << 63n);

    const labelInt = encodeLabelToInt(groupName);
    const chk4 = computeChecksum4(header66, labelInt);
    const scr66 = scramble66(header66);
    const obfLabel = obfuscateLabelInt(labelInt, scr66, chk4);

    const finalBig = (obfLabel << 70n) | (chk4 << 66n) | scr66;
    const rawB36 = finalBig.toString(36).toUpperCase().padStart(14, '0');
    return rawB36.match(/.{1,5}/g).join('-');
  }

  function decodeToken(rawInput, nowMs = Date.now()) {
    const cleaned = String(rawInput || '')
      .toUpperCase()
      .replace(/[\s\-_]+/g, '');
    if (!cleaned) return { valid: false, reason: 'Empty access code.' };

    if (ACCESS_PRESETS[cleaned]) {
      const p = ACCESS_PRESETS[cleaned];
      return {
        valid: true,
        isPreset: true,
        isExpired: false,
        code: p.code,
        groupName: p.groupName,
        targetPax: p.targetPax,
        lockedTables: [...p.lockedTables],
        recommended: [...p.recommended],
        expiryLabel: p.expiryLabel,
        remainingMs: Infinity,
      };
    }

    if (cleaned.length < 14 || cleaned.length > 42 || !/^[0-9A-Z]+$/.test(cleaned)) {
      return {
        valid: false,
        reason: 'Invalid format. Enter a valid DRS token (e.g. XXXXX-XXXXX-...) or preset code.',
      };
    }

    let finalBig = 0n;
    for (let i = 0; i < cleaned.length; i++) {
      const d = parseInt(cleaned[i], 36);
      if (Number.isNaN(d)) return { valid: false, reason: 'Invalid character in code.' };
      finalBig = finalBig * 36n + BigInt(d);
    }

    const scr66 = finalBig & MASK66;
    const chk4 = (finalBig >> 66n) & 0xFn;
    const obfLabel = finalBig >> 70n;

    const header66 = unscramble66(scr66);
    const labelInt = obfuscateLabelInt(obfLabel, scr66, chk4);
    const expectedChk = computeChecksum4(header66, labelInt);

    if (expectedChk !== chk4) {
      return {
        valid: false,
        reason: 'Access code checksum verification failed. Please check for mistyped characters.',
      };
    }

    const groupName = decodeIntToLabel(labelInt);
    if (!groupName) {
      return {
        valid: false,
        reason: 'Corrupted group label in access code.',
      };
    }

    const mask45 = header66 & ((1n << 45n) - 1n);
    const targetPax = Number((header66 >> 45n) & 0xFFn);
    const issuedSlot = Number((header66 >> 53n) & 0x3FFn);
    const ttlIdx = Number((header66 >> 63n) & 0x7n);

    if (targetPax < 1 || targetPax > 220) {
      return {
        valid: false,
        reason: 'Invalid group capacity encoded in token.',
      };
    }

    const lockedTables = [];
    for (let i = 0; i < CODEC_TABLE_IDS.length; i++) {
      if ((mask45 & (1n << BigInt(i))) !== 0n) {
        lockedTables.push(CODEC_TABLE_IDS[i]);
      }
    }

    const nowSlot = Math.floor(nowMs / SLOT_MS) & (SLOT_MOD - 1);
    let elapsedSlots = (nowSlot - issuedSlot + SLOT_MOD) & (SLOT_MOD - 1);
    if (elapsedSlots === SLOT_MOD - 1) elapsedSlots = 0;

    const allowedSlots = TTL_SLOTS[ttlIdx] || 48;
    const isExpired = elapsedSlots > allowedSlots;

    const remainingSlots = Math.max(0, allowedSlots - elapsedSlots);
    const slotRemainderMs = SLOT_MS - (nowMs % SLOT_MS);
    const remainingMs = isExpired
      ? 0
      : Math.max(0, (remainingSlots - 1) * SLOT_MS + slotRemainderMs);

    const formattedCode = cleaned.match(/.{1,5}/g).join('-');
    const lockedSet = new Set(lockedTables);
    const availSeats = TABLE_CATALOG.reduce(
      (sum, t) => (lockedSet.has(t.num) ? sum : sum + t.pax),
      0
    );

    return {
      valid: true,
      isPreset: false,
      isExpired,
      code: formattedCode,
      groupName,
      targetPax: Math.min(targetPax, Math.max(2, availSeats || targetPax)),
      lockedTables,
      recommended: buildRecommendedTables(lockedSet, targetPax),
      ttlName: TTL_NAMES[ttlIdx],
      issuedSlot,
      remainingMs,
      expiryLabel: isExpired
        ? `Expired (${TTL_NAMES[ttlIdx]} window ended · Slot #${issuedSlot} released)`
        : `${formatDurationRemaining(remainingMs)} (Slot #${issuedSlot})`,
    };
  }

  return { encodeToken, decodeToken, formatDurationRemaining };
})();

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
  b5_center: {
    pos: new THREE.Vector3(29.8, 1.62, -8.73),
    yaw: -Math.PI * 0.5,
    pitch: -0.04,
  },
};

// ============================================================================
// 2. HIGH-PERFORMANCE SCENE, RENDERERS, STATIC GEOMETRY BATCHER & CAMERAS
// ============================================================================
const canvas = document.getElementById('webgl-canvas');
const css2dContainer = document.getElementById('css2d-layer');

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: 'high-performance',
});
// Cap pixelRatio at 1.5x for locked 60+ FPS on Retina/4K presentation displays with full MSAA sharpness
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
renderer.setSize(window.innerWidth, window.innerHeight - 57);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;

const maxAnisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());

function requestShadowUpdate() {
  renderer.shadowMap.needsUpdate = true;
}

// High-FPS Geometry Batcher: Merges hundreds of static meshes sharing the same material into 1 draw call
function batchStaticMeshesInGroup(rootContainer, meshList, parentTarget) {
  const buckets = new Map();
  rootContainer.updateWorldMatrix(true, true);
  const invParentMat = parentTarget.matrixWorld.clone().invert();

  for (const mesh of meshList) {
    if (!mesh.isMesh || !mesh.visible || !mesh.geometry || Array.isArray(mesh.material)) continue;
    const geom = mesh.geometry;
    if (!geom.attributes.position || !geom.attributes.normal) continue;

    const hasUV = Boolean(geom.attributes.uv);
    const isIndexed = Boolean(geom.index);
    const key = `${mesh.material.uuid}_${hasUV ? 1 : 0}_${isIndexed ? 1 : 0}_${mesh.castShadow ? 1 : 0}`;

    if (!buckets.has(key)) {
      buckets.set(key, {
        material: mesh.material,
        hasUV,
        castShadow: mesh.castShadow,
        geoms: [],
        sourceMeshes: [],
      });
    }
    const b = buckets.get(key);

    const cloned = new THREE.BufferGeometry();
    cloned.setAttribute('position', geom.attributes.position.clone());
    cloned.setAttribute('normal', geom.attributes.normal.clone());
    if (hasUV) {
      cloned.setAttribute('uv', geom.attributes.uv.clone());
    }
    if (isIndexed) {
      cloned.setIndex(geom.index.clone());
    }

    const relMatrix = new THREE.Matrix4().multiplyMatrices(invParentMat, mesh.matrixWorld);
    cloned.applyMatrix4(relMatrix);

    b.geoms.push(cloned);
    b.sourceMeshes.push(mesh);
  }

  const createdMeshes = [];
  for (const [, b] of buckets) {
    if (b.geoms.length < 2) {
      b.geoms.forEach((g) => g.dispose());
      continue;
    }
    try {
      const mergedGeo = mergeGeometries(b.geoms, false);
      if (mergedGeo) {
        const batchedMesh = new THREE.Mesh(mergedGeo, b.material);
        batchedMesh.castShadow = b.castShadow;
        batchedMesh.receiveShadow = true;
        batchedMesh.matrixAutoUpdate = false;
        batchedMesh.updateMatrix();
        parentTarget.add(batchedMesh);
        createdMeshes.push(batchedMesh);

        for (const src of b.sourceMeshes) {
          if (src.parent) src.parent.remove(src);
        }
      }
    } catch (_) {
      // Fallback: leave original meshes if merge fails
    }
    b.geoms.forEach((g) => g.dispose());
  }
  return createdMeshes;
}

function fixFloorAndCarpetMesh(child) {
  const n = child.name || '';
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
scene.background = new THREE.Color(0x0b2842);
scene.fog = new THREE.FogExp2(0x164466, 0.00095);

const viewAspect = window.innerWidth / Math.max(1, window.innerHeight - 57);
const perspCamera = new THREE.PerspectiveCamera(42, viewAspect, 0.1, 2600);

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
let css2dDirty = true;

const controls = new OrbitControls(perspCamera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.maxDistance = 135;
controls.minDistance = 1.2;

let isOrbitDragging = false;
controls.addEventListener('start', () => {
  isOrbitDragging = true;
});
controls.addEventListener('change', () => {
  css2dDirty = true;
});
controls.addEventListener('end', () => {
  isOrbitDragging = false;
  css2dDirty = true;
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

// Optimized Interior Fill Lighting (2 wide-radius lights instead of 7 -> 3.5x faster PBR fragment shader!)
const interiorLightGroup = new THREE.Group();
scene.add(interiorLightGroup);
[
  [5.2, 3.4, -8.73, 0xffeacc, 2.1, 32.0],  // Forward Blocks 1 & 2 + Crossroads fill
  [20.6, 3.4, -8.73, 0xffeacc, 2.1, 32.0], // Aft Blocks 3 & 4 + Crossroads fill
  [34.2, 3.4, -8.73, 0xffeacc, 2.1, 32.0], // Block 5 (Green Zone) fill
].forEach(([lx, ly, lz, col, intensity, dist]) => {
  const pt = new THREE.PointLight(col, intensity, dist, 0.75);
  pt.castShadow = false;
  pt.position.set(lx, ly, lz);
  interiorLightGroup.add(pt);
});
interiorLightGroup.visible = false;

// ============================================================================
// 3. BOUNDLESS MEDITERRANEAN SEASCAPE, SKY DOME, MOUNTAINS & MARINE LIFE
// ============================================================================
const shipStageGroup = new THREE.Group();
scene.add(shipStageGroup);

const sunDirNorm = new THREE.Vector3(28, 42, 34).normalize();

// 3A. Seamless Atmospheric Sky Dome
const skyDomeGeo = new THREE.SphereGeometry(1420, 40, 20);
const skyDomeMat = new THREE.ShaderMaterial({
  side: THREE.BackSide,
  depthWrite: false,
  uniforms: {
    uSunDir: { value: sunDirNorm },
  },
  vertexShader: /* glsl */ `
    varying vec3 vWorldPos;
    void main() {
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorldPos = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }
  `,
  fragmentShader: /* glsl */ `
    varying vec3 vWorldPos;
    uniform vec3 uSunDir;
    void main() {
      vec3 dir = normalize(vWorldPos);
      float elev = clamp(dir.y, 0.0, 1.0);
      vec3 zenithCol = vec3(0.024, 0.095, 0.175);
      vec3 midSkyCol = vec3(0.055, 0.215, 0.355);
      vec3 horizonCol = vec3(0.145, 0.365, 0.515);

      vec3 col = mix(horizonCol, midSkyCol, smoothstep(0.0, 0.22, elev));
      col = mix(col, zenithCol, smoothstep(0.18, 0.75, elev));

      float sunAmt = max(dot(dir, uSunDir), 0.0);
      col += vec3(0.32, 0.24, 0.14) * pow(sunAmt, 8.0) * (1.0 - elev * 0.7);
      col += vec3(0.85, 0.75, 0.55) * pow(sunAmt, 90.0) * 0.45;

      gl_FragColor = vec4(col, 1.0);
    }
  `,
});
const skyDomeMesh = new THREE.Mesh(skyDomeGeo, skyDomeMat);
skyDomeMesh.matrixAutoUpdate = false;
shipStageGroup.add(skyDomeMesh);

// 3B. Boundless Circular Animated Mediterranean Ocean Shader
const oceanGeo = new THREE.CircleGeometry(1380, 96);
oceanGeo.rotateX(-Math.PI / 2);

const oceanUniforms = {
  uTime: { value: 0 },
  uSunDir: { value: sunDirNorm },
};

const oceanMat = new THREE.ShaderMaterial({
  uniforms: oceanUniforms,
  vertexShader: /* glsl */ `
    varying vec3 vWorldPos;
    uniform float uTime;
    void main() {
      vec4 wp = modelMatrix * vec4(position, 1.0);
      float r = length(wp.xz);
      float hullMask = smoothstep(26.0, 55.0, r);
      float swell =
        sin(wp.x * 0.08 + uTime * 1.1) * 0.12 +
        cos(wp.z * 0.09 - uTime * 0.9) * 0.10;
      wp.y += swell * hullMask * (1.0 - smoothstep(450.0, 1100.0, r));
      vWorldPos = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }
  `,
  fragmentShader: /* glsl */ `
    varying vec3 vWorldPos;
    uniform float uTime;
    uniform vec3 uSunDir;

    vec2 waveGrad(vec2 p, float t) {
      vec2 g = vec2(0.0);
      float p1 = dot(p, vec2(0.24, 0.17)) + t * 1.35;
      g += vec2(0.24, 0.17) * cos(p1) * 0.42;
      float p2 = dot(p, vec2(-0.19, 0.28)) - t * 1.15;
      g += vec2(-0.19, 0.28) * cos(p2) * 0.34;
      float p3 = dot(p, vec2(0.62, -0.48)) + t * 2.15;
      g += vec2(0.62, -0.48) * cos(p3) * 0.22;
      float p4 = dot(p, vec2(-0.88, -0.74)) - t * 2.85;
      g += vec2(-0.88, -0.74) * cos(p4) * 0.14;
      return g;
    }

    void main() {
      vec2 xz = vWorldPos.xz;
      float dist = length(xz);

      float detailFade = 1.0 - smoothstep(140.0, 750.0, dist);
      vec2 grad = waveGrad(xz, uTime) * (0.25 + 0.75 * detailFade);
      vec3 N = normalize(vec3(-grad.x * 0.28, 1.0, -grad.y * 0.28));

      vec3 V = normalize(cameraPosition - vWorldPos);
      float NoV = max(dot(N, V), 0.001);

      float fresnel = pow(1.0 - NoV, 4.2);
      fresnel = clamp(0.06 + 0.88 * fresnel, 0.0, 1.0);

      vec3 deepWater = vec3(0.014, 0.135, 0.245);
      vec3 shallowTurquoise = vec3(0.035, 0.365, 0.495);
      vec3 skyReflect = vec3(0.145, 0.375, 0.535);

      float hullProx = 1.0 - smoothstep(8.0, 62.0, dist);
      vec3 baseWater = mix(deepWater, shallowTurquoise, hullProx * 0.68 + 0.18 * (1.0 - NoV));
      vec3 waterCol = mix(baseWater, skyReflect, fresnel * 0.78);

      vec3 H = normalize(uSunDir + V);
      float specBroad = pow(max(dot(N, H), 0.0), 42.0);
      float specSparkle = pow(max(dot(N, H), 0.0), 240.0);
      waterCol += vec3(0.95, 0.86, 0.65) * (specBroad * 0.28 + specSparkle * 1.3) * detailFade;

      vec2 shipUV = vec2(xz.x / 35.5, xz.y / 6.2);
      float shipEllip = length(shipUV);
      float wakeHalo = smoothstep(1.65, 0.98, shipEllip) * smoothstep(0.75, 1.02, shipEllip);
      float foamNoise =
        0.5 + 0.5 * sin(xz.x * 2.4 + uTime * 3.2 + sin(xz.y * 2.8 - uTime * 2.1));
      float hullFoamRing =
        smoothstep(1.18, 0.99, shipEllip) *
        smoothstep(0.86, 1.0, shipEllip) *
        (0.55 + 0.45 * foamNoise);

      float sternMask = smoothstep(-28.0, -36.0, xz.x) * (1.0 - smoothstep(-36.0, -135.0, xz.x));
      float wakeWidth = 3.2 + max(0.0, (-30.0 - xz.x) * 0.14);
      float sternTrail =
        sternMask *
        exp(-(xz.y * xz.y) / (wakeWidth * wakeWidth)) *
        (0.45 + 0.55 * sin(xz.x * 1.5 - uTime * 4.5) * cos(xz.y * 1.9));

      waterCol = mix(waterCol, vec3(0.16, 0.62, 0.72), clamp(wakeHalo * 0.55 + sternTrail * 0.45, 0.0, 0.65));
      waterCol = mix(waterCol, vec3(0.92, 0.97, 1.0), clamp(hullFoamRing * 0.75 + sternTrail * 0.38, 0.0, 0.85));

      vec3 horizonMist = vec3(0.145, 0.365, 0.515);
      float horizonFactor = smoothstep(380.0, 1220.0, dist);
      waterCol = mix(waterCol, horizonMist, horizonFactor);

      gl_FragColor = vec4(waterCol, 1.0);
    }
  `,
});

const oceanMesh = new THREE.Mesh(oceanGeo, oceanMat);
oceanMesh.position.y = -0.05;
oceanMesh.matrixAutoUpdate = false;
oceanMesh.updateMatrix();
shipStageGroup.add(oceanMesh);

// 3C. 360° Surrounding Mediterranean Coastal Mountains & Islands Ring
function buildMediterraneanMountainRing() {
  const segsTheta = 144;
  const segsRad = 22;
  const innerR = 480;
  const outerR = 1120;

  const geo = new THREE.PlaneGeometry(1, 1, segsTheta, segsRad);
  const posAttr = geo.attributes.position;

  function smoothstep(edge0, edge1, x) {
    const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
    return t * t * (3 - 2 * t);
  }

  function ridgeHeight(theta, rNorm) {
    const env = Math.sin(Math.pow(rNorm, 0.78) * Math.PI);
    const w1 = Math.sin(theta * 3.0 + 0.4) * 0.5 + 0.5;
    const w2 = Math.cos(theta * 5.0 - 1.2) * 0.5 + 0.5;
    const w3 = Math.sin(theta * 11.0 + 2.1) * 0.5 + 0.5;
    const w4 = Math.cos(theta * 19.0 - 0.7) * 0.5 + 0.5;
    const w5 = Math.sin(theta * 31.0 + 1.5) * 0.5 + 0.5;

    const straitMask = smoothstep(0.18, 0.52, w1 * 0.7 + w2 * 0.3);
    const ridge1 = 1.0 - Math.abs(Math.sin(theta * 7.0 + rNorm * 2.6));
    const ridge2 = 1.0 - Math.abs(Math.cos(theta * 13.0 - rNorm * 3.4));
    const peaks =
      Math.pow(ridge1, 1.7) * 54.0 +
      Math.pow(ridge2, 2.1) * 34.0 +
      w3 * 18.0 +
      w4 * 9.0 +
      w5 * 4.5;

    return Math.max(-1.5, peaks * env * straitMask - 0.8);
  }

  for (let i = 0; i < posAttr.count; i++) {
    const u = posAttr.getX(i) + 0.5;
    const v = posAttr.getY(i) + 0.5;
    const theta = u * Math.PI * 2.0;

    const coastMeander =
      Math.sin(theta * 6.0) * 28.0 +
      Math.cos(theta * 14.0 + 1.1) * 16.0;
    const r = innerR + coastMeander * (1.0 - v) + v * (outerR - innerR);

    const x = Math.cos(theta) * r;
    const z = Math.sin(theta) * r;
    const y = ridgeHeight(theta, v);

    posAttr.setXYZ(i, x, y, z);
  }

  geo.computeVertexNormals();

  const mtnMat = new THREE.ShaderMaterial({
    uniforms: {
      uSunDir: { value: sunDirNorm },
    },
    vertexShader: /* glsl */ `
      varying vec3 vWorldPos;
      varying vec3 vNormal;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPos = wp.xyz;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: /* glsl */ `
      varying vec3 vWorldPos;
      varying vec3 vNormal;
      uniform vec3 uSunDir;
      void main() {
        if (vWorldPos.y < -0.06) discard;

        vec3 N = normalize(vNormal);
        float diff = max(dot(N, uSunDir), 0.0);

        vec3 baseCoast = vec3(0.045, 0.145, 0.235);
        vec3 rockSlope = vec3(0.095, 0.245, 0.365);
        vec3 warmPeak = vec3(0.245, 0.395, 0.505);

        float hNorm = clamp(vWorldPos.y / 78.0, 0.0, 1.0);
        vec3 terrainCol = mix(baseCoast, rockSlope, smoothstep(0.05, 0.55, hNorm));
        terrainCol = mix(terrainCol, warmPeak, smoothstep(0.45, 0.95, hNorm) * (0.4 + 0.6 * diff));
        terrainCol *= (0.62 + 0.58 * diff);

        float shoreLine = 1.0 - smoothstep(0.0, 1.8, vWorldPos.y);
        terrainCol = mix(terrainCol, vec3(0.28, 0.56, 0.68), shoreLine * 0.38);

        float dist = length(vWorldPos.xz);
        vec3 horizonMist = vec3(0.145, 0.365, 0.515);
        float haze = smoothstep(380.0, 1020.0, dist);
        haze = clamp(haze + (1.0 - hNorm) * 0.22, 0.0, 0.92);

        vec3 finalCol = mix(terrainCol, horizonMist, haze);
        gl_FragColor = vec4(finalCol, 1.0);
      }
    `,
  });

  const mtnMesh = new THREE.Mesh(geo, mtnMat);
  mtnMesh.matrixAutoUpdate = false;
  mtnMesh.updateMatrix();
  shipStageGroup.add(mtnMesh);
}

buildMediterraneanMountainRing();

// ============================================================================
// 3D. ANIMATED MEDITERRANEAN MARINE LIFE (WHALE, DOLPHIN/TUNA POD & FISH SCHOOL)
//     Passes naturally alongside the ship in alternating lanes (Never circles!)
// ============================================================================
const marineLifeSystem = (() => {
  const group = new THREE.Group();
  shipStageGroup.add(group);

  // 1. Build Sculpted Fin Whale Mesh (With Horizontal Cetacean Tail Flukes & Blowhole Spray)
  function createWhaleGeometry() {
    const geoms = [];
    // Fusiform whale body along Z (-6.5m tail to +5.5m snout)
    const bodyGeo = new THREE.SphereGeometry(1, 24, 16);
    const pos = bodyGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      let x = pos.getX(i);
      let y = pos.getY(i);
      let z = pos.getZ(i);
      // Stretch along Z: length ~13m
      const zNorm = z; // -1..+1
      const zLen = zNorm * 6.4;
      // Taper gently toward tail (zNorm < 0) and sleek rostrum snout (zNorm > 0)
      const tailTaper = zNorm < 0 ? Math.pow(1.0 + zNorm * 0.82, 1.35) : 1.0 - Math.pow(zNorm, 1.8) * 0.55;
      const widthScale = 1.25 * tailTaper;
      const heightScale = (zNorm > 0.2 ? 0.85 : 1.05) * tailTaper;
      x *= widthScale;
      y *= heightScale;
      // Flatten belly slightly and arch the dorsal back
      if (y > 0) y *= 1.15;
      else y *= 0.82;
      pos.setXYZ(i, x, y, zLen);
    }
    bodyGeo.computeVertexNormals();
    geoms.push(bodyGeo);

    // Horizontal Cetacean Tail Flukes (Unmistakably a Whale, NOT a vertical shark fin!)
    const flukeGeo = new THREE.BoxGeometry(3.6, 0.14, 1.35, 8, 1, 4);
    const fPos = flukeGeo.attributes.position;
    for (let i = 0; i < fPos.count; i++) {
      const fx = fPos.getX(i);
      const fy = fPos.getY(i);
      const fz = fPos.getZ(i);
      const ax = Math.abs(fx) / 1.8;
      // Sweep fluke tips backward
      const sweepZ = -ax * ax * 0.85;
      const chordScale = 1.0 - ax * 0.65;
      fPos.setXYZ(i, fx, fy * (1.0 - ax * 0.5), fz * chordScale + sweepZ - 6.35);
    }
    flukeGeo.computeVertexNormals();
    geoms.push(flukeGeo);

    // Pectoral Flippers (Left & Right)
    [-1, 1].forEach((side) => {
      const flipGeo = new THREE.BoxGeometry(2.1, 0.12, 0.75, 4, 1, 2);
      flipGeo.rotateZ(side * -0.28);
      flipGeo.rotateY(side * -0.35);
      flipGeo.translate(side * 1.55, -0.35, 1.4);
      flipGeo.computeVertexNormals();
      geoms.push(flipGeo);
    });

    // Small curved backwards cetacean dorsal fin on aft back (z = -2.4m)
    const dorsalGeo = new THREE.ConeGeometry(0.32, 0.68, 8);
    dorsalGeo.scale(0.32, 1.0, 1.35);
    dorsalGeo.rotateX(-0.48);
    dorsalGeo.translate(0, 0.78, -2.5);
    dorsalGeo.computeVertexNormals();
    geoms.push(dorsalGeo);

    return mergeGeometries(geoms, false);
  }

  const whaleGeo = createWhaleGeometry();
  const whaleUniforms = {
    uTime: { value: 0 },
  };
  const whaleMat = new THREE.MeshStandardMaterial({
    color: 0x162d3e,
    roughness: 0.25,
    metalness: 0.18,
  });
  whaleMat.onBeforeCompile = (shader) => {
    shader.uniforms.uSwimTime = whaleUniforms.uTime;
    shader.vertexShader =
      `uniform float uSwimTime;\n` +
      shader.vertexShader.replace(
        '#include <begin_vertex>',
        /* glsl */ `
        vec3 transformed = vec3(position);
        // Cetacean vertical tail-stroke undulation (increases toward tail z < 0)
        float tailFactor = clamp((2.0 - transformed.z) / 8.5, 0.0, 1.0);
        float wave = sin(uSwimTime * 3.4 + transformed.z * 0.45) * 0.42 * tailFactor * tailFactor;
        transformed.y += wave;
        `
      );
  };

  const whaleMesh = new THREE.Mesh(whaleGeo, whaleMat);
  group.add(whaleMesh);

  // Whale Blowhole Water Spout (Misty fountain spray when whale surfaces)
  const SPOUT_COUNT = 22;
  const spoutGeo = new THREE.SphereGeometry(0.28, 8, 6);
  const spoutMat = new THREE.MeshBasicMaterial({
    color: 0xeaf6ff,
    transparent: true,
    opacity: 0.62,
    depthWrite: false,
  });
  const spoutInst = new THREE.InstancedMesh(spoutGeo, spoutMat, SPOUT_COUNT);
  spoutInst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  group.add(spoutInst);

  // Expanding White Surface Ripple Rings (for Whale & Leaping Dolphins)
  const RING_COUNT = 6;
  const ringGeo = new THREE.RingGeometry(0.65, 1.0, 24);
  ringGeo.rotateX(-Math.PI / 2);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0xdff4ff,
    transparent: true,
    opacity: 0.55,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const ringInst = new THREE.InstancedMesh(ringGeo, ringMat, RING_COUNT);
  ringInst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  group.add(ringInst);

  // 2. Pod of 4 Mediterranean Dolphins / Bluefin Surface Swimmers
  const POD_COUNT = 4;
  function createDolphinGeometry() {
    const g = new THREE.SphereGeometry(0.38, 16, 10);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i) * 0.82;
      const y = p.getY(i) * 0.95;
      const z = p.getZ(i) * 3.4;
      p.setXYZ(i, x, y, z);
    }
    g.computeVertexNormals();
    return g;
  }
  const podGeo = createDolphinGeometry();
  const podMat = new THREE.MeshStandardMaterial({
    color: 0x2b5672,
    roughness: 0.22,
    metalness: 0.25,
  });
  const podInst = new THREE.InstancedMesh(podGeo, podMat, POD_COUNT);
  podInst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  group.add(podInst);

  // 3. Shimmering School of 48 Small Silver-Turquoise Surface Fish
  const SCHOOL_COUNT = 48;
  const fishGeo = new THREE.ConeGeometry(0.11, 0.52, 6);
  fishGeo.rotateX(Math.PI / 2);
  fishGeo.scale(0.55, 1.0, 1.0);
  const fishMat = new THREE.MeshStandardMaterial({
    color: 0x7fd4ea,
    emissive: 0x1a5e78,
    emissiveIntensity: 0.35,
    roughness: 0.18,
    metalness: 0.65,
  });
  const schoolInst = new THREE.InstancedMesh(fishGeo, fishMat, SCHOOL_COUNT);
  schoolInst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  group.add(schoolInst);

  // Precomputed offsets for the 48 small fish in the school
  const fishOffsets = Array.from({ length: SCHOOL_COUNT }, (_, i) => ({
    dx: ((i % 8) - 3.5) * 0.85 + Math.sin(i * 1.7) * 0.35,
    dz: (Math.floor(i / 8) - 2.5) * 0.95 + Math.cos(i * 2.3) * 0.35,
    dy: -0.12 - (i % 4) * 0.08,
    phase: i * 0.65,
  }));

  // 4 Straight / Gently Curved Passing Lanes Near the Ship (NEVER circling!)
  const PASS_LANES = [
    // Lane 0: Portside (+Z) passing from Bow (+X) toward Stern (-X)
    {
      start: new THREE.Vector3(88, 0, 17.5),
      end: new THREE.Vector3(-88, 0, 21.0),
      swayZ: 2.8,
      mode: 'whale_and_school',
    },
    // Lane 1: Starboardside (-Z) passing from Stern (-X) toward Bow (+X)
    {
      start: new THREE.Vector3(-82, 0, -18.5),
      end: new THREE.Vector3(86, 0, -16.0),
      swayZ: -2.4,
      mode: 'pod_and_school',
    },
    // Lane 2: Portside Closer Pass from Stern (-X) toward Bow (+X)
    {
      start: new THREE.Vector3(-86, 0, 15.0),
      end: new THREE.Vector3(88, 0, 18.5),
      swayZ: 2.2,
      mode: 'pod_and_school',
    },
    // Lane 3: Starboardside Pass from Bow (+X) toward Stern (-X)
    {
      start: new THREE.Vector3(86, 0, -20.0),
      end: new THREE.Vector3(-86, 0, -16.5),
      swayZ: -2.6,
      mode: 'whale_and_school',
    },
  ];

  const PASS_DURATION = 22.0; // seconds per linear pass
  const dummy = new THREE.Object3D();
  const posVec = new THREE.Vector3();
  const nextVec = new THREE.Vector3();

  function sampleLanePos(lane, u, outVec) {
    outVec.lerpVectors(lane.start, lane.end, u);
    outVec.z += Math.sin(u * Math.PI) * lane.swayZ;
  }

  function update(timeSec) {
    whaleUniforms.uTime.value = timeSec;

    const cycleIdx = Math.floor(timeSec / PASS_DURATION) % PASS_LANES.length;
    const lane = PASS_LANES[cycleIdx];
    const u = (timeSec % PASS_DURATION) / PASS_DURATION; // 0..1 linear progress along pass

    sampleLanePos(lane, u, posVec);
    sampleLanePos(lane, Math.min(1.0, u + 0.01), nextVec);
    const headingYaw = Math.atan2(nextVec.x - posVec.x, nextVec.z - posVec.z);

    // Smooth entry/exit depth fade at ends of the pass (u < 0.12 or u > 0.88)
    const endSubmerge =
      u < 0.12
        ? -2.8 * (1.0 - u / 0.12)
        : u > 0.88
        ? -2.8 * ((u - 0.88) / 0.12)
        : 0.0;

    // --- A. WHALE PASS & BLOWHOLE WATER SPOUT ---
    if (lane.mode === 'whale_and_school') {
      whaleMesh.visible = true;
      spoutInst.visible = true;

      // Whale surfaces smoothly twice during its pass (around u=0.32 and u=0.66)
      const crestWave = Math.sin(u * Math.PI * 3.0 - 0.4);
      const whaleY = -0.72 + Math.max(-0.6, crestWave * 0.68) + endSubmerge;
      const whalePitch = -Math.cos(u * Math.PI * 3.0 - 0.4) * 0.14;

      whaleMesh.position.set(posVec.x, whaleY, posVec.z);
      whaleMesh.rotation.set(whalePitch, headingYaw, 0);

      // Blowhole spout activates when whale back crests at the surface (crestWave > 0.25)
      const spoutActive = crestWave > 0.15 && endSubmerge > -0.3;
      const blowX = posVec.x + Math.sin(headingYaw) * 2.4;
      const blowZ = posVec.z + Math.cos(headingYaw) * 2.4;

      for (let i = 0; i < SPOUT_COUNT; i++) {
        if (!spoutActive) {
          dummy.position.set(0, -50, 0);
          dummy.scale.setScalar(0.001);
        } else {
          const pAge = (timeSec * 2.4 + i / SPOUT_COUNT) % 1.0;
          const spread = pAge * 0.95;
          const angle = i * 2.399;
          dummy.position.set(
            blowX + Math.cos(angle) * spread,
            0.15 + Math.sin(pAge * Math.PI) * 2.85,
            blowZ + Math.sin(angle) * spread
          );
          const sc = (0.35 + pAge * 1.45) * (1.0 - pAge * 0.65);
          dummy.scale.setScalar(sc);
        }
        dummy.updateMatrix();
        spoutInst.setMatrixAt(i, dummy.matrix);
      }
      spoutInst.instanceMatrix.needsUpdate = true;

      // Expanding surface ripple rings around surfacing whale
      for (let r = 0; r < RING_COUNT; r++) {
        const rAge = (timeSec * 0.55 + r / RING_COUNT) % 1.0;
        if (whaleY > -0.95) {
          dummy.position.set(
            posVec.x - Math.sin(headingYaw) * rAge * 4.0,
            -0.02,
            posVec.z - Math.cos(headingYaw) * rAge * 4.0
          );
          const rad = 1.6 + rAge * 5.2;
          dummy.scale.set(rad, 1, rad * (1.0 - rAge * 0.3));
        } else {
          dummy.position.set(0, -50, 0);
          dummy.scale.setScalar(0.001);
        }
        dummy.updateMatrix();
        ringInst.setMatrixAt(r, dummy.matrix);
      }
      ringInst.instanceMatrix.needsUpdate = true;
      podInst.visible = false;
    } else {
      // --- B. DOLPHIN / BLUEFIN POD SURFACE LEAPS ---
      whaleMesh.visible = false;
      spoutInst.visible = false;
      podInst.visible = true;

      const rightX = Math.cos(headingYaw);
      const rightZ = -Math.sin(headingYaw);
      const fwdX = Math.sin(headingYaw);
      const fwdZ = Math.cos(headingYaw);

      for (let i = 0; i < POD_COUNT; i++) {
        const latOff = (i - 1.5) * 2.2;
        const lonOff = (i % 2 === 0 ? 1 : -1) * 2.4 - i * 1.8;
        const leapCycle = (timeSec * 1.55 + i * 0.38) % (Math.PI * 2.0);
        const leapSin = Math.sin(leapCycle);
        // Parabolic leap above surface when leapSin > 0, shallow glide beneath when < 0
        const py = (leapSin > 0 ? leapSin * 1.45 : leapSin * 0.35) - 0.15 + endSubmerge;
        const pitch = -Math.cos(leapCycle) * (leapSin > 0 ? 0.52 : 0.15);

        const dx = posVec.x + rightX * latOff + fwdX * lonOff;
        const dz = posVec.z + rightZ * latOff + fwdZ * lonOff;

        dummy.position.set(dx, py, dz);
        dummy.rotation.set(pitch, headingYaw, 0);
        dummy.scale.setScalar(1.0);
        dummy.updateMatrix();
        podInst.setMatrixAt(i, dummy.matrix);

        // Splash ring where dolphin breaches/enters water
        if (i < RING_COUNT) {
          const splashAge = (leapCycle / (Math.PI * 2.0)) % 1.0;
          dummy.position.set(dx, -0.02, dz);
          dummy.rotation.set(0, 0, 0);
          const sRad = 0.4 + splashAge * 2.2;
          dummy.scale.setScalar(endSubmerge > -0.5 ? sRad : 0.001);
          dummy.updateMatrix();
          ringInst.setMatrixAt(i, dummy.matrix);
        }
      }
      for (let r = POD_COUNT; r < RING_COUNT; r++) {
        dummy.position.set(0, -50, 0);
        dummy.scale.setScalar(0.001);
        dummy.updateMatrix();
        ringInst.setMatrixAt(r, dummy.matrix);
      }
      podInst.instanceMatrix.needsUpdate = true;
      ringInst.instanceMatrix.needsUpdate = true;
    }

    // --- C. SHIMMERING SCHOOL OF SMALL FISH (Accompanies passes near the hull) ---
    // School swims slightly closer to the ship hull on the opposite or adjacent beat
    const schoolU = (u + 0.18) % 1.0;
    sampleLanePos(lane, schoolU, nextVec);
    const inwardSign = nextVec.z > 0 ? -1 : 1;
    const schoolCenterX = nextVec.x;
    const schoolCenterZ = nextVec.z + inwardSign * 3.8;

    const rightX = Math.cos(headingYaw);
    const rightZ = -Math.sin(headingYaw);
    const fwdX = Math.sin(headingYaw);
    const fwdZ = Math.cos(headingYaw);

    for (let i = 0; i < SCHOOL_COUNT; i++) {
      const fo = fishOffsets[i];
      const wiggle = Math.sin(timeSec * 7.5 + fo.phase) * 0.14;
      const fx = schoolCenterX + fwdX * fo.dz + rightX * (fo.dx + wiggle);
      const fz = schoolCenterZ + fwdZ * fo.dz + rightZ * (fo.dx + wiggle);
      const fy = fo.dy + Math.sin(timeSec * 3.2 + fo.phase) * 0.05;

      dummy.position.set(fx, fy, fz);
      dummy.rotation.set(0, headingYaw + Math.cos(timeSec * 7.5 + fo.phase) * 0.18, 0);
      dummy.scale.setScalar(1.0);
      dummy.updateMatrix();
      schoolInst.setMatrixAt(i, dummy.matrix);
    }
    schoolInst.instanceMatrix.needsUpdate = true;
  }

  return { update };
})();

// ============================================================================
// 3E. COSTA SMERALDA 3D MODEL & 4-LAYER CUTAWAY SYSTEM (BATCHED FOR 60+ FPS)
// ============================================================================
const shipLayerNodes = {
  L0: null,
  L1: null,
  L2: null,
  L3: null,
  L4: null,
};

let shipEmbeddedArlecchinoNode = null;
const shipLayerTargetY = { L1: 0, L2: 0, L3: 0, L4: 0 };
let currentCutawayMode = 'full';
let arlecchinoHitboxMesh = null;

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
  obj.visible = false;
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
    css2dDirty = true;
    loaderOverlay.classList.add('is-hidden');
  }
}

gltfLoader.load(
  './costa_smeralda_ship.glb?v=20261026i',
  (gltf) => {
    const shipModel = gltf.scene;
    shipStageGroup.add(shipModel);

    const embeddedArlMeshes = [];
    const layerMeshBuckets = { L0: [], L1: [], L2: [], L3: [], L4: [] };

    shipModel.traverse((child) => {
      if (child.name === 'Ship_Layer0_Base_Deck4Down') shipLayerNodes.L0 = child;
      if (child.name === 'Ship_Layer1_Deck5') shipLayerNodes.L1 = child;
      if (child.name === 'Ship_Layer2_Deck6') shipLayerNodes.L2 = child;
      if (child.name === 'Ship_Layer3_Deck7') shipLayerNodes.L3 = child;
      if (child.name === 'Ship_Layer4_Top_Deck8ToMuffler') shipLayerNodes.L4 = child;
      if (child.name === 'L2_Arlecchino_2Block_RealModel') {
        shipEmbeddedArlecchinoNode = child;
      }

      if (child.isMesh) {
        fixFloorAndCarpetMesh(child);
        if (child.name === 'L2_Arlecchino_2Block_Active_Hitbox') {
          arlecchinoHitboxMesh = child;
          return;
        }

        // Check if mesh belongs to the 1,694-mesh embedded Arlecchino model on Deck 6
        let p = child.parent;
        let inEmbeddedArl = false;
        let layerKey = null;
        while (p) {
          if (p.name === 'L2_Arlecchino_2Block_RealModel') inEmbeddedArl = true;
          if (p.name === 'Ship_Layer0_Base_Deck4Down') layerKey = 'L0';
          if (p.name === 'Ship_Layer1_Deck5') layerKey = 'L1';
          if (p.name === 'Ship_Layer2_Deck6') layerKey = 'L2';
          if (p.name === 'Ship_Layer3_Deck7') layerKey = 'L3';
          if (p.name === 'Ship_Layer4_Top_Deck8ToMuffler') layerKey = 'L4';
          p = p.parent;
        }

        child.castShadow = !inEmbeddedArl;
        child.receiveShadow = true;

        if (inEmbeddedArl) {
          embeddedArlMeshes.push(child);
        } else if (layerKey && layerMeshBuckets[layerKey]) {
          layerMeshBuckets[layerKey].push(child);
        }
      }
    });

    // Batch the 1,694 embedded Deck 6 meshes into ~18 draw calls AND hide when ship is closed!
    if (shipEmbeddedArlecchinoNode && embeddedArlMeshes.length > 0) {
      batchStaticMeshesInGroup(shipModel, embeddedArlMeshes, shipEmbeddedArlecchinoNode);
      shipEmbeddedArlecchinoNode.visible =
        currentStage === 'ship' && (currentCutawayMode === 'deck6' || currentCutawayMode === 'deck5');
    }

    // Batch each exterior ship deck layer for minimal draw calls during 360° orbit
    for (const key of ['L0', 'L1', 'L2', 'L3', 'L4']) {
      if (shipLayerNodes[key] && layerMeshBuckets[key].length > 1) {
        batchStaticMeshesInGroup(shipModel, layerMeshBuckets[key], shipLayerNodes[key]);
      }
    }

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
    eyebrow: 'DECK 6 · ROMA (MID-SHIP)',
    title: 'Ristorante Arlecchino',
    desc: 'Use the top bar to inspect deck cutaways or open Deck 6 to allocate your group tables.',
    subtitle: 'GROUP DINING RESERVATION SYSTEM',
  },
  deck7: {
    eyebrow: 'DECK 7 · POSITANO (AFT)',
    title: 'Ristorante Il Rugantino',
    desc: 'Deck 8 to funnel lifted. Aft zone shows Il Rugantino (546 seats) architectural placeholder.',
    subtitle: 'DECK 7 CUTAWAY · IL RUGANTINO',
  },
  deck6: {
    eyebrow: 'DECK 6 · ROMA (MID-SHIP)',
    title: 'Ristorante Arlecchino',
    desc: 'Mid-ship displays all 4 blocks of Arlecchino (45 tables · 220 seats). Click below to allocate tables.',
    subtitle: 'DECK 6 CUTAWAY · RISTORANTE ARLECCHINO',
  },
  deck5: {
    eyebrow: 'DECK 5 · TAORMINA (AFT)',
    title: 'Ristorante La Colombina',
    desc: 'Decks 6, 7, and 8 lifted in stepped tiers. Aft shows La Colombina (978 seats) placeholder.',
    subtitle: 'DECK 5 CUTAWAY · LA COLOMBINA',
  },
};

function setDeckLabelVis(labelRecord, vis) {
  if (!labelRecord) return;
  labelRecord.obj.visible = vis;
  labelRecord.el.classList.toggle('is-hidden', !vis);
}

function setShipCutawayLayer(layerMode, animateCam = true) {
  if (currentStage === 'gate') {
    layerMode = 'full';
  }
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
  if (currentStage === 'ship') {
    document.getElementById('stage-subtitle').textContent = info.subtitle;
  }

  // Only render the embedded 1,694-mesh Deck 6 interior when Deck 6 or Deck 5 cutaway is open!
  if (shipEmbeddedArlecchinoNode) {
    shipEmbeddedArlecchinoNode.visible =
      currentStage === 'ship' && (layerMode === 'deck6' || layerMode === 'deck5');
  }

  setDeckLabelVis(deckCutawayLabels.colombina, currentStage === 'ship' && layerMode === 'deck5');
  setDeckLabelVis(deckCutawayLabels.meneghino, currentStage === 'ship' && layerMode === 'deck6');
  setDeckLabelVis(deckCutawayLabels.rugantino, currentStage === 'ship' && layerMode === 'deck7');
  setDeckLabelVis(
    deckCutawayLabels.arlecchinoMain,
    currentStage === 'ship' && (layerMode === 'full' || layerMode === 'deck6')
  );
  css2dDirty = true;

  if (layerMode === 'full') {
    shipLayerTargetY.L1 = 0;
    shipLayerTargetY.L2 = 0;
    shipLayerTargetY.L3 = 0;
    shipLayerTargetY.L4 = 0;
    if (animateCam) {
      animateCameraTo(new THREE.Vector3(36, 16.5, 48), new THREE.Vector3(0, 5.2, 0), 850);
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
// 4. STAGE 2: LOAD 4-BLOCK ARLECCHINO GLB, MATCH ALL 45 TABLES & BATCH MESHES
// ============================================================================
const restaurantGroup = new THREE.Group();
restaurantGroup.visible = false;
scene.add(restaurantGroup);

const ceilingBatchGroup = new THREE.Group();
const chandelierBatchGroup = new THREE.Group();
const mainInteriorBatchGroup = new THREE.Group();
restaurantGroup.add(mainInteriorBatchGroup, ceilingBatchGroup, chandelierBatchGroup);

const ceilingMeshes = [];
const chandelierMeshes = [];
const tableRegistry = new Map();
const interactiveHitProxies = [];

const hitProxyMat = new THREE.MeshBasicMaterial({
  visible: false,
});

gltfLoader.load(
  './arlecchino_block1.glb?v=20261027b',
  (gltf) => {
    const model = gltf.scene;
    restaurantGroup.add(model);

    const mainStaticMeshes = [];

    model.traverse((child) => {
      if (!child.isMesh) return;
      fixFloorAndCarpetMesh(child);
      const n = child.name || '';

      const isSmallDetail =
        n.includes('Plate') ||
        n.includes('Phone') ||
        n.includes('Spot') ||
        n.includes('Downlight') ||
        n.includes('Art') ||
        n.includes('Chandelier') ||
        n.includes('Pendant');
      child.castShadow = !isSmallDetail;
      child.receiveShadow = true;

      if (n.startsWith('Ceiling_Chandelier_') || n.startsWith('B5_Pendant_')) {
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
      } else {
        mainStaticMeshes.push(child);
      }

      for (const meta of TABLE_CATALOG) {
        if (
          n.includes(meta.nodeKey) ||
          n.includes(`_${meta.num}_`) ||
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
      proxyMesh.matrixAutoUpdate = false;
      proxyMesh.updateMatrix();
      proxyMesh.userData.tableNum = meta.num;
      restaurantGroup.add(proxyMesh);
      interactiveHitProxies.push(proxyMesh);

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
      glassPad.matrixAutoUpdate = false;
      glassPad.updateMatrix();
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
      labelObj.visible = false;
      restaurantGroup.add(labelObj);
      entry.labelObj = labelObj;
      entry.labelEl = markerEl;
    }

    // Batch 1,810 static interior meshes into ~24 material draw calls!
    batchStaticMeshesInGroup(model, mainStaticMeshes, mainInteriorBatchGroup);
    const batchedCeil = batchStaticMeshesInGroup(model, ceilingMeshes, ceilingBatchGroup);
    const batchedChand = batchStaticMeshesInGroup(model, chandelierMeshes, chandelierBatchGroup);
    ceilingMeshes.push(...batchedCeil);
    chandelierMeshes.push(...batchedChand);

    buildSidebarTableRowsOnce();
    applyAccessSession(activeSession);
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
// 5. STATE MANAGEMENT: 3-STAGE HIERARCHY (GATE -> SHIP -> INTERIOR)
// ============================================================================
let currentStage = 'gate';
let currentCamMode = 'bird';
let top2dFlipped = false;
let showTableNumbers = true;
let activeBlockFilter = 'all';

let activeSession = { ...ACCESS_PRESETS.A98XKJ90 };
let selectedTables = new Set();
let lockedTables = new Set(activeSession.lockedTables);
let hoveredTableNum = null;

let camAnim = null;
let currentViewOffsetX = 0;
let targetViewOffsetX = 0;

function updateCameraViewOffset() {
  const w = window.innerWidth;
  const h = Math.max(1, window.innerHeight - 57);
  targetViewOffsetX = currentStage === 'gate' && w > 960 ? Math.round(Math.min(200, w * 0.145)) : 0;

  if (Math.abs(currentViewOffsetX) > 0.5) {
    perspCamera.setViewOffset(w, h, -currentViewOffsetX, 0, w, h);
  } else {
    perspCamera.clearViewOffset();
  }
}

function runStageViewTransition(domMutator, focusElementId = null) {
  const finishFocus = () => {
    if (focusElementId) {
      document.getElementById(focusElementId)?.focus({ preventScroll: true });
    }
  };
  if (!document.startViewTransition) {
    domMutator();
    finishFocus();
    return;
  }
  const transition = document.startViewTransition(() => {
    domMutator();
  });
  transition.finished.finally(finishFocus);
}

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
      css2dDirty = true;
      if (t >= 1) {
        camAnim = null;
        if (onDone) onDone();
      }
    },
  };
}

// STAGE 0: INITIAL ACCESS GATE
function setGateStage(instant = false) {
  currentStage = 'gate';
  activeCamera = perspCamera;
  perspCamera.fov = 42;
  perspCamera.up.set(0, 1, 0);
  perspCamera.updateProjectionMatrix();

  controls.object = perspCamera;
  controls.enabled = true;
  controls.enableRotate = true;
  controls.enablePan = false;
  controls.maxPolarAngle = Math.PI * 0.468;

  sunLight.position.set(28, 42, 34);
  sunLight.intensity = 2.3;
  sunLight.castShadow = true;
  ambientLight.intensity = 1.55;
  hemiLight.intensity = 1.25;

  shipStageGroup.visible = true;
  restaurantGroup.visible = false;
  interiorLightGroup.visible = false;

  if (shipEmbeddedArlecchinoNode) {
    shipEmbeddedArlecchinoNode.visible = false;
  }

  shipLayerTargetY.L1 = 0;
  shipLayerTargetY.L2 = 0;
  shipLayerTargetY.L3 = 0;
  shipLayerTargetY.L4 = 0;
  Object.values(deckCutawayLabels).forEach((lbl) => setDeckLabelVis(lbl, false));

  updateTableMarkersVisibility();
  requestShadowUpdate();

  const applyDOM = () => {
    document.getElementById('gate-access-ui').classList.add('is-active');
    document.getElementById('hero-ship-ui').classList.remove('is-active');
    document.getElementById('interior-ui').classList.remove('is-active');

    document.getElementById('ship-toolbar').hidden = true;
    document.getElementById('interior-toolbar').hidden = true;
    document.getElementById('active-session-bar').hidden = true;
    document.getElementById('stage-subtitle').textContent = 'GROUP DINING RESERVATION SYSTEM';
  };

  if (instant) {
    applyDOM();
    currentViewOffsetX = window.innerWidth > 960 ? Math.round(Math.min(200, window.innerWidth * 0.145)) : 0;
    updateCameraViewOffset();
    perspCamera.position.set(38, 15.5, 50);
    controls.target.set(0, 5.0, 0);
    controls.update();
  } else {
    runStageViewTransition(applyDOM, 'gate-heading');
    animateCameraTo(new THREE.Vector3(38, 15.5, 50), new THREE.Vector3(0, 5.0, 0), 800);
  }
}

// STAGE 1: SHIP CUTAWAY DASHBOARD
function setHeroShipCamera(instant = false) {
  currentStage = 'ship';
  activeCamera = perspCamera;
  perspCamera.fov = 42;
  perspCamera.up.set(0, 1, 0);
  perspCamera.updateProjectionMatrix();

  controls.object = perspCamera;
  controls.enabled = true;
  controls.enableRotate = true;
  controls.enablePan = true;
  controls.maxPolarAngle = Math.PI * 0.468;

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

  const applyDOM = () => {
    document.getElementById('gate-access-ui').classList.remove('is-active');
    document.getElementById('hero-ship-ui').classList.add('is-active');
    document.getElementById('interior-ui').classList.remove('is-active');

    document.getElementById('ship-toolbar').hidden = false;
    document.getElementById('interior-toolbar').hidden = true;
    document.getElementById('active-session-bar').hidden = false;
  };

  if (instant) {
    applyDOM();
  } else {
    runStageViewTransition(applyDOM, 'ship-card-title');
  }

  setShipCutawayLayer('full', !instant);
  if (instant) {
    perspCamera.position.set(36, 16.5, 48);
    controls.target.set(0, 5.2, 0);
    controls.update();
  }
}

setGateStage(true);

function enterInterior2Blocks() {
  if (currentStage !== 'ship') return;

  setShipCutawayLayer('deck6', false);
  Object.values(deckCutawayLabels).forEach((lbl) => setDeckLabelVis(lbl, false));

  animateCameraTo(
    new THREE.Vector3(-0.5, 5.2, 6.8),
    new THREE.Vector3(-1.5, 3.0, 1.5),
    750,
    () => {
      currentStage = 'interior';
      shipStageGroup.visible = false;
      restaurantGroup.visible = true;
      interiorLightGroup.visible = true;

      sunLight.position.set(12.9, 48, -8.73);
      sunLight.intensity = 1.15;
      sunLight.castShadow = false;
      ambientLight.intensity = 1.75;
      hemiLight.intensity = 1.3;

      runStageViewTransition(() => {
        document.getElementById('gate-access-ui').classList.remove('is-active');
        document.getElementById('hero-ship-ui').classList.remove('is-active');
        document.getElementById('interior-ui').classList.add('is-active');
        document.getElementById('ship-toolbar').hidden = true;
        document.getElementById('interior-toolbar').hidden = false;
        document.getElementById('active-session-bar').hidden = false;
        document.getElementById('stage-subtitle').textContent =
          'DECK 6 ROMA · RISTORANTE ARLECCHINO';
      }, 'interior-sidebar-heading');

      setInteriorCameraMode('bird');
      updateTableMarkersVisibility();
    }
  );
}

function setCeilingVisible(vis, showChandelier = vis) {
  ceilingBatchGroup.visible = vis;
  chandelierBatchGroup.visible = showChandelier;
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
    if (!entry.labelEl || !entry.labelObj) continue;
    const matchBlock =
      activeBlockFilter === 'all' || entry.meta.block === activeBlockFilter;
    const vis = shouldShow && matchBlock;
    entry.labelObj.visible = vis;
    entry.labelEl.classList.toggle('is-hidden', !vis);
  }
  css2dDirty = true;
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
    css2dDirty = true;
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
  const spot = WALK_SPOTS[spotKey] || WALK_SPOTS.crossroads;
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
  css2dDirty = true;
}

// ============================================================================
// 7. HOVER PILL, ACCESS SESSION & IN-PLACE TABLE SELECTION LOGIC
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

function applyAccessSession(sessionObj) {
  activeSession = sessionObj;
  lockedTables = new Set(sessionObj.lockedTables);
  selectedTables.clear();

  const availCount = TABLE_CATALOG.length - lockedTables.size;

  // Masthead shows ONLY the clean, untruncated Welcome greeting (zero duplicate code or truncated text)
  document.getElementById('active-welcome-badge').textContent = `Welcome, ${sessionObj.groupName}`;

  // Stage 1 compact summary strip
  document.getElementById('sts-avail-Info').textContent =
    `${sessionObj.targetPax} Pax Group · ${availCount} Available Tables · ${lockedTables.size} Reserved`;
  document.getElementById('btn-enter-deck6-label').textContent =
    `Open Ristorante Arlecchino (${availCount} Open Tables)`;

  syncSelectionUI();
}

function syncSelectionUI() {
  const targetPax = activeSession.targetPax || 44;
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
  document.getElementById('target-pax-count').textContent = String(targetPax);
  document.getElementById('selected-table-count').textContent =
    `${selectedTables.size} ${selectedTables.size === 1 ? 'Table' : 'Tables'}`;

  const pct = Math.min(100, Math.round((totalPax / targetPax) * 100));
  document.getElementById('pax-progress-fill').style.width = `${pct}%`;
  document.getElementById('pax-progressbar').setAttribute('aria-valuenow', String(totalPax));
  document.getElementById('pax-progressbar').setAttribute('aria-valuemax', String(targetPax));

  const pill = document.getElementById('pax-status-pill');
  const diff = targetPax - totalPax;
  pill.classList.remove('is-warn', 'is-good');
  if (totalPax === 0) {
    pill.textContent = `0 / ${targetPax} Pax`;
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
// 7B. STAGE 0 GATE FORM VALIDATION, LIVE PREVIEW & UNLOCK FLOW
// ============================================================================
const gateForm = document.getElementById('gate-access-form');
const gateInput = document.getElementById('gate-code-input');
const gateErrorEl = document.getElementById('gate-code-error');
const gatePreviewBox = document.getElementById('gate-token-preview');

function evaluateGateCodeInput(showErrors = false) {
  const raw = gateInput.value.trim();
  gateErrorEl.hidden = true;
  gateInput.classList.remove('is-code-error', 'is-code-valid');
  gateInput.setCustomValidity('');

  if (!raw) {
    gatePreviewBox.hidden = true;
    if (showErrors) {
      gateErrorEl.textContent = 'Please enter a valid Costa DRS access code.';
      gateErrorEl.hidden = false;
      gateInput.classList.add('is-code-error');
    }
    return null;
  }

  const res = DRS_CODEC.decodeToken(raw);
  if (!res.valid) {
    gatePreviewBox.hidden = true;
    if (showErrors) {
      gateInput.setCustomValidity(res.reason);
      gateErrorEl.textContent = res.reason;
      gateErrorEl.hidden = false;
      gateInput.classList.add('is-code-error');
    }
    return null;
  }

  const availCount = TABLE_CATALOG.length - res.lockedTables.length;
  gatePreviewBox.hidden = false;
  gatePreviewBox.classList.toggle('is-expired', res.isExpired);

  document.getElementById('gtp-greeting-text').textContent = `Welcome, ${res.groupName}!`;
  document.getElementById('gtp-status-badge').textContent = res.isExpired
    ? 'Expired Token'
    : res.isPreset
    ? 'Verified Preset'
    : 'Verified DRS Token';
  document.getElementById('gtp-expiry-text').textContent = res.expiryLabel;
  document.getElementById('gtp-target-pax').textContent = `${res.targetPax} Pax`;
  document.getElementById('gtp-avail-tables').textContent = `${availCount} / 45`;
  document.getElementById('gtp-locked-tables').textContent = `${res.lockedTables.length} Locked`;

  if (res.isExpired) {
    const expMsg = `Access code expired (${res.expiryLabel}). Please request a fresh token.`;
    gateInput.setCustomValidity(expMsg);
    if (showErrors) {
      gateErrorEl.textContent = expMsg;
      gateErrorEl.hidden = false;
      gateInput.classList.add('is-code-error');
    }
    return null;
  }

  gateInput.classList.add('is-code-valid');
  return res;
}

gateInput.addEventListener('input', () => {
  evaluateGateCodeInput(false);
});

gateInput.addEventListener('blur', () => {
  if (gateInput.value.trim().length > 0) {
    evaluateGateCodeInput(true);
  }
});

gateForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const decoded = evaluateGateCodeInput(true);
  if (!decoded) {
    gateInput.focus();
    return;
  }
  applyAccessSession(decoded);
  setHeroShipCamera(false);
});

document.getElementById('btn-paste-code').addEventListener('click', async () => {
  try {
    const clip = await navigator.clipboard.readText();
    if (clip) {
      gateInput.value = clip.trim().toUpperCase();
      evaluateGateCodeInput(true);
      gateInput.focus();
    }
  } catch (_) {
    gateInput.focus();
  }
});

document.querySelectorAll('[data-demo-code]').forEach((chip) => {
  chip.addEventListener('click', () => {
    gateInput.value = chip.dataset.demoCode;
    evaluateGateCodeInput(true);
    gateInput.focus();
  });
});

document.getElementById('btn-change-code').addEventListener('click', () => {
  setGateStage(false);
});

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

  if (currentStage === 'gate') {
    canvas.style.cursor = 'grab';
    return;
  }

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

  if (currentStage === 'gate') return;

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
document.getElementById('btn-brand-home').addEventListener('click', () => {
  if (currentStage === 'gate') {
    animateCameraTo(new THREE.Vector3(38, 15.5, 50), new THREE.Vector3(0, 5.0, 0), 750);
  } else {
    setHeroShipCamera(false);
  }
});

document.querySelectorAll('[data-cutaway-layer]').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (currentStage === 'gate') return;
    const layer = btn.dataset.cutawayLayer;
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
  selectedTables.clear();
  for (const tNum of activeSession.recommended) {
    if (!lockedTables.has(tNum)) selectedTables.add(tNum);
  }
  syncSelectionUI();
});

document.getElementById('btn-clear-selection').addEventListener('click', () => {
  selectedTables.clear();
  syncSelectionUI();
});

document.getElementById('btn-confirm-booking').addEventListener('click', () => {
  const chosenList = TABLE_CATALOG.filter((t) => selectedTables.has(t.num));
  const totalSeats = chosenList.reduce((acc, t) => acc + t.pax, 0);
  const b1List = chosenList.filter((t) => t.block === 'B1').map((t) => `#${t.num} (${t.pax}P)`);
  const b2List = chosenList.filter((t) => t.block === 'B2').map((t) => `#${t.num} (${t.pax}P)`);
  const b3List = chosenList.filter((t) => t.block === 'B3').map((t) => `#${t.num} (${t.pax}P)`);
  const b4List = chosenList.filter((t) => t.block === 'B4').map((t) => `#${t.num} (${t.pax}P)`);

  document.getElementById('dialog-summary-content').innerHTML = `
    <div><strong>Group Name / ID:</strong> ${activeSession.groupName}</div>
    <div><strong>Access Token:</strong> <span class="summary-mono">${activeSession.code}</span> (${activeSession.expiryLabel})</div>
    <div><strong>Venue:</strong> Ristorante Arlecchino · Deck 6 Roma (4 Blocks · Port &amp; Starboard)</div>
    <div><strong>Block 1 Portside (${b1List.length}):</strong> <span class="summary-mono">${b1List.join(', ') || 'None'}</span></div>
    <div><strong>Block 2 Starboard (${b2List.length}):</strong> <span class="summary-mono">${b2List.join(', ') || 'None'}</span></div>
    <div><strong>Block 3 Portside (${b3List.length}):</strong> <span class="summary-mono">${b3List.join(', ') || 'None'}</span></div>
    <div><strong>Block 4 Starboard (${b4List.length}):</strong> <span class="summary-mono">${b4List.join(', ') || 'None'}</span></div>
    <div><strong>Total Allocated Seats:</strong> <span class="summary-mono">${totalSeats} / ${activeSession.targetPax} Pax</span> (${chosenList.length} tables)</div>
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
  updateCameraViewOffset();

  orthoCamera.left = (-orthoFrustumH * asp) / 2;
  orthoCamera.right = (orthoFrustumH * asp) / 2;
  orthoCamera.top = orthoFrustumH / 2;
  orthoCamera.bottom = -orthoFrustumH / 2;
  orthoCamera.updateProjectionMatrix();

  renderer.setSize(w, h);
  labelRenderer.setSize(w, h);
  css2dDirty = true;
});

// ============================================================================
// 10. MAIN RENDER & ANIMATION LOOP (OPTIMIZED FOR 60+ FPS PRESENTATION)
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
  const timeSec = now * 0.001;

  if (camAnim) {
    camAnim.update(now);
  }

  if (pointerDirty && !isOrbitDragging) {
    performHoverRaycast();
  }

  const w = window.innerWidth;
  targetViewOffsetX = currentStage === 'gate' && w > 960 ? Math.round(Math.min(200, w * 0.145)) : 0;
  if (Math.abs(targetViewOffsetX - currentViewOffsetX) > 0.35) {
    currentViewOffsetX += (targetViewOffsetX - currentViewOffsetX) * Math.min(1.0, dt * 8.0);
    updateCameraViewOffset();
  } else if (currentViewOffsetX !== targetViewOffsetX) {
    currentViewOffsetX = targetViewOffsetX;
    updateCameraViewOffset();
  }

  if (currentStage === 'gate' || currentStage === 'ship') {
    oceanUniforms.uTime.value = timeSec;
    marineLifeSystem.update(timeSec);

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
      css2dDirty = true;
    }
    controls.update();
  } else if (currentStage === 'interior') {
    if (currentCamMode === 'walk') {
      const speed = 3.4 * dt;
      const forwardFlat = new THREE.Vector3(-Math.sin(walkYaw), 0, -Math.cos(walkYaw));
      const rightFlat = new THREE.Vector3(Math.cos(walkYaw), 0, -Math.sin(walkYaw));

      const moved =
        walkKeys.forward || walkKeys.backward || walkKeys.right || walkKeys.left;
      if (walkKeys.forward) perspCamera.position.addScaledVector(forwardFlat, speed);
      if (walkKeys.backward) perspCamera.position.addScaledVector(forwardFlat, -speed);
      if (walkKeys.right) perspCamera.position.addScaledVector(rightFlat, speed);
      if (walkKeys.left) perspCamera.position.addScaledVector(rightFlat, -speed);

      if (moved) {
        perspCamera.position.x = Math.max(-1.85, Math.min(40.6, perspCamera.position.x));
        perspCamera.position.z = Math.max(-17.0, Math.min(-0.55, perspCamera.position.z));
        perspCamera.position.y = 1.56;
        syncWalkCameraLook();
      }
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

  // Only run CSS2DRenderer DOM layout when labels are visible and camera/state changed!
  const hasVisibleLabels =
    (currentStage === 'interior' && showTableNumbers) ||
    (currentStage === 'ship' && currentCutawayMode !== 'full');
  if (hasVisibleLabels && css2dDirty) {
    labelRenderer.render(scene, activeCamera);
    css2dDirty = false;
  }
}

requestAnimationFrame(animate);
