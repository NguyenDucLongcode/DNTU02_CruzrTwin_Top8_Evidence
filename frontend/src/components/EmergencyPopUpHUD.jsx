import { useState, useRef, useCallback, useEffect } from 'react';
import MiniThreeViewer from './MiniThreeViewer';

/* ── Draggable + Resizable floating panel wrapper ── */
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
    const onMove = (ev) => { if (!resizeRef.current) return; setSize({ w: clamp(resizeRef.current.sw + (ev.clientX - resizeRef.current.sx), 160, 800), h: clamp(resizeRef.current.sh + (ev.clientY - resizeRef.current.sy), 120, 600) }); };
    const onUp = () => { resizeRef.current = null; window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [size]);

  return (
    <div
      className={`absolute z-50 rounded-xl font-mono text-white overflow-hidden animate-fade-in bg-black/20 border border-white/10`}
      style={{ left: pos.x, top: pos.y, width: size.w, height: size.h }}
    >
      {/* Invisible drag area (whole panel) + close button top-right */}
      <div className="absolute top-0 left-0 right-0 bottom-0 z-10 cursor-move" onMouseDown={onDragStart} />
      {onClose && (
        <button onClick={onClose} className="absolute top-1.5 right-1.5 z-20 text-zinc-400 hover:text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full bg-black/50 hover:bg-red-600/80 transition-colors cursor-pointer leading-none">✕</button>
      )}
      {/* Content */}
      <div className="w-full h-full overflow-hidden rounded-xl pointer-events-none">
        {children}
      </div>
      {/* Resize handle */}
      <div className="absolute bottom-0 right-0 w-5 h-5 cursor-nwse-resize z-20" onMouseDown={onResizeStart}>
        <svg className="w-3 h-3 absolute bottom-1 right-1 text-white/20 hover:text-blue-400" viewBox="0 0 10 10">
          <path d="M9 1L1 9M9 5L5 9M9 8L8 9" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
      </div>
    </div>
  );
}

export default function EmergencyPopUpHUD({ roomInfo, sensorData, onClose }) {
  if (!roomInfo) return null;

  const { id: roomId, floor: floorIdx } = roomInfo;
  const sensor = sensorData[roomId] || sensorData[roomId?.replace(/L\d+/, 'L1')] || {};

  const temp = Number(sensor.temp || 0);
  const smoke = Number(sensor.smoke_status !== undefined ? sensor.smoke_status : (sensor.smoke || 0));
  const co2 = Number(sensor.co2 || 0);
  const deviceStatus = String(sensor.device_status || sensor.status || 'CRITICAL').toUpperCase();

  const isCritical = deviceStatus === 'CRITICAL' || deviceStatus === 'ERROR' || deviceStatus === 'FIRE' || temp >= 40 || smoke >= 1 || co2 >= 1000;
  const isWarning = !isCritical && (deviceStatus === 'WARNING' || temp >= 32 || co2 >= 631 || smoke >= 0.5);

  const borderCritical = isCritical ? 'border-red-500/50 shadow-[0_0_25px_rgba(239,68,68,0.3)]' : 'border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.25)]';
  const headerBgCritical = isCritical ? 'bg-red-950/60' : 'bg-amber-950/60';
  const headerTextCritical = isCritical ? 'text-red-400' : 'text-amber-400';

  const floorFileIdx = Math.max(0, Math.min(4, (floorIdx || 1) - 1));
  const floorGlb = `/mohinh/Tang/Tang_${floorFileIdx}.glb`;
  const roomGlb = `/mohinh/Phong/Phong_${roomId}.glb`;

  const [showFloor, setShowFloor] = useState(true);
  const [showRoom, setShowRoom] = useState(true);
  const [showSensor, setShowSensor] = useState(true);

  return (
    <>
      {/* ── Panel 1: Floor 3D ── */}
      {showFloor && (
        <FloatingPanel
          title={`🏛 FLOOR ${floorIdx || 1} — 3D`}
          borderColor="border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
          headerBg="bg-blue-950/50"
          headerText="text-blue-400"
          initX={8} initY={8} initW={320} initH={280}
          onClose={() => setShowFloor(false)}
        >
          <div className="w-full h-full">
            <MiniThreeViewer key={`f-${floorGlb}`} glbPath={floorGlb} severity={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'} highlightRoomId={roomId} />
          </div>
        </FloatingPanel>
      )}

      {/* ── Panel 2: Room 3D ── */}
      {showRoom && (
        <FloatingPanel
          title={`🔥 ROOM ${roomId}`}
          titleRight={deviceStatus}
          borderColor={borderCritical}
          headerBg={headerBgCritical}
          headerText={headerTextCritical}
          initX={340} initY={8} initW={320} initH={280}
          onClose={() => setShowRoom(false)}
        >
          <div className="w-full h-full">
            <MiniThreeViewer key={`r-${roomGlb}`} glbPath={roomGlb} severity={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'} />
          </div>
        </FloatingPanel>
      )}

      {/* ── Panel 3: Sensor Telemetry ── */}
      {showSensor && (
        <FloatingPanel
          title="📊 SENSOR DATA"
          titleRight="LIVE"
          borderColor="border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
          headerBg="bg-emerald-950/40"
          headerText="text-emerald-400"
          initX={8} initY={296} initW={280} initH={180}
          onClose={() => setShowSensor(false)}
        >
          <div className="p-2.5 space-y-1.5 text-[11px]">
            {[
              { icon: '🌡️', label: 'Nhiệt độ', value: `${temp.toFixed(1)} °C`, alert: temp >= 40, warn: temp >= 32 },
              { icon: '💨', label: 'Khói', value: `${smoke.toFixed(1)} %`, alert: smoke >= 0.5 },
              { icon: '🫁', label: 'CO₂', value: `${co2.toFixed(0)} ppm`, alert: co2 >= 1000, warn: co2 >= 631 },
              { icon: '🤖', label: 'Robot', value: 'DISPATCHED', color: 'text-cyan-400' },
              { icon: '🔌', label: 'Smart Plug', value: isCritical ? 'POWER OFF' : 'ON', color: isCritical ? 'text-red-400' : 'text-emerald-400' },
            ].map((r, i) => (
              <div key={i} className="flex justify-between items-center bg-zinc-900/60 px-2.5 py-1.5 rounded border border-zinc-800/50">
                <span className="text-zinc-400">{r.icon} {r.label}</span>
                <span className={`font-bold ${r.color || (r.alert ? 'text-red-400 animate-pulse' : r.warn ? 'text-amber-400' : 'text-emerald-400')}`}>{r.value}</span>
              </div>
            ))}
          </div>
        </FloatingPanel>
      )}

      {/* Master close: khi tất cả panel đã đóng → gọi onClose */}
      {!showFloor && !showRoom && !showSensor && (() => { onClose?.(); return null; })()}
    </>
  );
}
