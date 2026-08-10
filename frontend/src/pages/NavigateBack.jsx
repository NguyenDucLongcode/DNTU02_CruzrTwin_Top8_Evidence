import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const BUTTON_CONFIGS = [
  { id: 'btn_1', slot: '01', title: '🔊 Phát Thoại Giới Thiệu', desc: 'Robot Cruzr chào & giới thiệu DNTU CruzrTwin', color: 'from-blue-600/30 to-blue-900/50 border-blue-400/80 hover:border-blue-300 text-blue-300 shadow-[0_0_15px_rgba(59,130,246,0.3)]' },
  { id: 'btn_2', slot: '02', title: '👁️ Focus AI Detection', desc: 'Bật/Tắt hiển thị Zoom AI Detection trên Dashboard', color: 'from-cyan-600/30 to-cyan-900/50 border-cyan-400/80 hover:border-cyan-300 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.3)]' },
  { id: 'btn_3', slot: '03', title: '🟢 Kịch Bản Normal', desc: 'Phát dữ liệu Normal & Khôi phục thiết bị IoT', color: 'from-emerald-600/30 to-emerald-900/50 border-emerald-400/80 hover:border-emerald-300 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]' },
  { id: 'btn_4', slot: '04', title: '🟡 Kịch Bản Warning', desc: 'Phát dữ liệu Cảnh Báo Warning (Nhiệt độ/CO2)', color: 'from-amber-600/30 to-amber-900/50 border-amber-400/80 hover:border-amber-300 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)]' },

  { id: 'btn_5', slot: '05', title: '🔴 1. Critical (Chỉ Log)', desc: 'Phát log Báo Động Đỏ Critical & chưa gọi Robot', color: 'from-rose-600/30 to-rose-900/50 border-rose-400/80 hover:border-rose-300 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.3)]' },
  { id: 'btn_6', slot: '06', title: '🤖 2. Kích Hoạt Robot & IoT', desc: 'Gọi Robot Cruzr phát thoại sơ tán & ngắt điện IoT', color: 'from-purple-600/30 to-purple-900/50 border-purple-400/80 hover:border-purple-300 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.3)]' },
  { id: 'btn_7', slot: '07', title: '🎉 Phát Thoại Outro (Cảm Ơn)', desc: 'Robot Cruzr chào cảm ơn & kết thúc phần thi (speak_outro.py)', color: 'from-violet-600/30 to-violet-900/50 border-violet-400/80 hover:border-violet-300 text-violet-300 shadow-[0_0_15px_rgba(139,92,246,0.3)]' },
  { id: 'btn_8', slot: '08', title: '🛑 Dừng Di Chuyển Robot', desc: 'Ngắt di chuyển bánh xe Robot ngay lập tức (Vẫn giữ thoại, log & IoT)', color: 'from-red-600/30 to-red-900/50 border-red-400/80 hover:border-red-300 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.3)]' },

  { id: 'btn_9', slot: '09', title: '🔄 Reset Demo System', desc: 'Ấn 1 lần: Undo 1 log | Ấn 3 lần nhanh: Reset All System', color: 'from-teal-600/30 to-teal-900/50 border-teal-400/80 hover:border-teal-300 text-teal-300 shadow-[0_0_15px_rgba(20,184,166,0.3)]' },
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

  const resetClickCountRef = useRef(0);
  const resetClickTimerRef = useRef(null);

  // Fetch command history periodically & auto detect Server status
  useEffect(() => {
    const checkServerStatus = async () => {
      try {
        const res = await fetch('/api/script/history');
        if (res.ok) {
          setIsServerRunning(true);
          const data = await res.json();
          if (data.history) setCommandHistory(data.history);
        } else {
          setIsServerRunning(false);
        }
      } catch (err) {
        setIsServerRunning(false);
      }
    };
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 2500);
    return () => clearInterval(interval);
  }, []);

  // Điều khiển Slide HTML bằng phím mũi tên từ trang NavigateBack
  useEffect(() => {
    const handleKeyDown = (e) => {
      const channel = new BroadcastChannel('cruzrtwin_sync');
      if (e.key === 'ArrowRight' || e.key === ' ') {
        channel.postMessage({ type: 'SLIDE_NEXT' });
      } else if (e.key === 'ArrowLeft') {
        channel.postMessage({ type: 'SLIDE_PREV' });
      }
      // Clean up channel after send
      channel.close();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const [isMovementPaused, setIsMovementPaused] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [isServerRunning, setIsServerRunning] = useState(true);
  const [resetClickBadge, setResetClickBadge] = useState('');

  const handleStopServer = async () => {
    try {
      // Gọi Flask API /api/system/stop để ngắt (kill) tiến trình Python py src/fiware/webhook_receiver.py (giống Ctrl+C)
      await fetch('/api/system/stop', { method: 'POST' });
    } catch (err) {
      // Bỏ qua lỗi ngắt kết nối do tiến trình ngắt tức thì
    }
    setIsServerRunning(false);
    setLastResponse({
      button_id: 'sys_stop',
      slot: 'SYS',
      name: 'Tắt Webhook Server (Ctrl+C)',
      message: '🔴 Đã TẮT (Kill) tiến trình py src/fiware/webhook_receiver.py thành công! (Tương đương Ctrl+C)',
      success: true,
      latencyMs: 0,
      time: new Date().toLocaleTimeString()
    });
  };

  const handleStartServer = async () => {
    try {
      // Gọi Vite Middleware /start-webhook-server để thực sự spawn tiến trình py src/fiware/webhook_receiver.py trên OS
      const res = await fetch('/start-webhook-server', { method: 'POST' });
      const data = await res.json();
      setIsServerRunning(true);
      setLastResponse({
        button_id: 'sys_start',
        slot: 'SYS',
        name: 'Bật Webhook Server',
        message: data.message || '🚀 Đã khởi chạy lại py src/fiware/webhook_receiver.py thành công!',
        success: true,
        latencyMs: 0,
        time: new Date().toLocaleTimeString()
      });
    } catch (err) {
      setLastResponse({
        button_id: 'sys_start',
        slot: 'SYS',
        name: 'Bật Webhook Server',
        message: `Lỗi khi khởi chạy server: ${err.message}`,
        success: false,
        latencyMs: 0,
        time: new Date().toLocaleTimeString()
      });
    }
  };

  const handleRestartServer = async () => {
    if (isRestarting) return;
    setIsRestarting(true);
    try {
      // Bước 1: Kill tiến trình cũ qua /api/system/stop
      try {
        await fetch('/api/system/stop', { method: 'POST' });
      } catch (e) {
        // bỏ qua nếu server đã ngắt trước đó
      }

      // Đợi 400ms để tiến trình ngắt hẳn
      await new Promise((r) => setTimeout(r, 400));

      // Bước 2: Spawn tiến trình mới qua Vite middleware /start-webhook-server
      const res = await fetch('/start-webhook-server', { method: 'POST' });
      const data = await res.json();
      setIsServerRunning(true);
      setLastResponse({
        button_id: 'sys_restart',
        slot: 'SYS',
        name: 'Restart Webhook Server',
        message: '🔄 Đã TẮT và CHẠY LẠI py src/fiware/webhook_receiver.py thành công! (Ctrl+C rồi py...)',
        success: true,
        latencyMs: 0,
        time: new Date().toLocaleTimeString()
      });
    } catch (err) {
      setLastResponse({
        button_id: 'sys_restart',
        slot: 'SYS',
        name: 'Restart Webhook Server',
        message: `Lỗi restart: ${err.message}`,
        success: false,
        latencyMs: 0,
        time: new Date().toLocaleTimeString()
      });
    } finally {
      setTimeout(() => {
        setIsRestarting(false);
      }, 1500);
    }
  };

  const executeRunScriptApi = async (btn, actionParam = 'normal') => {
    try {
      setLoadingBtn(btn.id);
      setActiveBtn(btn.id);

      const t0 = performance.now();
      const res = await fetch('/api/script/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          button_id: btn.id,
          action: actionParam,
          timestamp: new Date().toISOString()
        })
      });
      const t1 = performance.now();
      const latency = Math.round(t1 - t0);

      const data = await res.json();
      const isOk = res.ok && data.success !== false;

      // Cập nhật trạng thái Dừng / Tiếp Tục của Nút 8
      if (btn.id === 'btn_8' && data.is_stopped !== undefined) {
        setIsMovementPaused(data.is_stopped);
      }
      if (btn.id === 'btn_9' && actionParam === 'reset_all') {
        setIsMovementPaused(false);
      }

      const respObj = {
        button_id: btn.id,
        slot: btn.slot,
        name: data.name || (btn.id === 'btn_8' ? (isMovementPaused ? 'Dừng Di Chuyển Robot' : 'Tiếp Tục Di Chuyển Robot') : btn.title),
        message: data.message || 'Thực thi thành công!',
        success: isOk,
        latencyMs: latency,
        time: new Date().toLocaleTimeString()
      };

      setLastResponse(respObj);

      if (isOk) {
        // Đánh dấu nút vừa kích hoạt thành công trong 3.5 giây
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

  const handleTriggerScript = (btn) => {
    // Nếu là Nút 9 (Reset Demo System): Đếm số lần click trong 650ms (giống Dashboard.jsx)
    if (btn.id === 'btn_9') {
      resetClickCountRef.current += 1;
      const count = resetClickCountRef.current;

      if (count >= 3) {
        setResetClickBadge('🔥 TRIPLE CLICK: RESET ALL SYSTEM!');
      } else {
        setResetClickBadge(`⚡ CLICK ${count}/3 (CHỜ CLICK TIẾP...)`);
      }

      if (resetClickTimerRef.current) clearTimeout(resetClickTimerRef.current);

      resetClickTimerRef.current = setTimeout(async () => {
        const clicks = resetClickCountRef.current;
        resetClickCountRef.current = 0;
        setResetClickBadge('');

        if (clicks >= 3) {
          // Ấn 3 lần nhanh -> Reset toàn bộ hệ thống
          await executeRunScriptApi(btn, 'reset_all');
        } else {
          // Ấn 1 lần -> Undo 1 dòng log vừa thực hiện gần nhất
          await executeRunScriptApi(btn, 'undo');
        }
      }, 650);
      return;
    }

    executeRunScriptApi(btn, 'normal');
  };

  return (
    <div className="w-screen h-screen overflow-hidden bg-[#07090e] text-white font-mono flex flex-col justify-between p-5 select-none relative">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Bar */}
      <header className="flex items-center justify-between z-10 bg-zinc-950/80 p-4 rounded-2xl border border-zinc-800/80 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          <h1 className="text-base md:text-lg font-bold tracking-wider text-white">
            ⚡ CRUZRTWIN REMOTE SCRIPT CONTROLLER
          </h1>
          <span className="px-2.5 py-1 text-[10px] rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
            12 BUTTON SLOTS READY
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Nút Điều Khiển Màn Hình TV (BroadcastChannel) */}
          <div className="flex items-center bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden mr-2 shadow-lg">
            <button
              onClick={() => {
                const ch = new BroadcastChannel('cruzrtwin_sync');
                ch.postMessage({type: 'SWITCH_VIEW', view: 'dashboard'});
                ch.close();
              }}
              className="px-3 py-1.5 text-xs font-bold hover:bg-zinc-800 text-cyan-400 border-r border-zinc-700 transition-colors"
              title="Quay về màn hình Dashboard"
            >
              🖥️ DASHBOARD
            </button>
            <button
              onClick={() => {
                const ch = new BroadcastChannel('cruzrtwin_sync');
                ch.postMessage({type: 'SLIDE_PREV'});
                ch.close();
              }}
              className="px-2.5 py-1.5 text-xs font-bold hover:bg-zinc-800 text-amber-500/70 border-r border-zinc-700 transition-colors"
              title="Lùi lại 1 Slide"
            >
              ◀
            </button>
            <button
              onClick={() => {
                const ch = new BroadcastChannel('cruzrtwin_sync');
                ch.postMessage({type: 'SWITCH_VIEW', view: 'slide'});
                ch.postMessage({type: 'SLIDE_NEXT'});
                ch.close();
              }}
              className="px-3 py-1.5 text-xs font-bold hover:bg-zinc-800 text-amber-400 transition-colors flex items-center gap-1"
              title="Mở Slide / Chuyển sang Slide tiếp theo"
            >
              📊 SLIDE (NEXT) <span className="text-[10px]">▶</span>
            </button>
          </div>

          {/* Nút 1: BẬT WEBHOOK */}
          <button
            onClick={handleStartServer}
            disabled={isServerRunning}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg ${
              isServerRunning
                ? 'bg-zinc-900/50 border-zinc-800 text-zinc-500 cursor-not-allowed opacity-60'
                : 'bg-emerald-600 hover:bg-emerald-500 border-emerald-400 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)] cursor-pointer'
            }`}
            title="Khởi chạy lệnh py src/fiware/webhook_receiver.py"
          >
            <span>▶️</span>
            <span>BẬT WEBHOOK</span>
          </button>

          {/* Nút 2: TẮT WEBHOOK */}
          <button
            onClick={handleStopServer}
            disabled={!isServerRunning}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg ${
              !isServerRunning
                ? 'bg-zinc-900/50 border-zinc-800 text-zinc-500 cursor-not-allowed opacity-60'
                : 'bg-rose-600 hover:bg-rose-500 border-rose-400 text-white shadow-[0_0_12px_rgba(244,63,94,0.4)] cursor-pointer'
            }`}
            title="Tắt tiến trình Server (tương đương Ctrl+C)"
          >
            <span>⏹️</span>
            <span>TẮT WEBHOOK</span>
          </button>

          {/* Nút 3: RESTART WEBHOOK */}
          <button
            onClick={handleRestartServer}
            disabled={isRestarting}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg ${
              isRestarting
                ? 'bg-amber-500/20 border-amber-400 text-amber-300 animate-pulse cursor-wait'
                : 'bg-zinc-900 hover:bg-zinc-800 border-zinc-700 hover:border-cyan-400 text-cyan-400 hover:text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.25)] cursor-pointer'
            }`}
            title="Tắt và chạy lại py src/fiware/webhook_receiver.py (Ctrl+C rồi py...)"
          >
            <span className={isRestarting ? 'animate-spin' : ''}>🔄</span>
            <span>{isRestarting ? 'RESTARTING...' : 'RESTART'}</span>
          </button>

          <div className="text-xs text-zinc-400 flex items-center gap-2 ml-1">
            <span>STATUS:</span>
            <span className={`px-2 py-0.5 rounded border font-bold text-[11px] ${
              isServerRunning ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border-rose-500/40'
            }`}>
              {isServerRunning ? 'CONNECTED (PORT 5001)' : 'STOPPED (OFFLINE)'}
            </span>
          </div>
        </div>
      </header>

      {/* Main 3x4 Grid (12 Action Buttons) */}
      <main className="flex-1 my-4 grid grid-cols-4 grid-rows-3 gap-4 z-10">
        {BUTTON_CONFIGS.map((btn) => {
          const isLoading = loadingBtn === btn.id;
          const isActive = activeBtn === btn.id;
          const isSuccess = successBtns[btn.id];

          const isBtn8Paused = btn.id === 'btn_8' && isMovementPaused;
          const displayTitle = isBtn8Paused ? '▶️ Tiếp Tục Di Chuyển Robot' : btn.title;
          const displayDesc = isBtn8Paused ? 'Ấn để TIẾP TỤC cho phép Robot lăn bánh' : btn.desc;
          const displayColor = isBtn8Paused
            ? 'from-emerald-600/40 to-emerald-950/70 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse'
            : btn.color;

          return (
            <button
              key={btn.id}
              onClick={() => handleTriggerScript(btn)}
              disabled={isLoading}
              className={`relative group rounded-2xl p-4 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between overflow-hidden shadow-xl ${
                isSuccess
                  ? 'from-emerald-600/30 to-emerald-950/60 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse'
                  : displayColor
              } ${isActive ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
            >
              {/* Card Header: Slot Tag & Status indicator */}
              <div className="flex items-center justify-between w-full">
                <span className={`px-2.5 py-1 text-[10px] font-bold rounded-md border ${
                  isSuccess || isBtn8Paused ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200' : 'bg-black/60 border-white/10 text-zinc-300'
                }`}>
                  SLOT {btn.slot}
                </span>

                {isSuccess ? (
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500 text-black animate-bounce">
                    SENT SUCCESS ✅
                  </span>
                ) : isBtn8Paused ? (
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/30 border border-amber-400 text-amber-300 animate-pulse">
                    MOVEMENT PAUSED 🛑
                  </span>
                ) : (
                  <span className={`w-2.5 h-2.5 rounded-full ${isLoading ? 'bg-amber-400 animate-ping' : isActive ? 'bg-cyan-400 animate-pulse' : 'bg-zinc-600'}`} />
                )}
              </div>

              {/* Card Body: Title & Subtitle */}
              <div className="text-left my-2">
                <div className="text-base md:text-lg font-bold tracking-wide text-white group-hover:text-cyan-300 transition-colors">
                  {displayTitle}
                </div>
                <div className="text-[11px] text-zinc-400 mt-1 line-clamp-1">
                  {btn.id === 'btn_9' && resetClickBadge ? (
                    <span className="text-amber-300 font-bold animate-pulse">{resetClickBadge}</span>
                  ) : (
                    displayDesc
                  )}
                </div>
              </div>

              {/* Card Footer: Action State */}
              <div className="flex items-center justify-between w-full pt-2 border-t border-white/10 text-[10px]">
                <span className="text-zinc-500 font-mono">ID: {btn.id}</span>
                <span className={`text-xs font-bold ${isSuccess ? 'text-emerald-300' : 'text-zinc-300'} group-hover:translate-x-1 transition-transform`}>
                  {btn.id === 'btn_9' && resetClickBadge ? (
                    <span className="text-amber-300 animate-bounce">{resetClickBadge.includes('TRIPLE') ? '🔥 RESET ALL...' : '⚡ CLICKING...'}</span>
                  ) : isLoading ? (
                    '⏳ EXECUTING...'
                  ) : isSuccess ? (
                    '✅ EXECUTED 200 OK'
                  ) : (
                    'RUN SCRIPT ➔'
                  )}
                </span>
              </div>
            </button>
          );
        })}
      </main>

      {/* Footer Execution Log Terminal & System Monitor */}
      <footer className="z-10 bg-zinc-950/95 p-4 rounded-2xl border border-zinc-800/90 text-xs font-mono flex flex-col gap-3 shadow-2xl backdrop-blur-md max-h-56">
        {/* Top Status Summary Bar */}
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 text-cyan-400 font-bold tracking-wider">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>TERMINAL KẾT QUẢ GỬI LỆNH REAL-TIME</span>
            </span>
            {lastResponse && (
              <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold border ${
                lastResponse.success ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
              }`}>
                [{lastResponse.time}] SLOT {lastResponse.slot} - {lastResponse.name}
              </span>
            )}
          </div>

          {lastResponse && (
            <div className="text-[11px] text-zinc-400 font-bold flex items-center gap-3 bg-zinc-900 px-3 py-1 rounded-xl border border-zinc-800">
              <span>STATUS: <span className={lastResponse.success ? 'text-emerald-400' : 'text-rose-400'}>{lastResponse.success ? '200 OK SUCCESS' : '500 ERROR'}</span></span>
              <span className="text-zinc-600">|</span>
              <span>LATENCY: <span className="text-cyan-400">{lastResponse.latencyMs} ms</span></span>
            </div>
          )}
        </div>

        {/* Live Detail Message Output Box */}
        <div className="bg-black/90 p-3 rounded-xl border border-zinc-800/80 overflow-y-auto max-h-32 font-mono text-[11px] text-zinc-300 space-y-1.5 custom-scrollbar">
          {lastResponse ? (
            <div className="p-2 rounded bg-zinc-900/80 border border-zinc-800 flex flex-col gap-1">
              <div className="flex items-center justify-between text-cyan-300 font-bold border-b border-zinc-800/60 pb-1">
                <span>{'>'} [SLOT {lastResponse.slot}] {lastResponse.name}</span>
                <span className="text-zinc-500">{lastResponse.time}</span>
              </div>
              <div className="text-emerald-300 font-semibold leading-relaxed pt-0.5 whitespace-pre-wrap">
                {lastResponse.message}
              </div>
            </div>
          ) : (
            <div className="text-zinc-600 italic py-2 text-center">
              💡 Chưa có lệnh nào được thực thi. Hãy nhấp vào 1 trong 12 nút bấm phía trên để kiểm tra kết nối Robot hoặc kích chạy kịch bản.
            </div>
          )}

          {/* Execution History Log List */}
          {commandHistory.length > 0 && (
            <div className="pt-2 border-t border-zinc-800/60 space-y-1">
              <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">📜 Lịch Sử 5 Lệnh Gần Nhất:</div>
              {commandHistory.slice(0, 5).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-[10px] px-2 py-1 rounded bg-zinc-900/60 border border-zinc-800/50 text-zinc-400">
                  <span className="flex items-center gap-2">
                    <span className="text-zinc-600">[{item.timestamp}]</span>
                    <span className="text-cyan-400 font-bold">{item.button_id}</span>
                    <span className="text-zinc-300">({item.name})</span>
                  </span>
                  <span className="text-emerald-400 font-mono truncate max-w-md">{item.details || item.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}
