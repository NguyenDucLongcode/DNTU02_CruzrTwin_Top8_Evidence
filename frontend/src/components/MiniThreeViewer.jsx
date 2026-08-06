import { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

/**
 * Room matching logic (same as ThreeScene)
 */
const ROOM_MAPPING = {
  'L1-B1': 'L1-A1', 'L1-T1': 'L1-A2', 'L1-B2': 'L1-A3', 'L1-T2': 'L1-A4',
  'L1-B3': 'L1-A5', 'L1-T3': 'L1-A6', 'L1-B4': 'L1-A7', 'L1-T4': 'L1-A8',
  'L1-B5': 'L1-A9', 'L1-T5': 'L1-A10', 'L1-B6': 'L1-A11', 'L1-B7': 'L1-A12',
};

function normalizeRoomId(rawId) {
  if (!rawId) return null;
  const match = String(rawId).match(/(L1-[TB]\d|A1\d{2})/i);
  if (!match) return null;
  const id = match[1].toUpperCase();
  if (id.startsWith('A')) return `L1-A${parseInt(id.slice(1)) - 100}`;
  return ROOM_MAPPING[id] || id;
}

function getMeshRoomId(object) {
  let current = object;
  while (current) {
    const matched = normalizeRoomId(current.userData?.roomIdMatch || current.name);
    if (matched) return matched;
    current = current.parent;
  }
  return null;
}

/**
 * Mini 3D Viewer with transparent background and selective room highlighting.
 * @param {string} glbPath - Path to the GLB model
 * @param {'critical'|'warning'|'normal'} severity - Drives color blinking
 * @param {string|null} highlightRoomId - If set, only this room blinks. null = blink all.
 */
export default function MiniThreeViewer({ glbPath, severity = 'normal', highlightRoomId = null, autoRotate = true, className = '' }) {
  const mountRef = useRef(null);
  const rendererRef = useRef(null);
  const reqIdRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container || !glbPath) return;

    const initTimeout = setTimeout(() => {
      const w = container.clientWidth || 220;
      const h = container.clientHeight || 160;
      if (w < 10 || h < 10) return;

      const scene = new THREE.Scene();

      const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 500);
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      rendererRef.current = renderer;
      renderer.setClearColor(0x000000, 0);
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
      container.innerHTML = '';
      container.appendChild(renderer.domElement);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.autoRotate = autoRotate;
      controls.autoRotateSpeed = 1.5;

      scene.add(new THREE.AmbientLight(0xffffff, 1.0));
      const dir = new THREE.DirectionalLight(0xffffff, 1.2);
      dir.position.set(30, 60, 30);
      scene.add(dir);

      // Store original colors + room mapping per mesh
      const meshInfoMap = new Map(); // uuid -> { origColors: Map<idx, hex>, roomId: string|null }

      const loader = new GLTFLoader();
      loader.load(glbPath, (gltf) => {
        const model = gltf.scene;
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        model.position.sub(center);

        // Tag room IDs on meshes (same logic as ThreeScene)
        model.traverse((child) => {
          if (child.name && child.name.match(/(L1-[TB]\d|A10\d)/i)) {
            child.userData.roomIdMatch = child.name;
          }
          if (child.parent?.userData?.roomIdMatch) {
            child.userData.roomIdMatch = child.parent.userData.roomIdMatch;
          }
        });

        // Save original colors
        model.traverse((child) => {
          if (child.isMesh && child.material) {
            const origColors = new Map();
            const mats = Array.isArray(child.material) ? child.material : [child.material];
            mats.forEach((mat, idx) => {
              if (mat?.color) origColors.set(idx, mat.color.getHex());
            });
            meshInfoMap.set(child.uuid, {
              origColors,
              roomId: getMeshRoomId(child),
            });
          }
        });

        scene.add(model);

        const maxDim = Math.max(size.x || 1, size.y || 1, size.z || 1);
        const dist = maxDim * 1.8;
        camera.position.set(dist * 0.5, dist * 0.7, dist * 1.0);
        controls.target.set(0, 0, 0);
        controls.update();
      });

      const animate = () => {
        reqIdRef.current = requestAnimationFrame(animate);
        controls.update();

        const sev = (severity || 'normal').toLowerCase();
        const blink = (Math.sin(Date.now() * 0.005) + 1) / 2;
        const hlNorm = highlightRoomId ? normalizeRoomId(highlightRoomId) || highlightRoomId : null;

        scene.traverse((child) => {
          if (!child.isMesh || !child.material) return;
          const info = meshInfoMap.get(child.uuid);

          // Nếu model là mô hình 1 phòng duy nhất (Phong_xxx.glb), tự động gán origColors nếu chưa có
          const origColors = info?.origColors || new Map();
          const mats = Array.isArray(child.material) ? child.material : [child.material];
          mats.forEach((mat, idx) => {
            if (origColors.get(idx) === undefined && mat?.color) {
              origColors.set(idx, mat.color.getHex());
            }
          });

          // Đối với mô hình Tầng (Tang_x.glb): chỉ tô màu cho duy nhất phòng target (highlightRoomId)
          // Đối với mô hình Phòng (Phong_x.glb): tô màu toàn bộ mô hình phòng đó
          const isSingleRoomModel = glbPath.includes('/Phong/');
          const shouldHighlight = isSingleRoomModel
            ? true
            : Boolean(
                hlNorm && info?.roomId && (
                  info.roomId === hlNorm ||
                  info.roomId.replace(/^L\d+-/, '') === hlNorm.replace(/^L\d+-/, '')
                )
              );

          mats.forEach((mat, idx) => {
            const origHex = origColors.get(idx);
            if (origHex === undefined || !mat?.color) return;

            if (shouldHighlight) {
              if (sev === 'critical') {
                const targetColor = new THREE.Color(0xff0000);
                mat.color.lerpColors(new THREE.Color(origHex), targetColor, blink);
              } else if (sev === 'warning') {
                const targetColor = new THREE.Color(0xffaa00);
                mat.color.lerpColors(new THREE.Color(origHex), targetColor, blink * 0.6);
              } else {
                // Trạng thái Normal / Selected: Hiển thị màu Xanh Lá tươi (0x00ff00 / Pure Green)
                const targetColor = new THREE.Color(0x00ff00);
                mat.color.lerpColors(new THREE.Color(origHex), targetColor, 0.6);
              }
            } else {
              mat.color.setHex(origHex);
            }
          });
        });

        renderer.render(scene, camera);
      };
      animate();
    }, 120);

    return () => {
      clearTimeout(initTimeout);
      if (reqIdRef.current) cancelAnimationFrame(reqIdRef.current);
      if (rendererRef.current) {
        rendererRef.current.dispose();
        rendererRef.current = null;
      }
      if (container) container.innerHTML = '';
    };
  }, [glbPath, autoRotate, severity, highlightRoomId]);

  return <div ref={mountRef} className={`w-full h-full min-h-[80px] ${className}`} />;
}
