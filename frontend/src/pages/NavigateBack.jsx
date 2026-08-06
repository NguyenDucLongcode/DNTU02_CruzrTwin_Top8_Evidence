import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const BUTTON_CONFIGS = [
  { id: 'btn_1', slot: '01', title: 'Script 01', desc: 'Chờ phân công tính năng', color: 'from-blue-600/20 to-blue-900/40 border-blue-500/50 hover:border-blue-400 text-blue-400' },
  { id: 'btn_2', slot: '02', title: 'Script 02', desc: 'Chờ phân công tính năng', color: 'from-cyan-600/20 to-cyan-900/40 border-cyan-500/50 hover:border-cyan-400 text-cyan-400' },
  { id: 'btn_3', slot: '03', title: 'Script 03', desc: 'Chờ phân công tính năng', color: 'from-emerald-600/20 to-emerald-900/40 border-emerald-500/50 hover:border-emerald-400 text-emerald-400' },
  { id: 'btn_4', slot: '04', title: 'Script 04', desc: 'Chờ phân công tính năng', color: 'from-teal-600/20 to-teal-900/40 border-teal-500/50 hover:border-teal-400 text-teal-400' },

  { id: 'btn_5', slot: '05', title: 'Script 05', desc: 'Chờ phân công tính năng', color: 'from-indigo-600/20 to-indigo-900/40 border-indigo-500/50 hover:border-indigo-400 text-indigo-400' },
  { id: 'btn_6', slot: '06', title: 'Script 06', desc: 'Chờ phân công tính năng', color: 'from-purple-600/20 to-purple-900/40 border-purple-500/50 hover:border-purple-400 text-purple-400' },
  { id: 'btn_7', slot: '07', title: 'Script 07', desc: 'Chờ phân công tính năng', color: 'from-pink-600/20 to-pink-900/40 border-pink-500/50 hover:border-pink-400 text-pink-400' },
  { id: 'btn_8', slot: '08', title: 'Script 08', desc: 'Chờ phân công tính năng', color: 'from-amber-600/20 to-amber-900/40 border-amber-500/50 hover:border-amber-400 text-amber-400' },

  { id: 'btn_9', slot: '09', title: 'Script 09', desc: 'Chờ phân công tính năng', color: 'from-rose-600/20 to-rose-900/40 border-rose-500/50 hover:border-rose-400 text-rose-400' },
  { id: 'btn_10', slot: '10', title: 'Script 10', desc: 'Chờ phân công tính năng', color: 'from-red-600/20 to-red-900/40 border-red-500/50 hover:border-red-400 text-red-400' },
  { id: 'btn_11', slot: '11', title: 'Script 11', desc: 'Chờ phân công tính năng', color: 'from-orange-600/20 to-orange-900/40 border-orange-500/50 hover:border-orange-400 text-orange-400' },
  { id: 'btn_12', slot: '12', title: 'Script 12', desc: 'Chờ phân công tính năng', color: 'from-yellow-600/20 to-yellow-900/40 border-yellow-500/50 hover:border-yellow-400 text-yellow-400' },
];

export default function NavigateBack() {
  const navigate = useNavigate();
  const [activeBtn, setActiveBtn] = useState(null);
  const [lastResponse, setLastResponse] = useState(null);
  const [loadingBtn, setLoadingBtn] = useState(null);

  const handleBackToDashboard = () => {
    navigate('/');
  };

  const handleTriggerScript = async (btn) => {
    try {
      setLoadingBtn(btn.id);
      setActiveBtn(btn.id);

      const t0 = performance.now();
      const res = await fetch('/api/script/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ button_id: btn.id, timestamp: new Date().toISOString() })
      });
      const t1 = performance.now();
      const latency = Math.round(t1 - t0);

      const data = await res.json();
      setLastResponse({
        button_id: btn.id,
        slot: btn.slot,
        name: data.name || btn.title,
        message: data.message || 'Thực thi thành công!',
        success: data.success !== false,
        latencyMs: latency,
        time: new Date().toLocaleTimeString()
      });
    } catch (err) {
      setLastResponse({
        button_id: btn.id,
        slot: btn.slot,
        name: btn.title,
        message: `Lỗi kết nối: ${err.message}`,
        success: false,
        latencyMs: 0,
        time: new Date().toLocaleTimeString()
      });
    } finally {
      setLoadingBtn(null);
    }
  };

  return (
    <div className="w-screen h-screen overflow-hidden bg-[#07090e] text-white font-mono flex flex-col justify-between p-6 select-none relative">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Bar */}
      <header className="flex items-center justify-between z-10 bg-zinc-950/80 p-4 rounded-2xl border border-zinc-800/80 shadow-2xl backdrop-blur-md">
        <button
          onClick={handleBackToDashboard}
          className="px-5 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-cyan-400 hover:text-white font-bold text-xs rounded-xl border border-cyan-500/40 hover:border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)] transition-all cursor-pointer flex items-center gap-2"
        >
          <span className="text-sm">🖥️</span>
          <span>BACK TO DASHBOARD</span>
        </button>

        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          <h1 className="text-base md:text-lg font-bold tracking-wider text-white">
            ⚡ CRUZRTWIN REMOTE SCRIPT CONTROLLER
          </h1>
          <span className="px-2.5 py-1 text-[10px] rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
            12 BUTTON SLOTS READY
          </span>
        </div>

        <div className="text-xs text-zinc-400 flex items-center gap-2">
          <span>STATUS:</span>
          <span className="text-emerald-400 font-bold">ONLINE</span>
        </div>
      </header>

      {/* Main 3x4 Grid (12 Action Buttons) */}
      <main className="flex-1 my-6 grid grid-cols-4 grid-rows-3 gap-5 z-10">
        {BUTTON_CONFIGS.map((btn) => {
          const isLoading = loadingBtn === btn.id;
          const isActive = activeBtn === btn.id;

          return (
            <button
              key={btn.id}
              onClick={() => handleTriggerScript(btn)}
              disabled={isLoading}
              className={`relative group rounded-2xl p-5 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between overflow-hidden shadow-xl ${btn.color} ${
                isActive ? 'ring-2 ring-cyan-400 scale-[0.98]' : 'hover:scale-[1.02]'
              }`}
            >
              {/* Card Header: Slot Tag & Status indicator */}
              <div className="flex items-center justify-between w-full">
                <span className="px-2.5 py-1 text-[10px] font-bold rounded-md bg-black/60 border border-white/10 text-zinc-300">
                  SLOT {btn.slot}
                </span>
                <span className={`w-2.5 h-2.5 rounded-full ${isLoading ? 'bg-amber-400 animate-ping' : isActive ? 'bg-cyan-400 animate-pulse' : 'bg-zinc-600'}`} />
              </div>

              {/* Card Body: Title & Subtitle */}
              <div className="text-left my-2">
                <div className="text-base md:text-lg font-bold tracking-wide text-white group-hover:text-cyan-300 transition-colors">
                  {btn.title}
                </div>
                <div className="text-[11px] text-zinc-400 mt-1 line-clamp-1">
                  {btn.desc}
                </div>
              </div>

              {/* Card Footer: Action State */}
              <div className="flex items-center justify-between w-full pt-2 border-t border-white/10 text-[10px]">
                <span className="text-zinc-500 font-mono">ID: {btn.id}</span>
                <span className="text-xs font-bold text-zinc-300 group-hover:translate-x-1 transition-transform">
                  {isLoading ? 'EXECUTING...' : 'RUN SCRIPT ➔'}
                </span>
              </div>
            </button>
          );
        })}
      </main>

      {/* Footer Execution Log Bar */}
      <footer className="z-10 bg-zinc-950/90 p-3 rounded-xl border border-zinc-800/80 text-xs font-mono flex items-center justify-between min-h-[46px]">
        <div className="flex items-center gap-3">
          <span className="text-zinc-500">LAST RESPONSE:</span>
          {lastResponse ? (
            <span className={`font-bold flex items-center gap-2 ${lastResponse.success ? 'text-emerald-400' : 'text-red-400'}`}>
              <span>[{lastResponse.time}]</span>
              <span>SLOT {lastResponse.slot} ({lastResponse.name}):</span>
              <span>{lastResponse.message}</span>
            </span>
          ) : (
            <span className="text-zinc-600 italic">Sẵn sàng nhận lệnh kích hoạt nút từ Operator...</span>
          )}
        </div>

        {lastResponse && (
          <div className="text-[10px] text-zinc-500 font-bold">
            LATENCY: <span className="text-cyan-400">{lastResponse.latencyMs} ms</span>
          </div>
        )}
      </footer>
    </div>
  );
}