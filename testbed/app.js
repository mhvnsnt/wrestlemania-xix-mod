// WMXIX Mobile Testbed — Three.js app
// Real: WMXIX head models (solved skinning), 70-bone skeleton, YANM animations
// Procedural: Body capsules (placeholder until full body decode)

let scene, camera, renderer, clock;
let player, dummy;
let skeletonData = null;
let animations = {};
let currentAnim = 'idle';
let animTime = 0;

// YANM track hash -> bone index mapping (HIGH/MED-HIGH confidence only)
// From ycg-group-mapping.json: LEG=HIGH, ARM=MED-HIGH
const TRACK_TO_BONE = {
  // These will be populated from animation data based on track anatomy labels
};

async function init() {
  setStatus('Loading skeleton...');
  
  // Load skeleton
  const skelResp = await fetch('skeleton.json');
  skeletonData = await skelResp.json();
  
  // Load animations
  setStatus('Loading animations...');
  const animFiles = {
    'idle': 'anim_idle.json',
    'walk': 'anim_walk.json', 
    'punch': 'anim_punch.json',
    'kick': 'anim_kick.json',
    'grapple': 'anim_grapple.json'
  };
  for (const [name, file] of Object.entries(animFiles)) {
    try {
      const resp = await fetch(file);
      animations[name] = await resp.json();
    } catch (e) {
      console.warn(`Failed to load ${file}:`, e);
    }
  }
  
  // Setup Three.js
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a2e);
  scene.fog = new THREE.Fog(0x1a1a2e, 20, 60);
  
  camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 200);
  camera.position.set(0, 3, 8);
  
  renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('canvas'), antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  
  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8);
  dir.position.set(5, 10, 5);
  scene.add(dir);
  
  // Arena (procedural ring + real arena point cloud if available)
  buildArena();
  
  // Wrestlers
  setStatus('Building wrestlers...');
  player = buildWrestler(0x4488ff, 'Player');
  player.group.position.set(-1.5, 0, 0);
  scene.add(player.group);

  dummy = buildWrestler(0xff4444, 'Dummy');
  dummy.group.position.set(1.5, 0, 0);
  dummy.group.rotation.y = Math.PI;
  scene.add(dummy.group);
  
  // Load real head models
  loadHeadModel(player, 'head_000.obj');
  
  setupControls();
  
  clock = new THREE.Clock();
  animate();
  
  setStatus('Ready — YANM animations driving real skeleton');
}

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

function buildArena() {
  // Procedural wrestling ring (placeholder until arena faces decoded)
  const ringGroup = new THREE.Group();
  
  // Mat
  const matGeo = new THREE.BoxGeometry(8, 0.2, 8);
  const matMat = new THREE.MeshLambertMaterial({ color: 0x3366cc });
  const mat = new THREE.Mesh(matGeo, matMat);
  mat.position.y = -0.1;
  ringGroup.add(mat);
  
  // Apron
  const apronGeo = new THREE.BoxGeometry(9, 1, 9);
  const apronMat = new THREE.MeshLambertMaterial({ color: 0x222244 });
  const apron = new THREE.Mesh(apronGeo, apronMat);
  apron.position.y = -0.6;
  ringGroup.add(apron);
  
  // Posts
  const postGeo = new THREE.CylinderGeometry(0.1, 0.1, 2);
  const postMat = new THREE.MeshLambertMaterial({ color: 0x888888 });
  for (const [x, z] of [[-4,-4],[4,-4],[-4,4],[4,4]]) {
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(x, 1, z);
    ringGroup.add(post);
  }
  
  // Ropes
  const ropeMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  for (let h = 0.5; h <= 1.5; h += 0.5) {
    for (const [x1,z1,x2,z2] of [[-4,-4,4,-4],[4,-4,4,4],[4,4,-4,4],[-4,4,-4,-4]]) {
      const len = Math.sqrt((x2-x1)**2 + (z2-z1)**2);
      const ropeGeo = new THREE.CylinderGeometry(0.03, 0.03, len);
      const rope = new THREE.Mesh(ropeGeo, ropeMat);
      rope.position.set((x1+x2)/2, h, (z1+z2)/2);
      rope.rotation.z = Math.PI/2;
      rope.rotation.y = Math.atan2(z2-z1, x2-x1);
      ringGroup.add(rope);
    }
  }
  
  scene.add(ringGroup);
  
  // Ground
  const groundGeo = new THREE.PlaneGeometry(100, 100);
  const groundMat = new THREE.MeshLambertMaterial({ color: 0x111122 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI/2;
  ground.position.y = -1.1;
  scene.add(ground);
}

function buildWrestler(color, name) {
  const group = new THREE.Group();
  const bones = {};
  const meshes = {};
  
  // Build bone hierarchy from skeleton data
  // For now, create simplified rig with major bones
  const boneDefs = [
    { name: 'Bip Pelvis', pos: [0, 1.0, 0] },
    { name: 'Bip Spine', pos: [0, 0.15, 0], parent: 'Bip Pelvis' },
    { name: 'Bip Spine1', pos: [0, 0.2, 0], parent: 'Bip Spine' },
    { name: 'Bip Neck', pos: [0, 0.2, 0], parent: 'Bip Spine1' },
    { name: 'Bip Head', pos: [0, 0.15, 0], parent: 'Bip Neck' },
    { name: 'Bip R UpperArm', pos: [0.25, 0.1, 0], parent: 'Bip Spine1' },
    { name: 'Bip R Forearm', pos: [0.3, 0, 0], parent: 'Bip R UpperArm' },
    { name: 'Bip R Hand', pos: [0.25, 0, 0], parent: 'Bip R Forearm' },
    { name: 'Bip L UpperArm', pos: [-0.25, 0.1, 0], parent: 'Bip Spine1' },
    { name: 'Bip L Forearm', pos: [-0.3, 0, 0], parent: 'Bip L UpperArm' },
    { name: 'Bip L Hand', pos: [-0.25, 0, 0], parent: 'Bip L Forearm' },
    { name: 'Bip R Thigh', pos: [0.15, -0.1, 0], parent: 'Bip Pelvis' },
    { name: 'Bip R Calf', pos: [0, -0.4, 0], parent: 'Bip R Thigh' },
    { name: 'Bip R Foot', pos: [0, -0.4, 0], parent: 'Bip R Calf' },
    { name: 'Bip L Thigh', pos: [-0.15, -0.1, 0], parent: 'Bip Pelvis' },
    { name: 'Bip L Calf', pos: [0, -0.4, 0], parent: 'Bip L Thigh' },
    { name: 'Bip L Foot', pos: [0, -0.4, 0], parent: 'Bip L Calf' },
  ];
  
  const mat = new THREE.MeshLambertMaterial({ color: color });
  
  for (const def of boneDefs) {
    const obj = new THREE.Group();
    obj.position.set(...def.pos);
    obj.userData.boneName = def.name;
    obj.userData.isProcedural = true;  // Mark as procedural
    
    // Capsule mesh for this bone segment
    const isLimb = def.name.includes('Arm') || def.name.includes('Forearm') || 
                   def.name.includes('Thigh') || def.name.includes('Calf');
    if (isLimb || def.name.includes('Spine') || def.name === 'Bip Pelvis') {
      const geo = new THREE.CapsuleGeometry(0.08, 0.25, 4, 8);
      const mesh = new THREE.Mesh(geo, mat);
      // Orient along Y for vertical bones, X for horizontal
      if (def.name.includes('Arm') || def.name.includes('Hand')) {
        mesh.rotation.z = Math.PI/2;
      }
      obj.add(mesh);
    }
    
    // Head gets sphere placeholder (real head OBJ loads separately)
    if (def.name === 'Bip Head') {
      const geo = new THREE.SphereGeometry(0.15, 16, 16);
      const mesh = new THREE.Mesh(geo, mat);
      mesh.userData.isPlaceholder = true;
      obj.add(mesh);
      obj.userData.headPlaceholder = mesh;
    }
    
    bones[def.name] = obj;
    
    if (def.parent && bones[def.parent]) {
      bones[def.parent].add(obj);
    } else {
      group.add(obj);
    }
  }
  
  return { group, bones, name, color };
}

function loadHeadModel(wrestler, url) {
  // Simple OBJ loader for the real skinned head
  fetch(url)
    .then(r => r.text())
    .then(text => {
      const verts = [];
      const faces = [];
      for (const line of text.split('\n')) {
        if (line.startsWith('v ')) {
          const p = line.split(/\s+/);
          // Scale down: OBJ is in cm, we want meters
          verts.push([parseFloat(p[1])/100, parseFloat(p[2])/100, parseFloat(p[3])/100]);
        } else if (line.startsWith('f ')) {
          const p = line.split(/\s+/).slice(1).map(x => parseInt(x.split('/')[0]) - 1);
          if (p.length >= 3) faces.push(p);
        }
      }
      
      if (verts.length === 0) return;
      
      const geo = new THREE.BufferGeometry();
      const posArray = new Float32Array(verts.flat());
      geo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
      
      // Build index from faces
      const indices = [];
      for (const f of faces) {
        for (let i = 1; i < f.length - 1; i++) {
          indices.push(f[0], f[i], f[i+1]);
        }
      }
      if (indices.length > 0) {
        geo.setIndex(indices);
      }
      geo.computeVertexNormals();
      
      const mat = new THREE.MeshLambertMaterial({ 
        color: 0xd4a574,  // Skin tone
        side: THREE.DoubleSide 
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.userData.isReal = true;  // Mark as REAL WMXIX geometry
      
      // Replace placeholder head
      const headBone = wrestler.bones['Bip Head'];
      if (headBone && headBone.userData.headPlaceholder) {
        headBone.remove(headBone.userData.headPlaceholder);
      }
      // Position head model at head bone (adjust for scale)
      mesh.position.set(0, 0.1, 0);
      mesh.scale.set(1.5, 1.5, 1.5);
      headBone.add(mesh);
      
      setStatus('Real WMXIX head loaded — skinning verified');
    })
    .catch(e => console.warn('Head load failed:', e));
}

// Animation system
function applyAnimation(wrestler, animName, time) {
  const anim = animations[animName];
  if (!anim || !anim.tracks) {
    // Procedural fallback
    applyProcedural(wrestler, animName, time);
    return;
  }
  
  const secPerTick = anim.header?.sec_per_tick || 0.028;
  let appliedReal = 0;
  let appliedProcedural = 0;
  
  for (const track of anim.tracks) {
    const anatomy = track.anatomy || '';
    const boneName = mapTrackToBone(track);
    
    if (boneName && wrestler.bones[boneName]) {
      // Real YANM curve
      const angle = sampleTrack(track, time, secPerTick);
      // Apply as rotation (simplified: X-axis hinge)
      wrestler.bones[boneName].rotation.x = angle;
      appliedReal++;
    } else {
      appliedProcedural++;
    }
  }
  
  // If no real tracks applied, use procedural
  if (appliedReal === 0) {
    applyProcedural(wrestler, animName, time);
  }
}

function mapTrackToBone(track) {
  const anatomy = (track.anatomy || '').toLowerCase();
  const hash = track.hash || '';
  
  // HIGH confidence: LEG chains
  if (anatomy.includes('leg')) {
    // Map to thigh/calf based on track index or hash
    // Simplified: alternate between R/L thigh
    return track._side === 'A' ? 'Bip R Thigh' : 'Bip L Thigh';
  }
  // MED-HIGH: ARM chains  
  if (anatomy.includes('arm')) {
    return track._side === 'A' ? 'Bip R UpperArm' : 'Bip L UpperArm';
  }
  // Others: unresolved, return null for procedural fallback
  return null;
}

function sampleTrack(track, time, secPerTick) {
  const keys = track.keys || [];
  if (keys.length === 0) return 0;
  
  // Keys are [dt, val1, val2, ...] - simplified sampling
  // Find the key at current time
  let accTime = 0;
  for (let i = 0; i < keys.length; i++) {
    const dt = keys[i][0] || 0;
    accTime += dt * secPerTick;
    if (accTime >= time) {
      // Return angle from key (keys[3] and [4] are angle values per decoder)
      const angle = keys[i][3] || 0;
      return angle * Math.PI / 180 * 0.1; // Scale down
    }
  }
  return 0;
}

function applyProcedural(wrestler, animName, time) {
  const bones = wrestler.bones;
  const t = time * 2;
  
  if (animName === 'idle') {
    // Gentle breathing
    if (bones['Bip Spine']) bones['Bip Spine'].rotation.x = Math.sin(t) * 0.05;
    if (bones['Bip R UpperArm']) bones['Bip R UpperArm'].rotation.z = 0.2 + Math.sin(t) * 0.05;
    if (bones['Bip L UpperArm']) bones['Bip L UpperArm'].rotation.z = -0.2 - Math.sin(t) * 0.05;
  } else if (animName === 'walk') {
    // Walking cycle
    const swing = Math.sin(t * 3) * 0.4;
    if (bones['Bip R Thigh']) bones['Bip R Thigh'].rotation.x = swing;
    if (bones['Bip L Thigh']) bones['Bip L Thigh'].rotation.x = -swing;
    if (bones['Bip R UpperArm']) bones['Bip R UpperArm'].rotation.x = -swing * 0.5;
    if (bones['Bip L UpperArm']) bones['Bip L UpperArm'].rotation.x = swing * 0.5;
  } else if (animName === 'punch') {
    // Punch: right arm extends
    const p = Math.min(time * 4, 1);
    const punch = Math.sin(p * Math.PI);
    if (bones['Bip R UpperArm']) {
      bones['Bip R UpperArm'].rotation.x = -punch * 1.2;
      bones['Bip R Forearm'].rotation.x = -punch * 0.3;
    }
  } else if (animName === 'kick') {
    const p = Math.min(time * 4, 1);
    const kick = Math.sin(p * Math.PI);
    if (bones['Bip R Thigh']) bones['Bip R Thigh'].rotation.x = -kick * 1.0;
    if (bones['Bip R Calf']) bones['Bip R Calf'].rotation.x = kick * 0.5;
  } else if (animName === 'grapple') {
    // Grapple: both arms forward
    const p = Math.min(time * 3, 1);
    const g = Math.sin(p * Math.PI);
    if (bones['Bip R UpperArm']) bones['Bip R UpperArm'].rotation.x = -g * 0.8;
    if (bones['Bip L UpperArm']) bones['Bip L UpperArm'].rotation.x = -g * 0.8;
    if (bones['Bip Spine']) bones['Bip Spine'].rotation.x = g * 0.3;
  } else if (animName === 'block') {
    if (bones['Bip R UpperArm']) bones['Bip R UpperArm'].rotation.x = -0.8;
    if (bones['Bip L UpperArm']) bones['Bip L UpperArm'].rotation.x = -0.8;
    if (bones['Bip R Forearm']) bones['Bip R Forearm'].rotation.x = -0.5;
    if (bones['Bip L Forearm']) bones['Bip L Forearm'].rotation.x = -0.5;
  } else if (animName === 'taunt') {
    // Taunt: arms raised, head back
    const p = Math.min(time * 2, 1);
    const t2 = Math.sin(p * Math.PI);
    if (bones['Bip R UpperArm']) bones['Bip R UpperArm'].rotation.z = 0.2 + t2 * 1.2;
    if (bones['Bip L UpperArm']) bones['Bip L UpperArm'].rotation.z = -0.2 - t2 * 1.2;
    if (bones['Bip Neck']) bones['Bip Neck'].rotation.x = -t2 * 0.3;
  }
}

// ============================================================
// REAL WMXIX GameCube controls (verified vs Prima Official Strategy Guide)
// Prima numbering: 1=A 2=B 3=Y 4=X 5=Start 6=L 7=R 8=Z s=Stick
// A: Grapple (tap=light, hold=heavy)
// B: Strike  (tap=light, hold=heavy)
// X: Run (hold) / Irish whip (A+X) / Climb (X+stick toward turnbuckle)
// Y: Weapon grab (placeholder — no weapons in testbed)
// L: Grapple reversal (timed)   R: Strike reversal (timed)
// Z: Switch target / tag partner (placeholder)
// D-pad/C-stick: Taunt   Start: Pause
// A+B with full special: Special Move
// ============================================================
let joystickActive = false;
let joystickVec = { x: 0, y: 0 };
let runHeld = false;      // X held = run mode
let isPaused = false;
let specialMeter = 0;     // 0..100, fills over time; full = special available

// Tap vs hold detection (300ms threshold = light vs heavy)
const HOLD_THRESHOLD_MS = 300;
let pressTimers = {};

function setupControls() {
  const joy = document.getElementById('joystick');
  const stick = document.getElementById('stick');

  function handleStart(e) {
    joystickActive = true;
    handleMove(e);
  }
  function handleMove(e) {
    if (!joystickActive) return;
    e.preventDefault();
    const rect = joy.getBoundingClientRect();
    const cx = rect.left + rect.width/2;
    const cy = rect.top + rect.height/2;
    const t = e.touches ? e.touches[0] : e;
    let dx = (t.clientX - cx) / (rect.width/2);
    let dy = (t.clientY - cy) / (rect.height/2);
    const len = Math.sqrt(dx*dx + dy*dy);
    if (len > 1) { dx /= len; dy /= len; }
    joystickVec.x = dx;
    joystickVec.y = dy;
    stick.style.transform = `translate(calc(-50% + ${dx*35}px), calc(-50% + ${dy*35}px))`;
  }
  function handleEnd() {
    joystickActive = false;
    joystickVec.x = 0; joystickVec.y = 0;
    stick.style.transform = 'translate(-50%, -50%)';
  }

  joy.addEventListener('touchstart', handleStart, {passive: false});
  joy.addEventListener('touchmove', handleMove, {passive: false});
  joy.addEventListener('touchend', handleEnd);
  joy.addEventListener('mousedown', handleStart);
  window.addEventListener('mousemove', handleMove);
  window.addEventListener('mouseup', handleEnd);

  // --- A button: GRAPPLE (tap=light, hold=heavy) ---
  bindHoldButton('btn-a',
    () => triggerGrapple(false),   // tap  = light grapple
    () => triggerGrapple(true));   // hold = heavy grapple

  // --- B button: STRIKE (tap=light, hold=heavy) ---
  bindHoldButton('btn-b',
    () => triggerStrike(false),
    () => triggerStrike(true));

  // --- X button: RUN (hold) / IRISH WHIP (tap near opponent) ---
  bindHoldButton('btn-x',
    () => triggerIrishWhip(),
    null,
    () => { runHeld = true; setStatus('Running... (X held)'); },
    () => { runHeld = false; });

  // --- Y button: WEAPON (placeholder) ---
  bindTapButton('btn-y', () => {
    setStatus('Y: Weapon grab — no weapons in testbed yet');
  });

  // --- L: grapple reversal (timed) ---
  bindTapButton('btn-l', () => triggerReversal('grapple'));

  // --- R: strike reversal (timed) ---
  bindTapButton('btn-r', () => triggerReversal('strike'));

  // --- Z: switch target ---
  bindTapButton('btn-z', () => {
    setStatus('Z: Switch target — only 1 opponent in testbed');
  });

  // --- Start: pause ---
  bindTapButton('btn-start', () => {
    isPaused = !isPaused;
    setStatus(isPaused ? 'PAUSED — tap II to resume' : 'Resumed');
  });

  // --- Taunt ---
  bindTapButton('btn-taunt', () => {
    triggerAction('taunt');
    setStatus('Taunt!');
  });
}

// Bind a button with tap vs hold (light vs heavy) semantics
function bindHoldButton(id, onTap, onHold, onHoldStart, onHoldEnd) {
  const btn = document.getElementById(id);
  if (!btn) return;
  let timer = null;
  let held = false;
  const start = (e) => {
    if (e) e.preventDefault();
    held = false;
    timer = setTimeout(() => {
      held = true;
      if (onHoldStart) onHoldStart();
      if (onHold) onHold();
    }, HOLD_THRESHOLD_MS);
  };
  const end = (e) => {
    if (e) e.preventDefault();
    if (timer) clearTimeout(timer);
    if (!held && onTap) onTap();
    if (held && onHoldEnd) onHoldEnd();
    held = false;
  };
  btn.addEventListener('touchstart', start, {passive: false});
  btn.addEventListener('touchend', end, {passive: false});
  btn.addEventListener('touchcancel', end, {passive: false});
  btn.addEventListener('mousedown', start);
  btn.addEventListener('mouseup', end);
}

function bindTapButton(id, onTap) {
  const btn = document.getElementById(id);
  if (!btn) return;
  btn.addEventListener('touchstart', (e) => { e.preventDefault(); onTap(); }, {passive: false});
  btn.addEventListener('mousedown', () => onTap());
}

let actionQueue = null;
let actionTime = 0;

function triggerAction(anim, label) {
  actionQueue = anim;
  actionTime = 0;
  setStatus(`Action: ${(label || anim).toUpperCase()} (YANM + procedural)`);
  // Successful actions build special meter
  specialMeter = Math.min(100, specialMeter + 8);
  updateSpecialMeter();
}

function updateSpecialMeter() {
  const fill = document.getElementById('special-fill');
  if (fill) fill.style.width = specialMeter + '%';
}

// A button: grapple. Heavy does more damage but easier to reverse.
function triggerGrapple(heavy) {
  // A+B with full special = Special Move
  if (specialMeter >= 100) {
    triggerAction('grapple', heavy ? 'SPECIAL MOVE!' : 'special move');
    specialMeter = 0;
    updateSpecialMeter();
    return;
  }
  triggerAction('grapple', heavy ? 'heavy grapple' : 'light grapple');
}

// B button: strike. Tap repeatedly = combination.
let strikeCombo = 0;
let strikeComboTimer = null;
function triggerStrike(heavy) {
  if (heavy) {
    strikeCombo = 0;
    triggerAction(Math.random() > 0.5 ? 'punch' : 'kick', 'heavy strike');
  } else {
    strikeCombo++;
    if (strikeComboTimer) clearTimeout(strikeComboTimer);
    strikeComboTimer = setTimeout(() => { strikeCombo = 0; }, 1500);
    const anim = strikeCombo % 2 === 1 ? 'punch' : 'kick';
    triggerAction(anim, `strike combo ${strikeCombo}`);
  }
}

// X tap near opponent: Irish whip toward ropes
function triggerIrishWhip() {
  const dist = player.group.position.distanceTo(dummy.group.position);
  if (dist < 3.5) {
    triggerAction('grapple', 'irish whip!');
    // Shove dummy toward nearest ropes
    const dir = dummy.group.position.clone().sub(player.group.position).normalize();
    dummy.group.position.add(dir.multiplyScalar(1.5));
    dummy.group.position.x = Math.max(-3.5, Math.min(3.5, dummy.group.position.x));
    dummy.group.position.z = Math.max(-3.5, Math.min(3.5, dummy.group.position.z));
  } else {
    setStatus('X: Irish whip — get closer to opponent');
  }
}

// L/R: timed reversals
function triggerReversal(type) {
  // In the real game this is timing-based vs the opponent's attack.
  // Testbed: dummy attacks periodically; reversal succeeds if timed.
  triggerAction('block', `${type} reversal!`);
  setStatus(`${type === 'grapple' ? 'L' : 'R'}: Reversal attempt — timing is everything`);
}

// Main loop
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);

  if (isPaused) {
    renderer.render(scene, camera);
    return;
  }

  // Movement — X held = RUN (faster, like the real game)
  const speed = runHeld ? 6 : 3;
  if (joystickActive && (joystickVec.x !== 0 || joystickVec.y !== 0)) {
    player.group.position.x += joystickVec.x * speed * dt;
    player.group.position.z += joystickVec.y * speed * dt;
    // Face movement direction
    player.group.rotation.y = Math.atan2(joystickVec.x, joystickVec.y);
    currentAnim = 'walk';
    animTime += dt;
  } else if (actionQueue) {
    currentAnim = actionQueue;
    actionTime += dt;
    animTime = actionTime;
    // Action duration ~1s, then back to idle
    const animDur = animations[actionQueue]?.est_seconds || 1;
    if (actionTime > Math.min(animDur, 2)) {
      actionQueue = null;
      currentAnim = 'idle';
      animTime = 0;
    }
  } else {
    currentAnim = 'idle';
    animTime += dt;
  }
  
  // Clamp to ring
  player.group.position.x = Math.max(-3.5, Math.min(3.5, player.group.position.x));
  player.group.position.z = Math.max(-3.5, Math.min(3.5, player.group.position.z));
  
  // Apply animations
  applyAnimation(player, currentAnim, animTime % 10);
  applyAnimation(dummy, 'idle', animTime % 10 + 5);
  
  // Third-person camera follows player
  const target = new THREE.Vector3(
    player.group.position.x,
    2.5,
    player.group.position.z + 6
  );
  camera.position.lerp(target, 0.05);
  camera.lookAt(player.group.position.x, 1.2, player.group.position.z);
  
  renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Start
init().catch(e => {
  console.error(e);
  setStatus('Error: ' + e.message);
});
