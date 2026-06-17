import { useState, useEffect } from 'react';
import ThreeScene from '../components/ThreeScene';
import LogPanel from '../components/LogPanel';
import Map2D from '../components/Map2D';

export default function Dashboard() {
  const [activeRoom, setActiveRoom] = useState({ id: null, floor: null });
  const [sensorData, setSensorData] = useState({});
  const [logs, setLogs] = useState({ ai: [], alerts: [], robot: [], state: [], sensors: [] });

  // Polling data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dbRes, aiRes, alertsRes, robotRes, stateRes, sensorsRes] = await Promise.all([
          fetch('/api/db/sensors'),
          fetch('/api/logs/ai'),
          fetch('/api/logs/alerts'),
          fetch('/api/logs/robot'),
          fetch('/api/logs/state'),
          fetch('/api/logs/sensors'),
        ]);

        if (dbRes.ok) setSensorData(await dbRes.json());
        
        const aiData = aiRes.ok ? await aiRes.json() : null;
        const alertsData = alertsRes.ok ? await alertsRes.json() : null;
        const robotData = robotRes.ok ? await robotRes.json() : null;
        const stateData = stateRes.ok ? await stateRes.json() : null;
        const sensorsData = sensorsRes.ok ? await sensorsRes.json() : null;

        setLogs(prev => ({
          ...prev,
          ai: aiData || prev.ai,
          alerts: alertsData || prev.alerts,
          robot: robotData || prev.robot,
          state: stateData || prev.state,
          sensors: sensorsData || prev.sensors
        }));
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleRoomClick = (roomId, floorIdx) => {
    setActiveRoom({ id: roomId, floor: floorIdx });
  };

  const handleBackToBuilding = () => {
    setActiveRoom({ id: null, floor: null });
  };

  return (
    <div className="w-full h-full flex flex-col md:flex-row overflow-hidden bg-black">
      {/* LÃ¡t cáº¯t 3D (TrÃ¡i) */}
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
              className="absolute top-20 left-6 px-6 py-3 bg-red-600/90 hover:bg-red-500 text-white font-bold font-mono text-sm rounded shadow-[0_0_20px_rgba(220,38,38,0.4)] transition-all border border-red-400 z-40 cursor-pointer flex items-center gap-2 backdrop-blur-sm"
            >
              QUAY LẠI TÒA NHÀ (ESC)
            </button>
          )}

          {/* Panel thÃ´ng tin phÃ²ng */}
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
                  <span className="font-bold text-lg text-emerald-400">
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
        
        {/* Sơ đồ 2D */}
        {!activeRoom.id && (
          <Map2D 
            activeFloorIdx={activeRoom.floor} 
            activeRoomId={activeRoom.id} 
            sensorData={sensorData} 
          />
        )}
      </main>

      {/* LÃ¡t cáº¯t Logs (Pháº£i) */}
      <aside className="w-full md:w-[400px] lg:w-[450px] h-full bg-[#0a0a0c] border-l border-zinc-800 flex flex-col overflow-hidden shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-40 relative">
        <LogPanel title="AI_DETECTION" data={logs.ai} color="blue" height="h-1/5" />
        <LogPanel title="ALERT_EVENTS" data={logs.alerts} color="red" height="h-1/5" />
        <LogPanel title="ROBOT_ACTIONS" data={logs.robot} color="amber" height="h-1/5" />
        <LogPanel title="ORION_STATE" data={logs.state} color="purple" height="h-1/5" />
        <LogPanel title="RAW_SENSORS" data={logs.sensors} color="emerald" height="h-1/5" />
      </aside>
    </div>
  );
}
