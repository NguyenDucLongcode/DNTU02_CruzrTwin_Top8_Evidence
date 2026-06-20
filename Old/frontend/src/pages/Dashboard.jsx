import { useState, useEffect, useMemo } from 'react';
import ThreeScene from '../components/ThreeScene';
import LogPanel from '../components/LogPanel';
import Map2D from '../components/Map2D';

const LOG_TYPES = ['ai', 'alerts', 'robot', 'state', 'sensors', 'ack'];
const EMPTY_LOGS = { ai: [], alerts: [], robot: [], state: [], sensors: [], ack: [] };

const ROOM_TO_ZONE = {
  'L1-A1': 'DNTU_ROOM_A101',
  'L1-A2': 'DNTU_ROOM_A102',
  'L1-A3': 'DNTU_ROOM_A103',
  'L1-A4': 'DNTU_ROOM_A104',
  'L1-A5': 'DNTU_ROOM_A105',
  'L1-A6': 'DNTU_ROOM_A106',
  'L1-A7': 'DNTU_ROOM_A107',
  'L1-A8': 'DNTU_ROOM_A108',
  'L1-A9': 'DNTU_ROOM_A109',
  'L1-A10': 'DNTU_ROOM_A110',
  'L1-A11': 'DNTU_ROOM_A111',
  'L1-A12': 'DNTU_ROOM_A112'
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

  const selectedZoneId = getRoomZoneId(activeRoom.id);
  const displayRoomLabel = activeRoom.id || 'TẤT CẢ PHÒNG';

  const roomLogs = useMemo(() => ({
    ai: filterLogsByRoom(logs.ai, selectedZoneId),
    alerts: filterLogsByRoom(logs.alerts, selectedZoneId),
    robot: filterLogsByRoom(logs.robot, selectedZoneId),
    state: filterLogsByRoom(logs.state, selectedZoneId),
    sensors: filterLogsByRoom(logs.sensors, selectedZoneId),
    ack: filterLogsByRoom(logs.ack, selectedZoneId)
  }), [logs, selectedZoneId]);

  const latestRoomRobotAction = useMemo(() => (
    getLatestRoomLog(roomLogs.robot, selectedZoneId, (log) => Boolean(log.robot_action_id))
  ), [roomLogs.robot, selectedZoneId]);

  const latestRoomAlert = useMemo(() => (
    getLatestRoomLog(roomLogs.alerts, selectedZoneId, (log) => Boolean(log.alert_id))
  ), [roomLogs.alerts, selectedZoneId]);

  const latestRoomAi = useMemo(() => (
    getLatestRoomLog(roomLogs.ai, selectedZoneId, () => true)
  ), [roomLogs.ai, selectedZoneId]);

  const getAckBase = () => {
    if (latestRoomRobotAction) return latestRoomRobotAction;
    if (latestRoomAlert) return latestRoomAlert;
    if (latestRoomAi) return latestRoomAi;
    return {};
  };

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
        note: decision === 'ACK'
          ? 'Operator confirmed Cruzr guidance delivered.'
          : 'Operator reported an issue with Cruzr guidance.'
      };

      const response = await fetch('/api/operator/ack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `ACK failed with HTTP ${response.status}`);
      }

      setAckStatus('success');
      setAckMessage(`${decision === 'ACK' ? 'Đã xác nhận ACK' : 'Đã báo lỗi ERROR'}: ${result.status || decision}`);
    } catch (err) {
      setAckStatus('error');
      setAckMessage(err.message || 'Không thể gửi ACK.');
    }
  };

  useEffect(() => {
    let cancelled = false;

    const fetchJson = async (path) => {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`${path} trả về HTTP ${response.status}`);
      }
      return response.json();
    };

    const loadLog = async (type) => {
      try {
        const data = await fetchJson(`/api/logs/${type}`);
        if (!cancelled) {
          setLogs((prev) => ({ ...prev, [type]: data }));
          setLogErrors((prev) => ({ ...prev, [type]: null }));
        }
      } catch (err) {
        if (!cancelled) {
          setLogErrors((prev) => ({ ...prev, [type]: err.message }));
        }
      }
    };

    const fetchData = async () => {
      await Promise.all(LOG_TYPES.map(loadLog));

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
  const latestActionText = latestRoomRobotAction
    ? `${latestRoomRobotAction.robot_action_id || 'RobotAction'}`
    : 'Chưa có RobotAction gần nhất';

  return (
    <div className="w-full h-full flex flex-col md:flex-row overflow-hidden bg-black">
      <main className="flex-1 relative h-full flex flex-col">
        <div className="flex-1 relative w-full">
          <ThreeScene
            activeRoomId={activeRoom.id}
            activeFloorIdx={activeRoom.floor}
            onRoomClick={handleRoomClick}
            sensorData={sensorData}
          />

          {activeRoom.id && (
            <button
              onClick={handleBackToBuilding}
              className="absolute top-20 left-6 px-5 py-2 bg-red-600/90 hover:bg-red-500 text-white font-bold font-mono text-xs rounded shadow-[0_0_20px_rgba(220,38,38,0.4)] transition-all border border-red-400 z-40 cursor-pointer"
            >
              QUAY LẠI TÒA NHÀ
            </button>
          )}

          {activeRoom.id && (
            <div className="absolute bottom-8 left-6 bg-black/80 backdrop-blur-xl border border-blue-500/50 rounded-xl p-5 shadow-2xl shadow-blue-500/20 z-40 font-mono min-w-[280px]">
              <div className="text-xl font-bold text-blue-400 mb-4 border-b border-blue-500/30 pb-2">
                PHÒNG {activeRoom.id} (Tầng {activeRoom.floor})
              </div>

              {sensorData[activeRoom.id] ? (
                <div className="flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Nhiệt độ:</span>
                    <span className={`font-bold text-lg ${sensorData[activeRoom.id].temp >= 40 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {(sensorData[activeRoom.id].temp || 0).toFixed(1)} °C
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Khói:</span>
                    <span className={`font-bold text-lg ${sensorData[activeRoom.id].smoke > 0 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {(sensorData[activeRoom.id].smoke || 0).toFixed(1)} %
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">CO2:</span>
                    <span className={`font-bold text-lg ${sensorData[activeRoom.id].co2 >= 900 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {(sensorData[activeRoom.id].co2 || 0).toFixed(1)} ppm
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-zinc-500 font-bold">Chưa có dữ liệu cảm biến</div>
              )}
            </div>
          )}
        </div>

        {!activeRoom.id && (
          <div className="w-full flex border-t border-zinc-800 bg-black/50 min-h-[200px]">
            <div className="w-3/4 border-r border-zinc-800">
              <Map2D
                activeFloorIdx={activeRoom.floor}
                activeRoomId={activeRoom.id}
                sensorData={sensorData}
              />
            </div>
            <div className="w-1/4 p-4 flex flex-col justify-center items-center gap-3 relative overflow-hidden bg-zinc-950">
              <div className="text-[10px] text-zinc-500 font-mono text-center tracking-wider">HỆ THỐNG VẬN HÀNH</div>
              <button
                onClick={() => handleOperatorAck('ACK')}
                disabled={ackStatus === 'loading'}
                className="w-full max-w-[120px] h-8 bg-emerald-900/40 hover:bg-emerald-600/60 border border-emerald-500/50 hover:border-emerald-400 text-emerald-300 hover:text-white font-mono font-bold text-[10px] rounded-lg shadow-[0_0_12px_rgba(16,185,129,0.18)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all flex items-center justify-center gap-1 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ACK
              </button>
              {ackMessage && (
                <div className={`w-full max-w-[180px] text-[10px] font-mono text-center ${ackStatus === 'error' ? 'text-red-400' : ackStatus === 'success' ? 'text-emerald-400' : 'text-zinc-500'}`}>
                  {ackMessage}
                </div>
              )}
              <div className="w-full max-w-[180px] text-[10px] text-zinc-600 font-mono text-center">
                {latestActionText}
              </div>
            </div>
          </div>
        )}
      </main>

      <aside className="w-full md:w-[400px] lg:w-[450px] h-full bg-[#0a0a0c] border-l border-zinc-800 flex flex-col overflow-hidden shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-40 relative">
        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-950/80 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[10px] tracking-widest text-zinc-500 font-mono">LOG THEO PHÒNG</div>
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
            Một số API log chưa lấy được dữ liệu. Kiểm tra backend Flask cổng 5000.
          </div>
        )}

        <LogPanel title="AI_DETECTION" data={roomLogs.ai} height="flex-1 min-h-0" showNormal={showNormalLogs} emptyMessage={selectedZoneId ? `Chưa có log AI cho ${activeRoom.id}.` : 'Chưa có log AI.'} />
        <LogPanel title="ALERT_EVENTS" data={roomLogs.alerts} height="flex-1 min-h-0" showNormal={showNormalLogs} emptyMessage={selectedZoneId ? `Chưa có alert cho ${activeRoom.id}.` : 'Chưa có alert.'} />
        <LogPanel title="ROBOT_ACTIONS" data={roomLogs.robot} height="flex-1 min-h-0" showNormal={showNormalLogs} emptyMessage={selectedZoneId ? `Chưa có robot action cho ${activeRoom.id}.` : 'Chưa có robot action.'} />
        <LogPanel title="ORION_STATE" data={roomLogs.state} height="flex-1 min-h-0" showNormal={showNormalLogs} emptyMessage={selectedZoneId ? `Chưa có Orion state cho ${activeRoom.id}.` : 'Chưa có Orion state.'} />
        <LogPanel title="RAW_SENSORS" data={roomLogs.sensors} height="flex-1 min-h-0" showNormal={showNormalLogs} emptyMessage={selectedZoneId ? `Chưa có raw sensor cho ${activeRoom.id}.` : 'Chưa có raw sensor.'} />
      </aside>
    </div>
  );
}
