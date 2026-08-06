import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const BUTTON_CONFIGS = [
  { id: 'btn_1', slot: '01', title: '🔊 Phát Thoại Giới Thiệu', desc: 'Robot Cruzr chào & giới thiệu DNTU CruzrTwin', color: 'from-blue-600/30 to-blue-900/50 border-blue-400/80 hover:border-blue-300 text-blue-300 shadow-[0_0_15px_rgba(59,130,246,0.3)]' },
  { id: 'btn_2', slot: '02', title: '👁️ Focus AI Detection', desc: 'Bật/Tắt hiển thị Zoom AI Detection trên Dashboard', color: 'from-cyan-600/30 to-cyan-900/50 border-cyan-400/80 hover:border-cyan-300 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.3)]' },
  { id: 'btn_3', slot: '03', title: '🟢 Kịch Bản Normal', desc: 'Phát dữ liệu Normal & Khôi phục thiết bị IoT', color: 'from-emerald-600/30 to-emerald-900/50 border-emerald-400/80 hover:border-emerald-300 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]' },
  { id: 'btn_4', slot: '04', title: '🟡 Kịch Bản Warning', desc: 'Phát dữ liệu Cảnh Báo Warning (Nhiệt độ/CO2)', color: 'from-amber-600/30 to-amber-900/50 border-amber-400/80 hover:border-amber-300 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)]' },

  { id: 'btn_5', slot: '05', title: '🔴 1. Critical (Chỉ Log)', desc: 'Phát log Báo Động Đỏ Critical & chưa gọi Robot', color: 'from-rose-600/30 to-rose-900/50 border-rose-400/80 hover:border-rose-300 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.3)]' },
  { id: 'btn_6', slot: '06', title: '🤖 2. Kích Hoạt Robot & IoT', desc: 'Gọi Robot Cruzr phát thoại sơ tán & ngắt điện IoT', color: 'from-purple-600/30 to-purple-900/50 border-purple-400/80 hover:border-purple-300 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.3)]' },
  { id: 'btn_7', slot: '07', title: 'Script 07', desc: 'Chờ phân công tính năng', color: 'from-slate-600/20 to-slate-900/40 border-slate-500/50 hover:border-slate-400 text-slate-400' },
  { id: 'btn_8', slot: '08', title: 'Script 08', desc: 'Chờ phân công tính năng', color: 'from-zinc-600/20 to-zinc-900/40 border-zinc-500/50 hover:border-zinc-400 text-zinc-400' },

  { id: 'btn_9', slot: '09', title: 'Script 09', desc: 'Chờ phân công tính năng', color: 'from-neutral-600/20 to-neutral-900/40 border-neutral-500/50 hover:border-neutral-400 text-neutral-400' },
  { id: 'btn_10', slot: '10', title: '💡 Khôi Phục Điện Tuya Plugs (ON)', desc: 'Bật toàn bộ ổ cắm thông minh Tuya Smart Plugs (Nút 14)', color: 'from-emerald-600/30 to-emerald-900/50 border-emerald-400/80 hover:border-emerald-300 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]' },
  { id: 'btn_11', slot: '11', title: '⚡ Ngắt Điện Tuya Plugs (OFF)', desc: 'Tắt toàn bộ ổ cắm thông minh Tuya Smart Plugs (Nút 15)', color: 'from-amber-600/30 to-amber-900/50 border-amber-400/80 hover:border-amber-300 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)]' },
  { id: 'btn_12', slot: '12', title: '🔌 Test Kết Nối Robot', desc: 'Kiểm tra trạng thái ping & kết nối tới Robot Cruzr (Nút 16)', color: 'from-pink-600/30 to-pink-900/50 border-pink-400/80 hover:border-pink-300 text-pink-300 shadow-[0_0_15px_rgba(236,72,153,0.3)]' },
];

export default function NavigateBack() {
  const navigate = useNavigate();
  const [activeBtn, setActiveBtn] = useState(null);
  const [lastResponse, setLastResponse] = useState(null);
  const [loadingBtn, setLoadingBtn] = useState(null);
  const [successBtns, setSuccessBtns] = useState({}); // { btn_id: boolean }
  const [commandHistory, setCommandHistory] = useState([]);

  // Fetch command history periodically
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/api/script/history');
        if (res.ok) {
          const data = await res.json();
          if (data.history) setCommandHistory(data.history);
        }
      } catch (err) {
        // ignore offline errors
      }
    };
    fetchHistory();
    const interval = setInterval(fetchHistory, 3000);
    return () => clearInterval(interval);
  }, []);

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
      const isOk = res.ok && data.success !== false;

      const respObj = {
        button_id: btn.id,
        slot: btn.slot,
        name: data.name || btn.title,
        message: data.message || 'Thực thi thành công!',
        success: isOk,
        latencyMs: latency,
        time: new Date().toLocaleTimeString()
      };

      setLastResponse(respObj);

      if (isOk) {
        // Đánh dấu nút vừa kích hoạt thành công trong 3 giây
        setSuccessBtns(prev => ({ ...prev, [btn.id]: true }));
        setTimeout(() => {
          setSuccessBtns(prev => ({ ...prev, [btn.id]: false }));
        }, 3500);

        // Add to local history instantly
        setCommandHistory(prev => [
          { timestamp: respObj.time, button_id: btn.id, name: respObj.name, status: 'SUCCESS 200 OK', details: respObj.message },
          ...prev.slice(0, 20)
        ]);
      }
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
    <div className="w-screen h-screen overflow-hidden bg-[#07090e] text-white font-mono flex flex-col justify-between p-5 select-none relative">
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
          <span>SERVER STATUS:</span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold text-[11px]">
            CONNECTED (PORT 5000)
          </span>
        </div>
      </header>

      {/* Main 3x4 Grid (12 Action Buttons) */}
      <main className="flex-1 my-4 grid grid-cols-4 grid-rows-3 gap-4 z-10">
        {BUTTON_CONFIGS.map((btn) => {
          const isLoading = loadingBtn === btn.id;
          const isActive = activeBtn === btn.id;
          const isSuccess = successBtns[btn.id];

          return (
            <button
              key={btn.id}
              onClick={() => handleTriggerScript(btn)}
              disabled={isLoading}
              className={`relative group rounded-2xl p-4 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between overflow-hidden shadow-xl ${
                isSuccess
                  ? 'from-emerald-600/30 to-emerald-950/60 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse'
                  : btn.color
              } ${isActive ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
            >
              {/* Card Header: Slot Tag & Status indicator */}
              <div className="flex items-center justify-between w-full">
                <span className={`px-2.5 py-1 text-[10px] font-bold rounded-md border ${
                  isSuccess ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200' : 'bg-black/60 border-white/10 text-zinc-300'
                }`}>
                  SLOT {btn.slot}
                </span>

                {isSuccess ? (
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500 text-black animate-bounce">
                    SENT SUCCESS ✅
                  </span>
                ) : (
                  <span className={`w-2.5 h-2.5 rounded-full ${isLoading ? 'bg-amber-400 animate-ping' : isActive ? 'bg-cyan-400 animate-pulse' : 'bg-zinc-600'}`} />
                )}
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
                <span className={`text-xs font-bold ${isSuccess ? 'text-emerald-300' : 'text-zinc-300'} group-hover:translate-x-1 transition-transform`}>
                  {isLoading ? '⏳ EXECUTING...' : isSuccess ? '✅ EXECUTED 200 OK' : 'RUN SCRIPT ➔'}
                </span>
              </div>
            </button>
          );
        })}
      </main>

      {/* Footer Execution Log Bar */}
      <footer className="z-10 bg-zinc-950/90 p-3 rounded-xl border border-zinc-800/80 text-xs font-mono flex flex-col gap-2 shadow-2xl">
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
          <div className="flex items-center gap-3">
            <span className="text-zinc-500 font-bold">TRẠNG THÁI GỬI LỆNH GẦN NHẤT:</span>
            {lastResponse ? (
              <span className={`font-bold flex items-center gap-2 ${lastResponse.success ? 'text-emerald-400' : 'text-red-400'}`}>
                <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-700">[{lastResponse.time}]</span>
                <span className="text-cyan-400">SLOT {lastResponse.slot} ({lastResponse.name}):</span>
                <span>{lastResponse.message}</span>
              </span>
            ) : (
              <span className="text-zinc-600 italic">Chưa gửi lệnh nào. Click vào 1 trong 12 nút ở trên để gửi lệnh kích chạy script.</span>
            )}
          </div>

          {lastResponse && (
            <div className="text-[11px] text-zinc-400 font-bold bg-zinc-900 px-2.5 py-1 rounded-lg border border-zinc-800">
              HTTP STATUS: <span className="text-emerald-400">200 OK</span> | LATENCY: <span className="text-cyan-400">{lastResponse.latencyMs} ms</span>
            </div>
          )}
        </div>

        {/* Live Execution History Log */}
        {commandHistory.length > 0 && (
          <div className="flex items-center gap-2 text-[11px] overflow-x-auto custom-scrollbar pt-1 text-zinc-400">
            <span className="text-zinc-500 font-bold flex-shrink-0">LỊCH SỬ GỬI:</span>
            <div className="flex items-center gap-2 overflow-x-auto whitespace-nowrap">
              {commandHistory.slice(0, 3).map((item, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-zinc-900/90 rounded border border-emerald-500/30 text-emerald-300 text-[10px]">
                  [{item.timestamp}] {item.button_id} ({item.name}): {item.status}
                </span>
              ))}
            </div>
          </div>
        )}
      </footer>
    </div>
  );
}
