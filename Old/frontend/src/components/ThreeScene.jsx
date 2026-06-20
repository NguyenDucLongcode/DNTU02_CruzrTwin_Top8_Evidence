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
  const match = String(rawId).match(/(L1-[TB]\d|A10\d)/i);
  if (!match) return null;
  const id = match[1].toUpperCase();
  return id.startsWith('A') ? id : (ROOM_MAPPING[id] || id);
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
  if (!sensor) return 'Chưa có dữ liệu cảm biến';
  const parts = [];
  if (sensor.temp !== undefined) parts.push(`Temp: ${Number(sensor.temp).toFixed(1)}°C`);
  if (sensor.smoke !== undefined) parts.push(`Smoke: ${Number(sensor.smoke).toFixed(1)}%`);
  if (sensor.co2 !== undefined) parts.push(`CO2: ${Number(sensor.co2).toFixed(0)}ppm`);
  if (sensor.presence !== undefined) parts.push(`Presence: ${sensor.presence ? 'Có người' : 'Trống'}`);
  return parts.length ? parts.join(' | ') : 'Chưa có dữ liệu cảm biến';
}

function getSensorStatus(sensor) {
  if (!sensor) return 'NORMAL';
  if (sensor.temp >= 40 || sensor.smoke >= 1 || sensor.co2 >= 1000) return 'CRITICAL';
  if (sensor.temp >= 32 || sensor.co2 >= 631) return 'WARNING';
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
    
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    cameraRef.current = camera;
    camera.position.set(0, 100, 120);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(50, 100, 50);
    scene.add(dirLight);
    
    // Grid Helper
    const grid = new THREE.GridHelper(200, 40, 0x0044ff, 0x001133);
    grid.position.y = -0.1;
    scene.add(grid);

    // Lắp ráp mô hình tổng từ các file Tầng
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
        
        // Retain original colors in userData for blinking effect
        // Traverse top-down to inherit room IDs
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
      if (activeRoomIdRef.current) return; // Prevent clicking if already in room view
      
      const rect = container.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      if (overallModelRef.current) {
        const intersects = raycaster.intersectObject(overallModelRef.current, true);
        if (intersects.length > 0) {
          const point = intersects[0].point;
          let currentObj = intersects[0].object;
          let floorIdx = 1;
          while(currentObj) {
            if (currentObj.userData && currentObj.userData.floorIndex) {
              floorIdx = currentObj.userData.floorIndex;
              break;
            }
            currentObj = currentObj.parent;
          }
          
          const isTopRow = point.z < 0;
          const idx = Math.round(point.x / 12) + 3;
          
          let objName = (intersects[0].object.userData && intersects[0].object.userData.name) ? intersects[0].object.userData.name : intersects[0].object.name;
          let extractedId = null;
          if (objName) {
            const match = objName.match(/(L1-[TB]\d)/i);
            if (match) extractedId = match[1].toUpperCase();
          }

          let rawRoom = extractedId || `L1-${isTopRow ? 'T' : 'B'}${idx}`;
          let actualRoomId = ROOM_MAPPING[rawRoom] || 'L1-A1'; // Fallback to L1-A1
          actualRoomId = actualRoomId.replace('L1', `L${floorIdx}`);

          onRoomClickRef.current(actualRoomId, floorIdx);
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
      container.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []); // Run once

  // Handle Mode Change (Building vs Room)
  useEffect(() => {
    if (!sceneRef.current) return;
    
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
        subModel.position.sub(center);
        
        sceneRef.current.add(subModel);
      });
    } else {
      if (overallModelRef.current) overallModelRef.current.visible = true;
      if (activeSubModelRef.current) {
        sceneRef.current.remove(activeSubModelRef.current);
        activeSubModelRef.current = null;
      }
    }
  }, [activeRoomId]);

  // Handle Colors Sync
  useEffect(() => {
    if (!overallModelRef.current && !activeSubModelRef.current) return;
    
    const applyColor = (model, checkUserData = true) => {
      let blink = (Math.sin(Date.now() * 0.005) + 1) / 2; // 0 -> 1

      model.traverse((child) => {
        if (child.isMesh && child.material) {
          let roomId = null;
          
          if (checkUserData && child.userData.name) {
            const match = child.userData.name.match(/(L1-[TB]\d|A10\d)/i);
            if (match) {
              const raw = match[1].toUpperCase();
              roomId = ROOM_MAPPING[raw] || raw;
              
              // Get floor index from object ancestry
              let cur = child;
              let fIdx = 1;
              while(cur) {
                if(cur.userData && cur.userData.floorIndex) { fIdx = cur.userData.floorIndex; break; }
                cur = cur.parent;
              }
              roomId = roomId.replace('L1', `L${fIdx}`);
            }
          } else if (!checkUserData) {
            roomId = activeRoomId;
          }

          if (roomId && sensorData[roomId]) {
            const sensor = sensorData[roomId];
            let materials = Array.isArray(child.material) ? child.material : [child.material];

            materials.forEach((mat, idx) => {
              let cKey = `originalColor_${idx}`;
              if (child.userData[cKey] !== undefined) {
                let baseColor = new THREE.Color(child.userData[cKey]);
                let targetColor = new THREE.Color();

                if (sensor.temp >= 40 || sensor.smoke >= 1 || sensor.co2 >= 1000) {
                  targetColor.setHex(0xff0000); // Đỏ cháy
                  mat.color.copy(baseColor).lerp(targetColor, 0.6 + 0.4 * blink); // Nhấp nháy mạnh
                } else if (sensor.presence === 1) {
                  targetColor.setHex(0x00ff00); // Xanh lá
                  mat.color.copy(baseColor).lerp(targetColor, 0.5); 
                } else {
                  mat.color.copy(baseColor);
                }
              }
            });
          }
        }
      });
    };

    let reqId;
    const animateColors = () => {
      if (overallModelRef.current && !activeRoomId) {
        applyColor(overallModelRef.current, true);
      }
      if (activeSubModelRef.current && activeRoomId) {
        applyColor(activeSubModelRef.current, false);
      }
      reqId = requestAnimationFrame(animateColors);
    };
    animateColors();

    return () => cancelAnimationFrame(reqId);
  }, [sensorData, activeRoomId]);

  return (
    <div ref={mountRef} className="relative w-full h-[65%] md:h-full cursor-crosshair">
      {hoverInfo && (
        <div
          className="pointer-events-none absolute z-50 max-w-[260px] rounded-lg border border-zinc-700 bg-black/90 p-3 text-[10px] leading-relaxed text-zinc-100 shadow-2xl backdrop-blur"
          style={{ left: Math.min(hoverInfo.x + 14, window.innerWidth - 280), top: Math.min(hoverInfo.y + 14, window.innerHeight - 140) }}
        >
          <div className="mb-1 text-[11px] font-bold text-blue-300">
            {hoverInfo.deviceId}
          </div>
          <div>Phòng: <span className="text-emerald-300">{hoverInfo.roomId}</span></div>
          <div>Tầng: {hoverInfo.floor}</div>
          <div>Trạng thái: <span className={hoverInfo.status === 'CRITICAL' ? 'text-red-400 font-bold' : hoverInfo.status === 'WARNING' ? 'text-amber-300 font-bold' : 'text-emerald-300'}>{hoverInfo.status}</span></div>
          <div className="mt-1 text-zinc-300">{hoverInfo.sensorText}</div>
        </div>
      )}
    </div>
  );
}
