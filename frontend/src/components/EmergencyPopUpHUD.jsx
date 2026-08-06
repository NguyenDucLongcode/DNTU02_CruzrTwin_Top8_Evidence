import { useState, useRef, useCallback, useEffect } from 'react';
import MiniThreeViewer from './MiniThreeViewer';

const PANEL_WIDTH = 250;
const PANEL_HEIGHT = 200;
const TELEMETRY_HEIGHT = 145;
const SPACING = 14;

/* ── Draggable + Resizable floating panel wrapper ── */
// eslint-disable-next-line no-unused-vars
function FloatingPanel({ title, titleRight, borderColor, headerBg, headerText, initX, initY, initW, initH, onClose, children }) {
  const [pos, setPos] = useState({ x: initX, y: initY });
  const [size, setSize] = useState({ w: initW, h: initH });

  const dragRef = useRef(null);
  const resizeRef = useRef(null);

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  const onDragStart = useCallback((e) => {
    e.preventDefault();
    dragRef.current = { sx: e.clientX - pos.x, sy: e.clientY - pos.y };
    const onMove = (ev) => { if (!dragRef.current) return; setPos({ x: ev.clientX - dragRef.current.sx, y: ev.clientY - dragRef.current.sy }); };
    const onUp = () => { dragRef.current = null; window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [pos]);

  const onResizeStart = useCallback((e) => {
    e.preventDefault(); e.stopPropagation();
    resizeRef.current = { sx: e.clientX, sy: e.clientY, sw: size.w, sh: size.h };
    const onMove = (ev) => { if (!resizeRef.current) return; setSize({ w: clamp(resizeRef.current.sw + (ev.clientX - resizeRef.current.sx), 160, 800), h: clamp(resizeRef.current.sh + (ev.clientY - resizeRef.current.sy), 100, 600) }); };
    const onUp = () => { resizeRef.current = null; window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [size]);

  return (
    <div
      className={`absolute z-50 rounded-xl font-mono text-white overflow-hidden animate-fade-in bg-black/30 backdrop-blur-md border border-white/15 pointer-events-auto shadow-2xl`}
      style={{ left: pos.x, top: pos.y, width: size.w, height: size.h }}
    >
      {/* Invisible drag area (whole panel) + close button top-right */}
      <div className="absolute top-0 left-0 right-0 bottom-0 z-10 cursor-move" onMouseDown={onDragStart} />
      {onClose && (
        <button onClick={onClose} className="absolute top-1.5 right-1.5 z-20 text-zinc-400 hover:text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full bg-black/60 hover:bg-red-600/90 transition-colors cursor-pointer leading-none">✕</button>
      )}
      {/* Content */}
      <div className="w-full h-full overflow-hidden rounded-xl pointer-events-none">
        {children}
      </div>
      {/* Resize handle */}
      <div className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize z-20" onMouseDown={onResizeStart}>
        <svg className="w-2.5 h-2.5 absolute bottom-1 right-1 text-white/30 hover:text-blue-400" viewBox="0 0 10 10">
          <path d="M9 1L1 9M9 5L5 9M9 8L8 9" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
      </div>
    </div>
  );
}

function EmergencyPopupContent({ roomInfo, sensorData, onClose }) {
  const { id: roomId, floor: floorIdx } = roomInfo;
  const containerRef = useRef(null);

  const [containerSize, setContainerSize] = useState(() => ({
    w: typeof window !== 'undefined' ? window.innerWidth * 0.65 : 800,
    h: typeof window !== 'undefined' ? window.innerHeight * 0.6 : 500
  }));

  const [showFloor, setShowFloor] = useState(true);
  const [showRoom, setShowRoom] = useState(true);
  const [showSensor, setShowSensor] = useState(true);

  useEffect(() => {
    const parent = containerRef.current?.parentElement;
    if (!parent) return;

    const updateSize = () => {
      const rect = parent.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setContainerSize({ w: rect.width, h: rect.height });
      }
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(parent);
    return () => observer.disconnect();
  }, []);

  const safeSensorData = sensorData || {};
  const targetKey = roomId || 'L1-A1';
  const fallbackKey = targetKey.replace(/L\d+/, 'L1');
  const sensor = safeSensorData[targetKey] || safeSensorData[fallbackKey] || {};

  const rawTemp = sensor.temp ?? sensor.temperature ?? 24.5;
  const temp = isNaN(Number(rawTemp)) ? 24.5 : Number(rawTemp);

  const rawSmoke = sensor.smoke_status ?? sensor.smoke ?? 0.0;
  const smoke = isNaN(Number(rawSmoke)) ? 0.0 : Number(rawSmoke);

  const rawCo2 = sensor.co2 ?? sensor.air_quality_or_co2 ?? 400.0;
  const co2 = isNaN(Number(rawCo2)) ? 400.0 : Number(rawCo2);

  const deviceStatus = String(sensor.device_status || sensor.status || 'NORMAL').toUpperCase();

  const isCritical = deviceStatus === 'CRITICAL' || deviceStatus === 'ERROR' || deviceStatus === 'FIRE' || temp >= 40 || smoke >= 1 || co2 >= 1000;
  const isWarning = !isCritical && (deviceStatus === 'WARNING' || temp >= 32 || co2 >= 631 || smoke >= 0.5);

  const borderCritical = isCritical
    ? 'border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.3)]'
    : isWarning
    ? 'border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.25)]'
    : 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]';
  const headerBgCritical = isCritical ? 'bg-red-950/50' : isWarning ? 'bg-amber-950/50' : 'bg-emerald-950/50';
  const headerTextCritical = isCritical ? 'text-red-400' : isWarning ? 'text-amber-400' : 'text-emerald-400';

  // ── Tọa độ 3 góc CHUẨN XÁC VÀ ĐỒNG ĐỀU (Match Ảnh Mẫu) ──
  // Góc 1: Trên-Trái (Top-Left of 3D Canvas)
  const floorX = SPACING;
  const floorY = SPACING;

  // Góc 2: Trên-Phải (Top-Right of 3D Canvas)
  const rightPanelX = Math.max(SPACING, containerSize.w - PANEL_WIDTH - SPACING);
  const rightPanelY = SPACING;

  // Góc 3: Dưới-Trái (Bottom-Left of 3D Canvas — Cùng chiều rộng 250px với góc trên trái)
  const bottomPanelX = SPACING;
  const bottomPanelY = Math.max(SPACING, containerSize.h - TELEMETRY_HEIGHT - SPACING);

  useEffect(() => {
    if (!showFloor && !showRoom && !showSensor) {
      onClose?.();
    }
  }, [showFloor, showRoom, showSensor, onClose]);

  const floorFileIdx = Math.max(0, Math.min(4, (floorIdx || 1) - 1));
  const floorGlb = `/mohinh/Tang/Tang_${floorFileIdx}.glb`;
  const validRooms = ['L1-A1', 'L1-A2', 'L1-A3', 'L1-A4', 'L1-A5'];
  const safeRoomId = validRooms.includes(roomId) ? roomId : 'L1-A1';
  const roomGlb = `/mohinh/Phong/Phong_${safeRoomId}.glb`;

  return (
    <div ref={containerRef} className="absolute inset-0 pointer-events-none z-40 overflow-hidden">
      {/* ── Panel 1: Floor 3D (Góc Trên-Trái) ── */}
      {showFloor && (
        <FloatingPanel
          title={`🏛 FLOOR ${floorIdx || 1} — 3D`}
          borderColor="border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
          headerBg="bg-blue-950/50"
          headerText="text-blue-400"
          initX={floorX} initY={floorY} initW={PANEL_WIDTH} initH={PANEL_HEIGHT}
          onClose={() => setShowFloor(false)}
        >
          <div className="w-full h-full">
            <MiniThreeViewer key={`f-${floorGlb}`} glbPath={floorGlb} severity={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'} highlightRoomId={roomId} />
          </div>
        </FloatingPanel>
      )}

      {/* ── Panel 2: Room 3D (Góc Trên-Phải) ── */}
      {showRoom && (
        <FloatingPanel
          title={`🔥 ROOM ${roomId}`}
          titleRight={deviceStatus}
          borderColor={borderCritical}
          headerBg={headerBgCritical}
          headerText={headerTextCritical}
          initX={rightPanelX} initY={rightPanelY} initW={PANEL_WIDTH} initH={PANEL_HEIGHT}
          onClose={() => setShowRoom(false)}
        >
          <div className="w-full h-full">
            <MiniThreeViewer key={`r-${roomGlb}`} glbPath={roomGlb} severity={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'} />
          </div>
        </FloatingPanel>
      )}

      {/* ── Panel 3: Sensor Telemetry (Góc Dưới-Trái — Chiều rộng 250px khớp góc trên) ── */}
      {showSensor && (
        <FloatingPanel
          title="📊 SENSOR DATA"
          titleRight="LIVE"
          borderColor="border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
          headerBg="bg-emerald-950/40"
          headerText="text-emerald-400"
          initX={bottomPanelX} initY={bottomPanelY} initW={PANEL_WIDTH} initH={TELEMETRY_HEIGHT}
          onClose={() => setShowSensor(false)}
        >
          <div className="p-2 space-y-1 text-[11px] h-full flex flex-col justify-between">
            {[
              { icon: '🌡️', label: 'Nhiệt độ', value: `${temp.toFixed(1)} °C`, alert: temp >= 40, warn: temp >= 32 },
              { icon: '💨', label: 'Khói', value: `${smoke.toFixed(1)} %`, alert: smoke >= 0.5 },
              { icon: '🫁', label: 'CO₂', value: `${co2.toFixed(0)} ppm`, alert: co2 >= 1000, warn: co2 >= 631 },
              { icon: '🤖', label: 'Robot', value: 'DISPATCHED', color: 'text-cyan-400' },
              { icon: '🔌', label: 'Smart Plug', value: isCritical ? 'POWER OFF' : 'ON', color: isCritical ? 'text-red-400' : 'text-emerald-400' },
            ].map((r, i) => (
              <div key={i} className="flex justify-between items-center bg-zinc-900/80 px-2 py-0.5 rounded border border-zinc-800/50 text-[10px]">
                <span className="text-zinc-400">{r.icon} {r.label}</span>
                <span className={`font-bold ${r.color || (r.alert ? 'text-red-400 animate-pulse' : r.warn ? 'text-amber-400' : 'text-emerald-400')}`}>{r.value}</span>
              </div>
            ))}
          </div>
        </FloatingPanel>
      )}
    </div>
  );
}

export default function EmergencyPopUpHUD({ roomInfo, sensorData, onClose }) {
  return roomInfo ? <EmergencyPopupContent roomInfo={roomInfo} sensorData={sensorData} onClose={onClose} /> : null;
}
