import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

const ROOM_MAPPING = {
  'L1-B1': 'L1-A1',
  'L1-T1': 'L1-A2',
  'L1-B2': 'L1-A3',
  'L1-T2': 'L1-A4',
  'L1-B3': 'L1-A5',
  'L1-T3': 'L1-A6',
  'L1-B4': 'L1-A7',
  'L1-T4': 'L1-A8',
  'L1-B5': 'L1-A9',
  'L1-T5': 'L1-A10',
  'L1-B6': 'L1-A11',
  'L1-B7': 'L1-A12',
};

function normalizeRoomId(rawId) {
  if (!rawId) return null;
  const match = String(rawId).match(/(L1-[TB]\d|A1\d{2})/i);
  if (!match) return null;
  const id = match[1].toUpperCase();
  if (id.startsWith('A')) return `L1-A${parseInt(id.slice(1)) - 100}`;
  return ROOM_MAPPING[id] || id;
}

function getFloorIndex(object) {
  let current = object;
  while (current) {
    if (current.userData && current.userData.floorIndex) return current.userData.floorIndex;
    current = current.parent;
  }
  return 1;
}

function getRoomIdFromObject(object, fallbackRoomId) {
  let current = object;
  while (current) {
    const matched = normalizeRoomId(current.userData?.roomIdMatch || current.userData?.name || current.name);
    if (matched) return matched.replace('L1', `L${getFloorIndex(current)}`);
    current = current.parent;
  }
  return fallbackRoomId;
}

function getSensorText(sensor) {
  if (!sensor) return 'No sensor data';
  const parts = [];
  if (sensor.temp !== undefined) parts.push(`Temp: ${Number(sensor.temp).toFixed(1)}°C`);
  if (sensor.humidity !== undefined) parts.push(`Hum: ${Number(sensor.humidity).toFixed(1)}%`);
  if (sensor.co2 !== undefined) parts.push(`CO2: ${Number(sensor.co2).toFixed(0)}ppm`);
  if (sensor.smoke !== undefined) parts.push(`Smoke: ${Number(sensor.smoke).toFixed(1)}%`);
  if (sensor.energy !== undefined) parts.push(`Energy: ${sensor.energy}`);
  if (sensor.device_status) parts.push(`Status: ${sensor.device_status}`);
  return parts.length ? parts.join(' | ') : 'No sensor data';
}

function getSensorStatus(sensor) {
  if (!sensor) return 'NORMAL';
  const smoke = sensor.smoke_status !== undefined ? sensor.smoke_status : (sensor.smoke || 0);
  const status = String(sensor.device_status || sensor.status || '').toUpperCase();
  if (status === 'CRITICAL' || status === 'ERROR' || status === 'FIRE') return 'CRITICAL';
  if (status === 'WARNING') return 'WARNING';
  if (sensor.temp >= 40 || smoke >= 1 || sensor.co2 >= 1000) return 'CRITICAL';
  if (sensor.temp >= 32 || smoke >= 0.5 || sensor.co2 >= 631) return 'WARNING';
  return 'NORMAL';
}

export default function ThreeScene({ activeRoomId, onRoomClick, sensorData }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const overallModelRef = useRef(null);
  const activeSubModelRef = useRef(null);
  const cameraRef = useRef(null);
  const raycasterRef = useRef(null);
  const mouseRef = useRef(new THREE.Vector2());
  const activeRoomIdRef = useRef(activeRoomId);
  const onRoomClickRef = useRef(onRoomClick);
  const sensorDataRef = useRef(sensorData);
  const [hoverInfo, setHoverInfo] = useState(null);

  useEffect(() => {
    activeRoomIdRef.current = activeRoomId;
  }, [activeRoomId]);

  useEffect(() => {
    onRoomClickRef.current = onRoomClick;
  }, [onRoomClick]);

  useEffect(() => {
    sensorDataRef.current = sensorData;
  }, [sensorData]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // --- Init Scene ---
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x111827);
    
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    cameraRef.current = camera;
    camera.position.set(0, 75, 90); // Zoom in ~20-25% closer/larger

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.6; // Auto-rotate slowly

    let autoRotateTimer = null;
    const pauseAutoRotate = () => {
      controls.autoRotate = false;
      if (autoRotateTimer) clearTimeout(autoRotateTimer);
      autoRotateTimer = setTimeout(() => {
        controls.autoRotate = true;
      }, 2000); // Pause rotation for 2 seconds on interaction
    };

    controls.addEventListener('start', pauseAutoRotate);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(50, 100, 50);
    scene.add(dirLight);

    // Assembly
    const overallGroup = new THREE.Group();
    scene.add(overallGroup);
    overallModelRef.current = overallGroup;

    const floorsToLoad = [
      { file: '/mohinh/Tang/Tang_0.glb', y: 0 },
      { file: '/mohinh/Tang/Tang_1.glb', y: 4 },
      { file: '/mohinh/Tang/Tang_2.glb', y: 8 },
      { file: '/mohinh/Tang/Tang_3.glb', y: 12 },
      { file: '/mohinh/Tang/Tang_4.glb', y: 16 }
    ];

    const loader = new GLTFLoader();
    floorsToLoad.forEach(floor => {
      loader.load(floor.file, (gltf) => {
        const floorMesh = gltf.scene;
        floorMesh.position.y = floor.y;
        const floorIndex = Math.round(floor.y / 4) + 1;
        floorMesh.userData.floorIndex = floorIndex;
        
        floorMesh.traverse((child) => {
          if (child.name && child.name.match(/(L1-[TB]\d|A10\d)/i)) {
            child.userData.roomIdMatch = child.name;
          }
          if (child.parent && child.parent.userData && child.parent.userData.roomIdMatch) {
            child.userData.roomIdMatch = child.parent.userData.roomIdMatch;
          }
          
          if (child.isMesh) {
            child.userData.name = child.userData.roomIdMatch || child.name;
            if (child.material) {
              let materials = Array.isArray(child.material) ? child.material : [child.material];
              materials.forEach((mat, idx) => {
                if (mat && mat.color) {
                  let cKey = `originalColor_${idx}`;
                  if (child.userData[cKey] === undefined) child.userData[cKey] = mat.color.getHex();
                }
              });
            }
          }
        });

        overallGroup.add(floorMesh);
      });
    });

    // Raycaster
    const raycaster = new THREE.Raycaster();
    raycasterRef.current = raycaster;
    const mouse = new THREE.Vector2();
    mouseRef.current = mouse;

    const onMouseClick = (event) => {
      pauseAutoRotate();
      if (activeRoomIdRef.current) return;
      
      const rect = container.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      if (overallModelRef.current) {
        const intersects = raycaster.intersectObject(overallModelRef.current, true);
        if (intersects.length > 0) {
          let currentObj = intersects[0].object;
          let floorIdx = getFloorIndex(currentObj);
          
          let roomId = getRoomIdFromObject(currentObj, null);
          if (!roomId) {
            const point = intersects[0].point;
            const isTopRow = point.z < 0;
            const idx = Math.max(1, Math.min(6, Math.round(point.x / 12) + 3));
            let rawRoom = `L1-${isTopRow ? 'T' : 'B'}${idx}`;
            roomId = (ROOM_MAPPING[rawRoom] || 'L1-A1').replace('L1', `L${floorIdx}`);
          }

          if (roomId && onRoomClickRef.current) {
            onRoomClickRef.current(roomId, floorIdx);
          }
        }
      }
    };

    const onMouseMove = (event) => {
      const target = overallModelRef.current && !activeRoomIdRef.current
        ? overallModelRef.current
        : activeSubModelRef.current;
      if (!target || !raycasterRef.current || !cameraRef.current) {
        setHoverInfo(null);
        return;
      }

      const rect = container.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
      raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current);

      const intersects = raycasterRef.current.intersectObject(target, true);
      if (!intersects.length) {
        setHoverInfo(null);
        return;
      }

      const hit = intersects[0];
      const roomId = getRoomIdFromObject(hit.object, activeRoomIdRef.current);
      const deviceId = hit.object.userData?.name || hit.object.name || 'Unknown device';
      const sensor = roomId ? sensorDataRef.current[roomId] : null;
      const status = getSensorStatus(sensor);

      setHoverInfo({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        roomId: roomId || 'Unknown room',
        deviceId,
        floor: getFloorIndex(hit.object),
        sensorText: getSensorText(sensor),
        status
      });
    };

    const onMouseLeave = () => setHoverInfo(null);

    container.addEventListener('click', onMouseClick);
    container.addEventListener('mousemove', onMouseMove);
    container.addEventListener('mouseleave', onMouseLeave);

    // Animation loop
    let reqId;
    const animate = () => {
      reqId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('click', onMouseClick);
      container.removeEventListener('mousemove', onMouseMove);
      container.removeEventListener('mouseleave', onMouseLeave);
      if (autoRotateTimer) clearTimeout(autoRotateTimer);
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Handle Mode Change (Building vs Room)
  useEffect(() => {
    if (!sceneRef.current || !cameraRef.current) return;
    
    const camera = cameraRef.current;
    
    if (activeRoomId) {
      if (overallModelRef.current) overallModelRef.current.visible = false;
      
      const loader = new GLTFLoader();
      loader.load(`/mohinh/Phong/Phong_${activeRoomId}.glb`, (gltf) => {
        if (activeSubModelRef.current) {
          sceneRef.current.remove(activeSubModelRef.current);
        }
        
        const subModel = gltf.scene;
        activeSubModelRef.current = subModel;
        
        const box = new THREE.Box3().setFromObject(subModel);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        subModel.position.sub(center);
        
        sceneRef.current.add(subModel);
        
        setTimeout(() => {
          const maxDim = Math.max(size.x, size.y, size.z);
          const fov = 45;
          const distance = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(fov / 2)));
          camera.position.set(0, distance * 0.8, distance * 1.5);
          camera.lookAt(0, 0, 0);
        }, 100);
      });
    } else {
      if (overallModelRef.current) overallModelRef.current.visible = true;
      if (activeSubModelRef.current) {
        sceneRef.current.remove(activeSubModelRef.current);
        activeSubModelRef.current = null;
      }
      
      setTimeout(() => {
        camera.position.set(0, 75, 90);
        camera.lookAt(0, 8, 0);
      }, 100);
    }
  }, [activeRoomId]);

  // Handle Colors Sync
  useEffect(() => {
    if (!overallModelRef.current && !activeSubModelRef.current) return;
    
    const applyColor = (model) => {
      let blink = (Math.sin(Date.now() * 0.005) + 1) / 2;

      model.traverse((child) => {
        if (child.isMesh && child.material) {
          const roomId = getRoomIdFromObject(child, activeRoomIdRef.current);
          const sensor = roomId ? sensorDataRef.current[roomId] : null;
          const status = getSensorStatus(sensor);

          let materials = Array.isArray(child.material) ? child.material : [child.material];
          materials.forEach((mat, idx) => {
            let cKey = `originalColor_${idx}`;
            if (child.userData[cKey] !== undefined) {
              if (status === 'CRITICAL') {
                const targetColor = new THREE.Color(0xff0000);
                mat.color.lerpColors(new THREE.Color(child.userData[cKey]), targetColor, blink);
              } else if (status === 'WARNING') {
                const targetColor = new THREE.Color(0xffaa00);
                mat.color.lerpColors(new THREE.Color(child.userData[cKey]), targetColor, blink * 0.7);
              } else {
                mat.color.setHex(child.userData[cKey]);
              }
            }
          });
        }
      });
    };

    let frameId;
    const updateColors = () => {
      if (overallModelRef.current && overallModelRef.current.visible) {
        applyColor(overallModelRef.current);
      }
      if (activeSubModelRef.current && activeSubModelRef.current.visible !== false) {
        applyColor(activeSubModelRef.current);
      }
      frameId = requestAnimationFrame(updateColors);
    };

    updateColors();
    return () => cancelAnimationFrame(frameId);
  }, [sensorData]);

  return (
    <div className="relative w-full h-full" ref={mountRef}>
      {hoverInfo && (
        <div
          className="absolute z-50 pointer-events-none p-3 rounded-lg shadow-xl bg-zinc-950/90 border border-zinc-700 text-xs font-mono backdrop-blur-md"
          style={{
            left: Math.min(hoverInfo.x + 15, window.innerWidth - 240),
            top: Math.min(hoverInfo.y + 15, window.innerHeight - 150)
          }}
        >
          <div className="font-bold text-white mb-1 flex items-center justify-between gap-2 border-b border-zinc-800 pb-1">
            <span>{hoverInfo.roomId}</span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] ${
                hoverInfo.status === 'CRITICAL'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                  : hoverInfo.status === 'WARNING'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              }`}
            >
              {hoverInfo.status}
            </span>
          </div>
          <div className="text-zinc-400 text-[11px] mb-1">
            Object: <span className="text-zinc-200">{hoverInfo.deviceId}</span>
          </div>
          <div className="text-zinc-300 text-[11px]">
            {hoverInfo.sensorText}
          </div>
        </div>
      )}
    </div>
  );
}