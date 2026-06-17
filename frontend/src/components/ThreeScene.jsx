import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

const ROOM_MAPPING = {
  'L1-B1': 'L1-A1',
  'L1-T1': 'L1-A2',
  'L1-B2': 'L1-A3',
  'L1-T2': 'L1-A4',
  'L1-B3': 'L1-A5',
};

export default function ThreeScene({ activeRoomId, activeFloorIdx, onRoomClick, sensorData }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const overallModelRef = useRef(null);
  const activeSubModelRef = useRef(null);
  const isAutoPopsUpBlocked = useRef(false);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // --- Init Scene ---
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
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

    floorsToLoad.forEach(floor => {
      loader.load(floor.file, (gltf) => {
        const floorMesh = gltf.scene;
        floorMesh.position.y = floor.y;
        
        // Retain original colors in userData for blinking effect
        floorMesh.traverse((child) => {
          if (child.isMesh) {
            if (!child.userData.name) {
               child.userData.name = child.name;
            }
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
    const mouse = new THREE.Vector2();

    const onMouseClick = (event) => {
      if (activeRoomId) return; // Prevent clicking if already in room view
      
      const rect = container.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      if (overallModelRef.current) {
        const intersects = raycaster.intersectObject(overallModelRef.current, true);
        if (intersects.length > 0) {
          const point = intersects[0].point;
          const floorIdx = Math.round(point.y / 4);
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

          onRoomClick(actualRoomId, floorIdx);
        }
      }
    };

    container.addEventListener('click', onMouseClick);

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

                if (sensor.temp >= 40 || sensor.smoke > 50 || sensor.co2 >= 1000) {
                  targetColor.setHex(0xff0000); // Đỏ cháy
                  mat.color.copy(baseColor).lerp(targetColor, 0.6 + 0.4 * blink); // Nhấp nháy mạnh
                  
                  if (checkUserData && !activeRoomId && !isAutoPopsUpBlocked.current) {
                    isAutoPopsUpBlocked.current = true;
                    onRoomClick(roomId, 0);
                    setTimeout(() => { isAutoPopsUpBlocked.current = false; }, 15000);
                  }
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
  }, [sensorData, activeRoomId, onRoomClick]);

  return <div ref={mountRef} className="w-full h-[65%] md:h-full cursor-crosshair"></div>;
}
