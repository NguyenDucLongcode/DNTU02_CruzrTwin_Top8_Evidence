import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Building, Flame, BarChart3, Thermometer, Wind, Activity, Bot, AlertTriangle } from 'lucide-react';
import ThreeScene from '../components/ThreeScene';
import LogPanel from '../components/LogPanel';
import Map2D from '../components/Map2D';
import EmergencyPopUpHUD from '../components/EmergencyPopUpHUD';
import MiniThreeViewer from '../components/MiniThreeViewer';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.warn("ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || null;
    }
    return this.props.children;
  }
}

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
  if (!roomId) return null;
  if (ROOM_TO_ZONE[roomId]) return ROOM_TO_ZONE[roomId];
  const match = String(roomId).match(/L(\d+)-A(\d+)/i);
  if (match) {
    const floor = parseInt(match[1]);
    const num = parseInt(match[2]);
    return `DNTU_ROOM_A${floor * 100 + num}`;
  }
  return roomId;
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

function RoomDetailBottomBar({ roomId, floorIdx, sensorData }) {
  const sensor = sensorData[roomId] || sensorData[roomId?.replace(/L\d+/, 'L1')] || {};

  const temp = Number(sensor.temp !== undefined ? sensor.temp : (sensor.temperature !== undefined ? sensor.temperature : 24.5));
  const smoke = Number(sensor.smoke_status !== undefined ? sensor.smoke_status : (sensor.smoke !== undefined ? sensor.smoke : 0.0));
  const co2 = Number(sensor.co2 !== undefined ? sensor.co2 : (sensor.air_quality_or_co2 !== undefined ? sensor.air_quality_or_co2 : 400.0));
  const deviceStatus = String(sensor.device_status || sensor.status || 'NORMAL').toUpperCase();

  const isCritical = deviceStatus === 'CRITICAL' || deviceStatus === 'ERROR' || deviceStatus === 'FIRE' || temp >= 40 || smoke >= 1 || co2 >= 1000;
  const isWarning = !isCritical && (deviceStatus === 'WARNING' || temp >= 32 || co2 >= 631 || smoke >= 0.5);

  const floorFileIdx = Math.max(0, Math.min(4, (floorIdx || 1) - 1));
  const floorGlb = `/mohinh/Tang/Tang_${floorFileIdx}.glb`;
  const roomGlb = `/mohinh/Phong/Phong_${roomId}.glb`;

  return (
    <div className="w-full h-full p-1.5 grid grid-cols-3 gap-2 bg-zinc-950 font-mono text-white overflow-hidden">
      {/* Mục 1: Mô hình Tầng chứa phòng */}
      <div className="relative rounded-lg overflow-hidden border border-blue-500/30 bg-black/40 flex flex-col h-full">
        <div className="px-2 py-0.5 bg-blue-950/60 border-b border-blue-500/30 text-[10px] font-bold text-blue-400 flex items-center justify-between">
          <span className="flex items-center gap-1"><Building className="w-3 h-3" /> FLOOR {floorIdx || 1} VIEW</span>
          <span className="text-[9px] text-zinc-400">3D MODEL</span>
        </div>
        <div className="flex-1 relative w-full h-full">
          <MiniThreeViewer key={`f-${floorGlb}`} glbPath={floorGlb} severity={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'} highlightRoomId={roomId} />
        </div>
      </div>

      {/* Mục 2: Mô hình Phòng 3D */}
      <div className={`relative rounded-lg overflow-hidden border ${isCritical ? 'border-red-500/40 bg-red-950/20' : isWarning ? 'border-amber-500/40 bg-amber-950/20' : 'border-emerald-500/40 bg-emerald-950/20'} flex flex-col h-full`}>
        <div className={`px-2 py-0.5 border-b text-[10px] font-bold flex items-center justify-between ${isCritical ? 'bg-red-950/60 border-red-500/30 text-red-400' : isWarning ? 'bg-amber-950/60 border-amber-500/30 text-amber-400' : 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400'}`}>
          <span className="flex items-center gap-1"><Flame className="w-3 h-3" /> ROOM {roomId} 3D</span>
          <span className="text-[9px] px-1 py-0.5 rounded bg-black/40">{deviceStatus}</span>
        </div>
        <div className="flex-1 relative w-full h-full">
          <MiniThreeViewer key={`r-${roomGlb}`} glbPath={roomGlb} severity={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'} />
        </div>
      </div>

      {/* Mục 3: Bảng Thông số Cảm biến từ Log */}
      <div className="relative rounded-lg border border-emerald-500/30 bg-zinc-900/90 p-2 flex flex-col justify-between text-[11px] h-full overflow-y-auto">
        <div className="font-bold text-emerald-400 border-b border-zinc-800 pb-1 flex justify-between items-center">
          <span className="flex items-center gap-1"><BarChart3 className="w-3 h-3" /> SENSOR TELEMETRY</span>
          <span className="text-[9px] text-zinc-400">ROOM {roomId}</span>
        </div>
        <div className="space-y-1 my-1">
          <div className="flex justify-between items-center bg-zinc-950/80 px-2 py-0.5 rounded border border-zinc-800/60">
            <span className="text-zinc-400 flex items-center gap-1"><Thermometer className="w-3 h-3" /> Nhiệt độ</span>
            <span className={`font-bold ${temp >= 40 ? 'text-red-400 animate-pulse' : temp >= 32 ? 'text-amber-400' : 'text-emerald-400'}`}>{temp.toFixed(1)} °C</span>
          </div>
          <div className="flex justify-between items-center bg-zinc-950/80 px-2 py-0.5 rounded border border-zinc-800/60">
            <span className="text-zinc-400 flex items-center gap-1"><Wind className="w-3 h-3" /> Khói</span>
            <span className={`font-bold ${smoke >= 0.5 ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>{smoke.toFixed(1)} %</span>
          </div>
          <div className="flex justify-between items-center bg-zinc-950/80 px-2 py-0.5 rounded border border-zinc-800/60">
            <span className="text-zinc-400 flex items-center gap-1"><Activity className="w-3 h-3" /> CO₂</span>
            <span className={`font-bold ${co2 >= 1000 ? 'text-red-400 animate-pulse' : co2 >= 631 ? 'text-amber-400' : 'text-emerald-400'}`}>{co2.toFixed(0)} ppm</span>
          </div>
        </div>
        <div className="flex justify-between items-center text-[10px] text-zinc-400 pt-1 border-t border-zinc-800/60">
          <span className="flex items-center gap-1"><Bot className="w-3 h-3" /> Robot: <strong className="text-cyan-400">DISPATCHED</strong></span>
          <span className="flex items-center gap-1">Plug: <strong className={isCritical ? 'text-red-400' : 'text-emerald-400'}>{isCritical ? 'POWER OFF' : 'ON'}</strong></span>
        </div>
      </div>
    </div>
  );
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
  const [emergencyPopup, setEmergencyPopup] = useState(null);
  const [controllerState, setControllerState] = useState({ ai_detection_focus: false });

  // Poll Controller State từ Remote Controller (/api/script/state) định kỳ 1s
  useEffect(() => {
    // Đảm bảo tên Tab chính xác để Python script có thể chộp được
    document.title = "DNTU02 CruzrTwin — Digital Twin Fire Safety Monitoring";

    const pollControllerState = async () => {
      try {
        const res = await fetch('/api/script/state');
        if (res.ok) {
          const data = await res.json();
          if (data.state) setControllerState(data.state);
        }
      } catch {
        // ignore offline errors - empty catch is intentional
      }
    };
    pollControllerState();
    const interval = setInterval(pollControllerState, 1000);
    return () => clearInterval(interval);
  }, []);

  const [focusPanel, setFocusPanel] = useState(null);
  const [focusVisible, setFocusVisible] = useState(false);

  useEffect(() => {
    let activePanel = null;
    if (controllerState.sensor_focus) activePanel = 'sensor';
    else if (controllerState.orion_focus) activePanel = 'orion';
    else if (controllerState.ai_detection_focus) activePanel = 'ai_detection';
    else if (controllerState.robot_focus) activePanel = 'robot';
    else if (controllerState.ack_focus) activePanel = 'ack';

    if (activePanel) {
      setFocusPanel(activePanel);
      requestAnimationFrame(() => requestAnimationFrame(() => setFocusVisible(true)));
    } else {
      setFocusVisible(false);
      const t = setTimeout(() => setFocusPanel(null), 300);
      return () => clearTimeout(t);
    }
  }, [controllerState]);

  const resetClickCountRef = useRef(0);
  const resetClickTimerRef = useRef(null);
  const lastAlertIdRef = useRef(null);

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

  // eslint-disable-next-line no-unused-vars
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
  // eslint-disable-next-line no-unused-vars
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

  // eslint-disable-next-line no-unused-vars
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
      if (scenarioType === 'normal' || scenarioType === 'reset_all' || scenarioType === 'undo') {
        setEmergencyPopup(null);
      }
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
    } catch {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-detect CRITICAL/WARNING from AI detection logs and pop the emergency HUD
  useEffect(() => {
    const aiLogs = logs.ai || [];
    if (aiLogs.length === 0) {
      setEmergencyPopup(null);
      return;
    }
    const latest = aiLogs[aiLogs.length - 1];
    const severity = String(latest?.predicted_level || latest?.severity || latest?.device_status || '').toUpperCase();
    const alertId = latest?.source_ai_event_id || latest?.alert_id || latest?.timestamp || '';

    if (severity === 'NORMAL' || severity === 'RESET' || severity === 'OK') {
      setEmergencyPopup(null);
      return;
    }

    if ((severity === 'CRITICAL' || severity === 'WARNING') && alertId !== lastAlertIdRef.current) {
      lastAlertIdRef.current = alertId;
      const zoneId = latest?.zone_id || latest?.room || 'DNTU_ROOM_A101';
      const match = String(zoneId).match(/A(\d+)/);
      let roomId = 'L1-A1';
      let floorIdx = 1;
      if (match) {
        const num = parseInt(match[1]);
        floorIdx = Math.floor(num / 100) || 1;
        const roomNum = num % 100 || num;
        roomId = `L${floorIdx}-A${roomNum}`;
      }
      setEmergencyPopup({ id: roomId, floor: floorIdx });
    }
  }, [logs.ai]);

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
        <div className="flex-1 relative w-full overflow-hidden">
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



          {/* Nút bấm QUAY VỀ TOÀN TÒA NHÀ (Hiển thị nổi bật khi đang xem Phòng hoặc Tầng) */}
          {(activeRoom.id || activeRoom.floor) && (
            <button
              onClick={handleBackToBuilding}
              className="absolute top-6 left-6 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-mono font-bold text-xs rounded-xl shadow-[0_0_20px_rgba(37,99,235,0.7)] border-2 border-blue-300 z-50 cursor-pointer flex items-center gap-2 transition-all hover:scale-105"
            >
              <span className="text-sm">⬅</span>
              <span>BACK TO BUILDING VIEW {activeRoom.id ? `(ROOM ${activeRoom.id})` : `(FLOOR ${activeRoom.floor})`}</span>
            </button>
          )}

          {/* Emergency Pop-up HUD — 3 panel nổi phủ lên vùng 3D (Bọc ErrorBoundary bảo vệ tuyệt đối) */}
          {!activeRoom.id && (
            <ErrorBoundary fallback={null}>
              <EmergencyPopUpHUD
                roomInfo={emergencyPopup}
                sensorData={sensorData}
                onClose={() => setEmergencyPopup(null)}
              />
            </ErrorBoundary>
          )}
        </div>

        <div className="w-full border-t border-zinc-800 bg-zinc-900" style={{ height: bottomPanelHeight }}>
          <div className="flex h-full">
            <div className="flex-shrink-0" style={{ width: `${mapWidthPercent}%` }}>
              {!activeRoom.id ? (
                <Map2D
                  activeFloorIdx={activeRoom.floor}
                  activeRoomId={activeRoom.id}
                  sensorData={sensorData}
                  onRoomClick={handleRoomClick}
                />
              ) : (
                <RoomDetailBottomBar
                  roomId={activeRoom.id}
                  floorIdx={activeRoom.floor}
                  sensorData={sensorData}
                />
              )}
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
                    <span className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> WEBHOOK OFFLINE - CLICK TO START SERVER</span>
                  </button>
                )}

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

              {ackMessage && (
                <div className={`w-full max-w-[260px] text-[10px] font-mono text-center ${ackStatus === 'error' ? 'text-red-400' : ackStatus === 'success' ? 'text-emerald-400' : 'text-zinc-500'}`}>
                  {ackMessage}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <div
        className="h-full bg-[#0a0a0c] border-l border-zinc-800 flex flex-col overflow-hidden shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-40 relative flex-shrink-0"
        style={{ width: sidebarWidth }}
      >
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

      {/* FULL-SCREEN FOCUS MODAL FOR LOG PANELS (Sensor, Orion, AI, Robot) */}
      {focusPanel && (
        <div
          className={`fixed inset-0 z-[100] flex items-center justify-center p-6 transition-all duration-300 ease-out ${focusVisible
            ? 'bg-black/80 backdrop-blur-md opacity-100'
            : 'bg-black/0 backdrop-blur-none opacity-0'
            }`}
        >
          <div
            className={`bg-[#0c0c0e] border border-zinc-800 rounded-xl p-4 w-full max-w-4xl shadow-2xl flex flex-col h-[75vh] max-h-[80vh] overflow-hidden transition-all duration-350 cubic-bezier(0.16, 1, 0.3, 1) transform origin-[85%_55%] ${focusVisible
              ? 'scale-100 opacity-100 translate-x-0 translate-y-0'
              : 'scale-0 opacity-0 translate-x-24 translate-y-8 pointer-events-none'
              }`}
          >
            {focusPanel === 'sensor' && (
              <LogPanel title="SENSORS" data={roomLogs.sensors} height="100%" showNormal={showNormalLogs} emptyMessage="Chưa có dữ liệu Sensor..." />
            )}
            {focusPanel === 'orion' && (
              <LogPanel title="ORION_STATE" data={roomLogs.state} height="100%" showNormal={showNormalLogs} emptyMessage="Chưa có dữ liệu Orion..." />
            )}
            {focusPanel === 'ai_detection' && (
              <LogPanel title="AI_DETECTION" data={logs.ai} height="100%" showNormal={showNormalLogs} emptyMessage="Chưa có dữ liệu AI Detection..." />
            )}
            {focusPanel === 'robot' && (
              <LogPanel title="ROBOT_ACTION" data={roomLogs.robot} height="100%" showNormal={showNormalLogs} emptyMessage="Chưa có dữ liệu Robot Action..." />
            )}
            {focusPanel === 'ack' && (
              <LogPanel title="OPERATOR_ACK" data={roomLogs.ack} height="100%" showNormal={showNormalLogs} emptyMessage="Chưa có dữ liệu Operator Ack..." />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
