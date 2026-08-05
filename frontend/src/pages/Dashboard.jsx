import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import ThreeScene from '../components/ThreeScene';
import LogPanel from '../components/LogPanel';
import Map2D from '../components/Map2D';

const LOG_CONFIG = [
  { type: 'sensors', header: 'SENSORS' },
  { type: 'state', header: 'ORION_STATE' },
  { type: 'ai', header: 'AI_DETECTION' },
  { type: 'robot', header: 'ROBOT_ACTIONS' },
  { type: 'ack', header: 'OPERATOR_ACK' },
];

const EMPTY_LOGS = {};
LOG_CONFIG.forEach((c) => { EMPTY_LOGS[c.type] = []; });

const ROOM_TO_ZONE = {
  'L1-A1': 'DNTU_ROOM_A101', 'L1-A2': 'DNTU_ROOM_A102', 'L1-A3': 'DNTU_ROOM_A103',
  'L1-A4': 'DNTU_ROOM_A104', 'L1-A5': 'DNTU_ROOM_A105', 'L1-A6': 'DNTU_ROOM_A106',
  'L1-A7': 'DNTU_ROOM_A107', 'L1-A8': 'DNTU_ROOM_A108', 'L1-A9': 'DNTU_ROOM_A109',
  'L1-A10': 'DNTU_ROOM_A110', 'L1-A11': 'DNTU_ROOM_A111', 'L1-A12': 'DNTU_ROOM_A112'
};

const DEMO_RUN_ID = 'DNTU02_TOP8_RUN_2026_001';
const DEFAULT_OPERATOR_ID = 'demo_operator';
const DEFAULT_ZONE_ID = 'DNTU_ROOM_A101';
const DEFAULT_ALERT_ID = 'AlertEvent:SCN_CRITICAL_001';
const DEFAULT_ROBOT_ACTION_ID = 'RobotAction:SCN_CRITICAL_001';
const DEFAULT_SCENARIO_ID = 'SCN_CRITICAL_001';

function getRoomZoneId(roomId) {
  return roomId ? ROOM_TO_ZONE[roomId] || roomId : null;
}

function logMatchesRoom(log, zoneId) {
  if (!zoneId || !log) return true;
  const compactRoomId = zoneId.replace('DNTU_ROOM_', '');
  const text = JSON.stringify(log);
  return text.includes(zoneId) || text.includes(compactRoomId);
}

function filterLogsByRoom(logs, zoneId) {
  if (!Array.isArray(logs)) return [];
  if (!zoneId) return logs;
  return logs.filter((log) => logMatchesRoom(log, zoneId));
}

function getLatestRoomLog(logs, zoneId, predicate) {
  if (!Array.isArray(logs)) return null;
  const scopedLogs = zoneId ? logs.filter((log) => logMatchesRoom(log, zoneId)) : logs;
  return [...scopedLogs].reverse().find(predicate) || null;
}

export default function Dashboard() {
  const [activeRoom, setActiveRoom] = useState({ id: null, floor: null });
  const [sensorData, setSensorData] = useState({});
  const [logs, setLogs] = useState(EMPTY_LOGS);
  const [logErrors, setLogErrors] = useState({});
  const [showNormalLogs, setShowNormalLogs] = useState(true);
  const [ackStatus, setAckStatus] = useState('idle');
  const [ackMessage, setAckMessage] = useState('');
  const [isWebhookOnline, setIsWebhookOnline] = useState(false);
  const [networkLatency, setNetworkLatency] = useState(0);
  const [e2eMeasuredLatency, setE2eMeasuredLatency] = useState(null);

  const resetClickCountRef = useRef(0);
  const resetClickTimerRef = useRef(null);

  const handleResetDemoClick = () => {
    resetClickCountRef.current += 1;
    if (resetClickTimerRef.current) clearTimeout(resetClickTimerRef.current);

    resetClickTimerRef.current = setTimeout(async () => {
      const clicks = resetClickCountRef.current;
      resetClickCountRef.current = 0;
      if (clicks >= 3) {
        // Ấn 3 lần nhanh -> Xóa toàn bộ logs
        await handleRunScenario('reset_all');
      } else {
        // Ấn 1 lần -> Undo dòng log vừa thực hiện gần nhất
        await handleRunScenario('undo');
      }
    }, 450);
  };

  const [sidebarWidth, setSidebarWidth] = useState(420);
  const [panelHeights, setPanelHeights] = useState({
    sensors: 140, state: 130, ai: 170, robot: 140, ack: 120
  });
  const [collapsedPanels, setCollapsedPanels] = useState({});

  const [bottomPanelHeight, setBottomPanelHeight] = useState(240);
  const [mapWidthPercent, setMapWidthPercent] = useState(75);
  const [isDraggingMapResize, setIsDraggingMapResize] = useState(false);
  const mapResizeRef = useRef({ startX: 0, startPercent: 0 });

  const [isDraggingSidebar, setIsDraggingSidebar] = useState(false);
  const sidebarDragRef = useRef({ startX: 0, startWidth: 0 });

  const fetchJson = async (path) => {
    const response = await fetch(path);
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Flask backend (port 5000) chưa bật.');
    }
    if (!response.ok) {
      throw new Error(`${path} returned HTTP ${response.status}`);
    }
    return response.json();
  };

  const loadLog = async (type) => {
    try {
      const data = await fetchJson(`/api/logs/${type}`);
      setLogs((prev) => ({ ...prev, [type]: data }));
      setLogErrors((prev) => ({ ...prev, [type]: null }));
    } catch (err) {
      setLogErrors((prev) => ({ ...prev, [type]: err.message }));
    }
  };

  const selectedZoneId = getRoomZoneId(activeRoom.id);
  const displayRoomLabel = activeRoom.id || 'ALL ROOMS';

  const roomLogs = useMemo(() => {
    const out = {};
    LOG_CONFIG.forEach(({ type }) => {
      out[type] = filterLogsByRoom(logs[type], selectedZoneId);
    });
    return out;
  }, [logs, selectedZoneId]);

  const latestRoomRobotAction = useMemo(() => (
    getLatestRoomLog(roomLogs.robot, selectedZoneId, (log) => Boolean(log.robot_action_id))
  ), [roomLogs.robot, selectedZoneId]);

  const latestRoomAi = useMemo(() => (
    getLatestRoomLog(roomLogs.ai, selectedZoneId, () => true)
  ), [roomLogs.ai, selectedZoneId]);

  const getAckBase = () => {
    if (latestRoomRobotAction) return latestRoomRobotAction;
    if (latestRoomAi) return latestRoomAi;
    return {};
  };

  const latestActionText = latestRoomRobotAction
    ? `${latestRoomRobotAction.robot_action_id || 'RobotAction'}`
    : 'No recent RobotAction';

  const handleRoomClick = (roomId, floorIdx) => {
    setActiveRoom({ id: roomId, floor: floorIdx });
    setAckMessage('');
  };

  const handleBackToBuilding = () => {
    setActiveRoom({ id: null, floor: null });
    setAckMessage('');
  };

  const handleOperatorAck = async (decision = 'ACK') => {
    try {
      setAckStatus('loading');
      const base = getAckBase();
      const payload = {
        decision,
        alert_id: base.alert_id || DEFAULT_ALERT_ID,
        robot_action_id: base.robot_action_id || DEFAULT_ROBOT_ACTION_ID,
        operator_id: DEFAULT_OPERATOR_ID,
        demo_run_id: DEMO_RUN_ID,
        scenario_id: base.scenario_id || DEFAULT_SCENARIO_ID,
        zone_id: base.zone_id || selectedZoneId || DEFAULT_ZONE_ID,
        note: `Operator decision: ${decision}`
      };

      const t0 = performance.now();
      const response = await fetch('/api/operator/ack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const t1 = performance.now();
      setNetworkLatency(Math.round(t1 - t0));

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Flask server (port 5000) chưa bật. Hãy chạy: py src/fiware/webhook_receiver.py');
      }

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `ACK failed with HTTP ${response.status}`);
      }

      setAckStatus('success');
      setAckMessage(`${decision}: ${result.status || 'OK'}`);
      loadLog('ack');
    } catch (err) {
      setAckStatus('error');
      setAckMessage(err.message || 'Failed to send ACK.');
    }
  };

  const handleRunScenario = async (scenarioType) => {
    try {
      setAckStatus('loading');
      setAckMessage(`Triggering ${scenarioType}...`);
      const t0 = performance.now();
      const response = await fetch('/api/scenario/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: scenarioType })
      });
      const t1 = performance.now();
      const measuredMs = Math.max(1, Math.round(t1 - t0));
      setE2eMeasuredLatency(measuredMs);

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Flask server (port 5000) chưa bật. Hãy chạy: py src/fiware/webhook_receiver.py');
      }

      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || `Failed with HTTP ${response.status}`);
      }
      setAckStatus('success');
      setAckMessage(result.message || `Started: ${scenarioType}`);
      setTimeout(() => {
        setAckStatus('idle');
        setAckMessage('');
      }, 3500);
    } catch (err) {
      setAckStatus('error');
      setAckMessage(err.message || `Failed to run ${scenarioType}`);
    }
  };

  const checkWebhookHealth = async () => {
    try {
      const t0 = performance.now();
      const res = await fetch('/webhook/health');
      const t1 = performance.now();
      const contentType = res.headers.get('content-type');
      if (res.ok && contentType && contentType.includes('application/json')) {
        const data = await res.json();
        setIsWebhookOnline(data.status === 'healthy');
        setNetworkLatency(Math.max(2, Math.round(t1 - t0)));
      } else {
        setIsWebhookOnline(false);
      }
    } catch (e) {
      setIsWebhookOnline(false);
    }
  };

  const calculatedE2eLatency = useMemo(() => {
    if (e2eMeasuredLatency !== null) {
      return e2eMeasuredLatency;
    }
    const latestRobot = roomLogs.robot?.[roomLogs.robot.length - 1];
    const latestAi = roomLogs.ai?.[roomLogs.ai.length - 1];
    const latestSensor = roomLogs.sensors?.[roomLogs.sensors.length - 1];

    if (!latestSensor && !latestAi && !latestRobot) return null;

    const latestTarget = latestRobot || latestAi;
    const tSensorStr = latestSensor?.timestamp || latestSensor?.created_at;
    const tTargetStr = latestTarget?.timestamp || latestTarget?.created_at;

    if (tSensorStr && tTargetStr) {
      const t1 = new Date(tSensorStr).getTime();
      const t2 = new Date(tTargetStr).getTime();

      if (!isNaN(t1) && !isNaN(t2)) {
        const diffMs = Math.abs(t2 - t1);
        if (diffMs > 0) {
          return diffMs;
        }
      }
    }

    return null;
  }, [e2eMeasuredLatency, roomLogs.sensors, roomLogs.robot, roomLogs.ai]);

  const handleStartWebhookServer = async () => {
    try {
      setAckStatus('loading');
      setAckMessage('Starting Webhook Server...');
      const res = await fetch('/start-webhook-server', { method: 'POST' });
      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Hãy restart Vite (npm run dev) để nạp plugin mới.');
      }
      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Server spawn error');
      }
      setTimeout(async () => {
        await checkWebhookHealth();
        setAckStatus('idle');
        setAckMessage('');
      }, 2500);
    } catch (err) {
      setAckStatus('error');
      setAckMessage(err.message || 'Failed to start Webhook Server');
    }
  };

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      await checkWebhookHealth();
      await Promise.all(LOG_CONFIG.map(({ type }) => loadLog(type)));
      try {
        const dbData = await fetchJson('/api/db/sensors');
        if (!cancelled) setSensorData(dbData);
      } catch (err) {
        if (!cancelled) {
          setLogErrors((prev) => ({ ...prev, sensors: err.message }));
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const hasLogError = Object.values(logErrors).some(Boolean);

  useEffect(() => {
    if (!isDraggingSidebar) return;
    const handleMouseMove = (e) => {
      const delta = e.clientX - sidebarDragRef.current.startX;
      const newWidth = Math.max(320, Math.min(900, sidebarDragRef.current.startWidth - delta));
      setSidebarWidth(newWidth);
    };
    const handleMouseUp = () => setIsDraggingSidebar(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDraggingSidebar]);

  const handleSidebarDragStart = useCallback((e) => {
    e.preventDefault();
    sidebarDragRef.current = { startX: e.clientX, startWidth: sidebarWidth };
    setIsDraggingSidebar(true);
  }, [sidebarWidth]);

  const handleMapDragStart = useCallback((e) => {
    e.preventDefault();
    mapResizeRef.current = { startX: e.clientX, startPercent: mapWidthPercent };
    setIsDraggingMapResize(true);
  }, [mapWidthPercent]);

  useEffect(() => {
    if (!isDraggingMapResize) return;
    const handleMouseMove = (e) => {
      const delta = e.clientX - mapResizeRef.current.startX;
      const viewportWidth = window.innerWidth;
      const newPercent = Math.max(40, Math.min(90, mapResizeRef.current.startPercent + (delta / viewportWidth) * 100));
      setMapWidthPercent(newPercent);
    };
    const handleMouseUp = () => setIsDraggingMapResize(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDraggingMapResize]);

  const togglePanel = useCallback((type) => {
    setCollapsedPanels((prev) => ({ ...prev, [type]: !prev[type] }));
  }, []);

  const resizePanel = useCallback((type, newHeight) => {
    setPanelHeights((prev) => ({ ...prev, [type]: newHeight }));
  }, []);

  return (
    <div className="w-full h-full flex flex-col md:flex-row overflow-hidden bg-black">
      <main className="flex-1 relative h-full flex flex-col min-w-0">
        <div className="flex-1 relative w-full">
          <ThreeScene
            activeRoomId={activeRoom.id}
            activeFloorIdx={activeRoom.floor}
            onRoomClick={handleRoomClick}
            sensorData={sensorData}
          />

          {!isWebhookOnline && (
            <button
              onClick={handleStartWebhookServer}
              disabled={ackStatus === 'loading'}
              className="absolute top-6 left-6 px-4 py-2 bg-red-600/95 hover:bg-red-500 text-white font-mono font-bold text-xs rounded-lg shadow-[0_0_20px_rgba(220,38,38,0.7)] border border-red-400 animate-pulse transition-all z-50 cursor-pointer flex items-center gap-2"
            >
              <span>⚡ WEBHOOK OFFLINE - CLICK TO START SERVER</span>
            </button>
          )}

          {activeRoom.id && (
            <button
              onClick={handleBackToBuilding}
              className="absolute top-20 left-6 px-5 py-2 bg-red-600/90 hover:bg-red-500 text-white font-bold font-mono text-xs rounded shadow-[0_0_20px_rgba(220,38,38,0.4)] transition-all border border-red-400 z-40 cursor-pointer"
            >
              BACK TO BUILDING
            </button>
          )}

          {activeRoom.id && (() => {
            const s = sensorData[activeRoom.id];
            const smoke = s?.smoke || 0;
            const co2 = s?.co2 || 0;
            const temp = s?.temp || 0;
            const ds = String(s?.device_status || '').toUpperCase();
            const isCritical = ds === 'CRITICAL' || ds === 'ERROR' || ds === 'FIRE' || temp >= 40 || smoke >= 1 || co2 >= 1000;
            const isWarning = !isCritical && (ds === 'WARNING' || temp >= 32 || co2 >= 631 || smoke >= 0.5);
            const statusLabel = isCritical ? 'CRITICAL' : isWarning ? 'WARNING' : 'NORMAL';
            const borderClass = isCritical ? 'border-red-500/50' : isWarning ? 'border-amber-400/50' : 'border-emerald-500/50';
            const shadowClass = isCritical ? 'shadow-red-500/20' : isWarning ? 'shadow-amber-400/20' : 'shadow-emerald-500/20';
            const titleClass = isCritical ? 'text-red-500 border-red-500/30' : isWarning ? 'text-amber-400 border-amber-400/30' : 'text-emerald-500 border-emerald-500/30';
            const badgeClass = isCritical ? 'border-red-500 text-red-500' : isWarning ? 'border-amber-400 text-amber-400' : 'border-emerald-500 text-emerald-500';
            return (
            <div className={`absolute bottom-8 left-6 bg-black/80 backdrop-blur-xl border ${borderClass} rounded-xl p-5 shadow-2xl ${shadowClass} z-40 font-mono min-w-[280px]`}>
              <div className={`text-xl font-bold ${titleClass} mb-4 border-b pb-2 flex justify-between items-center`}>
                <span>ROOM {activeRoom.id} (Floor {activeRoom.floor})</span>
                <span className={`text-xs px-2 py-0.5 rounded border ${badgeClass}`}>{statusLabel}</span>
              </div>

              {s ? (
                <div className="flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Temperature:</span>
                    <span className={`font-bold text-lg ${temp >= 40 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {temp.toFixed(1)} °C
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Smoke:</span>
                    <span className={`font-bold text-lg ${smoke > 0 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {smoke.toFixed(1)} %
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">CO2:</span>
                    <span className={`font-bold text-lg ${co2 >= 900 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {co2.toFixed(1)} ppm
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-zinc-500 font-bold">No sensor data</div>
              )}
            </div>
            );
          })()}
        </div>

        {!activeRoom.id && (
          <div className="w-full border-t border-zinc-800 bg-zinc-900" style={{ height: bottomPanelHeight }}>
            <div className="flex h-full">
              <div className="flex-shrink-0" style={{ width: `${mapWidthPercent}%` }}>
                <Map2D
                  activeFloorIdx={activeRoom.floor}
                  activeRoomId={activeRoom.id}
                  sensorData={sensorData}
                  onRoomClick={handleRoomClick}
                />
              </div>
              <div
                className="w-1.5 cursor-col-resize bg-zinc-800 hover:bg-blue-500/40 transition-colors flex-shrink-0"
                onMouseDown={handleMapDragStart}
              />
              <div className="flex-1 p-3 flex flex-col justify-center items-center gap-2 relative overflow-hidden bg-zinc-950 min-w-[220px]">
                {/* Thanh thông số độ trễ Mạng (NET RTT) & Toàn luồng (E2E LATENCY) */}
                <div className="w-full max-w-[260px] flex items-center justify-between px-2.5 py-1 bg-zinc-900/90 border border-zinc-800 rounded-md font-mono text-[9px] text-zinc-400 select-none shadow-inner">
                  <div className="flex items-center gap-1.5" title="Độ trễ mạng RTT (Round-Trip Time)">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                    <span className="text-zinc-500">NET RTT:</span>
                    <span className="text-emerald-400 font-bold">{networkLatency} ms</span>
                  </div>
                  <div className="flex items-center gap-1.5" title="Độ trễ toàn luồng End-to-End (Sensor -> AI -> Robot)">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                    <span className="text-zinc-500">E2E LATENCY:</span>
                    <span className="text-blue-400 font-bold">{calculatedE2eLatency !== null ? `${calculatedE2eLatency} ms` : '-- ms'}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 w-full max-w-[260px]">
                  {/* Cột 1 (Trái) */}
                  <button
                    onClick={() => handleOperatorAck('ACK')}
                    disabled={ackStatus === 'loading'}
                    className="h-7 bg-emerald-950/60 hover:bg-emerald-600/80 border border-emerald-500/50 text-emerald-300 hover:text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_10px_rgba(16,185,129,0.2)] transition-all cursor-pointer disabled:opacity-50"
                  >
                    ACK
                  </button>
                  {/* Cột 2 (Phải) */}
                  <button
                    onClick={() => handleRunScenario('normal')}
                    disabled={ackStatus === 'loading'}
                    className="h-7 bg-blue-950/60 hover:bg-blue-600/80 border border-blue-500/50 text-blue-300 hover:text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_10px_rgba(59,130,246,0.2)] transition-all cursor-pointer disabled:opacity-50"
                  >
                    Normal
                  </button>

                  <button
                    onClick={() => handleRunScenario('robot_retry')}
                    disabled={ackStatus === 'loading'}
                    className="h-7 bg-amber-950/60 hover:bg-amber-600/80 border border-amber-500/50 text-amber-300 hover:text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_10px_rgba(245,158,11,0.2)] transition-all cursor-pointer disabled:opacity-50"
                  >
                    Robot Retry
                  </button>
                  <button
                    onClick={() => handleRunScenario('warning')}
                    disabled={ackStatus === 'loading'}
                    className="h-7 bg-yellow-950/60 hover:bg-yellow-600/80 border border-yellow-500/50 text-yellow-300 hover:text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_10px_rgba(234,179,8,0.2)] transition-all cursor-pointer disabled:opacity-50"
                  >
                    Warning
                  </button>

                  <button
                    onClick={handleResetDemoClick}
                    disabled={ackStatus === 'loading'}
                    title="Bấm 1 lần: Undo dòng log vừa thực hiện | Bấm 3 lần nhanh: Xóa toàn bộ log"
                    className="h-7 bg-zinc-800/80 hover:bg-zinc-700 border border-zinc-600 text-zinc-300 hover:text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_10px_rgba(113,113,122,0.2)] transition-all cursor-pointer disabled:opacity-50"
                  >
                    Reset Demo
                  </button>
                  <button
                    onClick={() => handleRunScenario('critical')}
                    disabled={ackStatus === 'loading'}
                    className="h-7 bg-red-950/60 hover:bg-red-600/80 border border-red-500/50 text-red-300 hover:text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_10px_rgba(239,68,68,0.2)] transition-all cursor-pointer disabled:opacity-50"
                  >
                    Critical
                  </button>

                  {/* Nút Khởi động Webhook - nằm ngay trong cụm nút */}
                  {!isWebhookOnline && (
                    <button
                      onClick={handleStartWebhookServer}
                      disabled={ackStatus === 'loading'}
                      className="col-span-2 h-8 bg-red-600/90 hover:bg-red-500 text-white font-mono font-bold text-[10px] rounded-md shadow-[0_0_15px_rgba(220,38,38,0.6)] border border-red-400 animate-pulse transition-all cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
                    >
                      <span>⚡ WEBHOOK OFFLINE - CLICK TO START SERVER</span>
                    </button>
                  )}
                </div>

                {ackMessage && (
                  <div className={`w-full max-w-[260px] text-[10px] font-mono text-center ${ackStatus === 'error' ? 'text-red-400' : ackStatus === 'success' ? 'text-emerald-400' : 'text-zinc-500'}`}>
                    {ackMessage}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <div
        className="h-full bg-[#0a0a0c] border-l border-zinc-800 flex flex-col overflow-hidden shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-40 relative flex-shrink-0"
        style={{ width: sidebarWidth }}
      >
        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/80 flex items-center justify-between gap-3 select-none">
          <div className="min-w-0">
            <div className="text-[10px] tracking-widest text-zinc-500 font-mono">ROOM LOGS</div>
            <div className="text-xs text-blue-300 font-bold truncate">{displayRoomLabel}</div>
          </div>
          <label className="flex items-center gap-1 text-[10px] text-zinc-400 font-mono whitespace-nowrap cursor-pointer">
            <input
              type="checkbox"
              checked={showNormalLogs}
              onChange={(event) => setShowNormalLogs(event.target.checked)}
              className="accent-blue-500"
            />
            Normal
          </label>
        </div>

        {hasLogError && (
          <div className="px-3 py-2 text-[10px] text-red-300 bg-red-950/40 border-b border-red-900 font-mono">
            Some API logs failed to fetch. Check Flask backend on port 5000.
          </div>
        )}

        <div className="flex-1 overflow-y-auto flex flex-col">
          {LOG_CONFIG.map(({ type, header }) => (
            <LogPanel
              key={type}
              title={header}
              data={roomLogs[type]}
              height={collapsedPanels[type] ? undefined : panelHeights[type]}
              showNormal={showNormalLogs}
              isCollapsed={!!collapsedPanels[type]}
              onToggleCollapse={() => togglePanel(type)}
              onResize={(h) => resizePanel(type, h)}
              emptyMessage={selectedZoneId ? `No ${header} log for ${activeRoom.id}.` : `No ${header} log.`}
            />
          ))}
        </div>
      </div>

      <div
        className="w-1.5 cursor-col-resize bg-zinc-800 hover:bg-blue-500/40 transition-colors flex-shrink-0 h-full"
        onMouseDown={handleSidebarDragStart}
      />
    </div>
  );
}