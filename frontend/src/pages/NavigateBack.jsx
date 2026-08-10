import { useState, useEffect, useRef } from 'react';
import {
  Volume2, Eye, Circle, Flame, Bot, PartyPopper, StopCircle, RefreshCw,
  Lightbulb, Zap, Plug, Clock, CheckCircle, ChevronLeft,
  ChevronRight, ArrowRight, Monitor, BarChart3, FileText
} from 'lucide-react';

const BUTTON_CONFIGS = [
  { id: 'btn_1', slot: '01', title: 'Phát Thoại Giới Thiệu', desc: 'Robot Cruzr chào & giới thiệu DNTU CruzrTwin', icon: Volume2, color: 'from-blue-600/30 to-blue-900/50 border-blue-400/80 hover:border-blue-300 text-blue-300 shadow-[0_0_15px_rgba(59,130,246,0.3)]' },
  { id: 'btn_2', slot: '02', title: 'Focus AI Detection', desc: 'Bật/Tắt hiển thị Zoom AI Detection trên Dashboard', icon: Eye, color: 'from-cyan-600/30 to-cyan-900/50 border-cyan-400/80 hover:border-cyan-300 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.3)]' },
  { id: 'btn_3', slot: '03', title: 'Kịch Bản Normal', desc: 'Phát dữ liệu Normal & Khôi phục thiết bị IoT', icon: Circle, color: 'from-emerald-600/30 to-emerald-900/50 border-emerald-400/80 hover:border-emerald-300 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]' },
  { id: 'btn_4', slot: '04', title: 'Dự phòng âm thanh', desc: 'Chọn các đoạn âm thanh từ bắt đầu, mô phỏng trạng thái nguy hiểm và kết thúc', icon: Circle, color: 'from-amber-600/30 to-amber-900/50 border-amber-400/80 hover:border-amber-300 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)]' },

  { id: 'btn_5', slot: '05', title: '1. Critical (Chỉ Log)', desc: 'Phát log Báo Động Đỏ Critical & chưa gọi Robot', icon: Circle, color: 'from-rose-600/30 to-rose-900/50 border-rose-400/80 hover:border-rose-300 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.3)]' },
  { id: 'btn_6', slot: '06', title: '2. Kích Hoạt Robot & IoT', desc: 'Gọi Robot Cruzr phát thoại sơ tán & ngắt điện IoT', icon: Bot, color: 'from-purple-600/30 to-purple-900/50 border-purple-400/80 hover:border-purple-300 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.3)]' },
  { id: 'btn_7', slot: '07', title: 'Phát Thoại Outro (Cảm Ơn)', desc: 'Robot Cruzr chào cảm ơn & kết thúc phần thi (speak_outro.py)', icon: PartyPopper, color: 'from-violet-600/30 to-violet-900/50 border-violet-400/80 hover:border-violet-300 text-violet-300 shadow-[0_0_15px_rgba(139,92,246,0.3)]' },
  { id: 'btn_8', slot: '08', title: 'Dừng Di Chuyển Robot', desc: 'Ngắt di chuyển bánh xe Robot ngay lập tức (Vẫn giữ thoại, log & IoT)', icon: StopCircle, color: 'from-red-600/30 to-red-900/50 border-red-400/80 hover:border-red-300 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.3)]' },

  { id: 'btn_9', slot: '09', title: 'Reset & Undo', desc: 'Xóa 1 dòng log gần nhất hoặc Reset toàn bộ', icon: RefreshCw, color: 'from-teal-600/30 to-teal-900/50 border-teal-400/80 hover:border-teal-300 text-teal-300 shadow-[0_0_15px_rgba(20,184,166,0.3)]' },
  { id: 'btn_10', slot: '10', title: 'Khôi Phục Điện Tuya Plugs (ON)', desc: 'Bật toàn bộ ổ cắm thông minh Tuya Smart Plugs (Nút 14)', icon: Lightbulb, color: 'from-emerald-600/30 to-emerald-900/50 border-emerald-400/80 hover:border-emerald-300 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]' },
  { id: 'btn_11', slot: '11', title: 'Ngắt Điện Tuya Plugs (OFF)', desc: 'Tắt toàn bộ ổ cắm thông minh Tuya Smart Plugs (Nút 15)', icon: Zap, color: 'from-amber-600/30 to-amber-900/50 border-amber-400/80 hover:border-amber-300 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)]' },
  { id: 'btn_alarm', slot: '11', title: 'Bật Chuông (ON)', desc: 'Kích hoạt còi Alarm', icon: Lightbulb, color: 'from-rose-600/30 to-rose-900/50 border-rose-400/80 hover:border-rose-300 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.3)]' },
  { id: 'btn_alarm_off', slot: '11', title: 'Tắt Chuông (OFF)', desc: 'Ngắt còi Alarm', icon: StopCircle, color: 'from-zinc-600/30 to-zinc-900/50 border-zinc-400/80 hover:border-zinc-300 text-zinc-300 shadow-[0_0_15px_rgba(161,161,170,0.3)]' },
  { id: 'btn_12', slot: '12', title: 'Test Kết Nối Robot', desc: 'Kiểm tra trạng thái ping & kết nối tới Robot Cruzr (Nút 16)', icon: Plug, color: 'from-pink-600/30 to-pink-900/50 border-pink-400/80 hover:border-pink-300 text-pink-300 shadow-[0_0_15px_rgba(236,72,153,0.3)]' },
];

export default function NavigateBack() {
  const [isServerRunning, setIsServerRunning] = useState(true);
  const [activeBtn, setActiveBtn] = useState(null);
  const [lastResponse, setLastResponse] = useState(null);
  const [loadingBtn, setLoadingBtn] = useState(null);
  const [successBtns, setSuccessBtns] = useState({}); // { btn_id: boolean }
  const [commandHistory, setCommandHistory] = useState([]);
  const [openDropdown, setOpenDropdown] = useState(null);

  const VOICE_FILES = [
    'full_action_multilingual.mp3',
    'intro_speech.mp3',
    'outro_en_google_female.mp3'
  ];

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
      } catch {
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
  const [resetClickBadge, setResetClickBadge] = useState('');

  const handleStopServer = async () => {
    try {
      await fetch('/api/system/stop', { method: 'POST' });
    } catch {
      // ignore stop errors
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
      } catch {
        // ignore if server already stopped
      }

      await new Promise((r) => setTimeout(r, 400));

      const res = await fetch('/start-webhook-server', { method: 'POST' });
      await res.json();
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

      // eslint-disable-next-line react-hooks/purity
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
      // eslint-disable-next-line react-hooks/purity
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

        </div>

        <div className="flex items-center gap-2.5">
          {/* Nút Điều Khiển Màn Hình TV (BroadcastChannel) */}
          <div className="flex items-center bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden mr-2 shadow-lg">
            <button
              onClick={() => {
                const ch = new BroadcastChannel('cruzrtwin_sync');
                ch.postMessage({ type: 'SWITCH_VIEW', view: 'dashboard' });
                ch.close();
              }}
              className="px-3 py-1.5 text-xs font-bold hover:bg-zinc-800 text-cyan-400 border-r border-zinc-700 transition-colors"
              title="Quay về màn hình Dashboard"
            >
              DASHBOARD
            </button>
            <button
              onClick={() => {
                const ch = new BroadcastChannel('cruzrtwin_sync');
                ch.postMessage({ type: 'SLIDE_PREV' });
                ch.close();
              }}
              className="px-2.5 py-1.5 text-xs font-bold hover:bg-zinc-800 text-amber-500/70 border-r border-zinc-700 transition-colors"
              title="Lùi lại 1 Slide"
            >
              <ChevronLeft className="w-3 h-3 mr-1" />
            </button>
            <button
              onClick={() => {
                const ch = new BroadcastChannel('cruzrtwin_sync');
                ch.postMessage({ type: 'SWITCH_VIEW', view: 'slide' });
                ch.postMessage({ type: 'SLIDE_NEXT' });
                ch.close();
              }}
              className="px-3 py-1.5 text-xs font-bold hover:bg-zinc-800 text-amber-400 transition-colors flex items-center gap-1"
              title="Mở Slide / Chuyển sang Slide tiếp theo"
            >
              SLIDE (NEXT)
            </button>
          </div>

          {/* Nút 1: BẬT WEBHOOK */}
          <button
            onClick={handleStartServer}
            disabled={isServerRunning}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg ${isServerRunning
              ? 'bg-zinc-900/50 border-zinc-800 text-zinc-500 cursor-not-allowed opacity-60'
              : 'bg-emerald-600 hover:bg-emerald-500 border-emerald-400 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)] cursor-pointer'
              }`}
            title="Khởi chạy lệnh py src/fiware/webhook_receiver.py"
          >
            <ArrowRight className="w-3 h-3 mr-1" />
            <span>BẬT WEBHOOK</span>
          </button>

          {/* Nút 2: TẮT WEBHOOK */}
          <button
            onClick={handleStopServer}
            disabled={!isServerRunning}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg ${!isServerRunning
              ? 'bg-zinc-900/50 border-zinc-800 text-zinc-500 cursor-not-allowed opacity-60'
              : 'bg-rose-600 hover:bg-rose-500 border-rose-400 text-white shadow-[0_0_12px_rgba(244,63,94,0.4)] cursor-pointer'
              }`}
            title="Tắt tiến trình Server (tương đương Ctrl+C)"
          >
            <StopCircle className="w-3 h-3 mr-1" />
            <span>TẮT WEBHOOK</span>
          </button>

          {/* Nút 3: RESTART WEBHOOK */}
          <button
            onClick={handleRestartServer}
            disabled={isRestarting}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-lg w-[130px] ${isRestarting
              ? 'bg-amber-500/20 border-amber-400 text-amber-300 animate-pulse cursor-wait'
              : 'bg-zinc-900 hover:bg-zinc-800 border-zinc-700 hover:border-cyan-400 text-cyan-400 hover:text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.25)] cursor-pointer'
              }`}
            title="Tắt và chạy lại py src/fiware/webhook_receiver.py (Ctrl+C rồi py...)"
          >
            <RefreshCw className={`w-3 h-3 mr-1 ${isRestarting ? 'animate-spin' : ''}`} />
            <span>{isRestarting ? 'RESTARTING...' : 'RESTART'}</span>
          </button>

          <div className="text-xs text-zinc-400 flex items-center gap-2 ml-1">
            <span>STATUS:</span>
            <span className={`px-2 py-0.5 rounded border font-bold text-[11px] w-[155px] text-center inline-block ${isServerRunning ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border-rose-500/40'
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
          const displayTitle = isBtn8Paused ? <><ArrowRight className="w-3 h-3 mr-1" /> Tiếp Tục Di Chuyển Robot</ > : btn.title;
          const displayDesc = isBtn8Paused ? 'Ấn để TIẾP TỤC cho phép Robot lăn bánh' : btn.desc;
          const displayColor = isBtn8Paused
            ? 'from-emerald-600/40 to-emerald-950/70 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse'
            : btn.color;

          if (btn.id === 'btn_9') {
            return (
              <div key={btn.id} className="relative h-full flex flex-row gap-2">
                {/* Nửa trái: Undo */}
                <button
                  onClick={() => executeRunScriptApi(btn, 'undo')}
                  disabled={isLoading}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccess ? 'from-teal-600/30 to-teal-950/60 border-teal-400 text-teal-300 ring-2 ring-teal-400 shadow-[0_0_20px_rgba(20,184,166,0.5)] animate-pulse' : btn.color
                    } ${isActive ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md border ${isSuccess ? 'bg-teal-500/30 border-teal-400 text-teal-200' : 'bg-black/60 border-white/10 text-zinc-300'
                      }`}>
                      SLOT 09A
                    </span>
                    {isLoading ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-teal-300 transition-colors">
                      Undo Log
                    </div>
                    <div className="text-[9px] text-teal-400/70 mt-0.5 line-clamp-2">
                      Xóa 1 dòng log lỗi
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-teal-300 group-hover:text-teal-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>

                {/* Nửa phải: Reset All */}
                <button
                  onClick={() => executeRunScriptApi(btn, 'reset_all')}
                  disabled={isLoading}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl from-sky-600/30 to-sky-900/50 border-sky-400/80 hover:border-sky-300 text-sky-300 shadow-[0_0_15px_rgba(14,165,233,0.3)] hover:scale-[1.02]`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="px-2 py-0.5 text-[9px] font-bold rounded-md border bg-black/60 border-white/10 text-zinc-300">
                      SLOT 09B
                    </span>
                    {isLoading ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-sky-300 transition-colors">
                      Reset All
                    </div>
                    <div className="text-[9px] text-sky-400/70 mt-0.5 line-clamp-2">
                      Reset toàn bộ Demo
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-sky-300 group-hover:text-sky-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>
              </div>
            );
          }

          if (btn.id === 'btn_1') {
            return (
              <div key={btn.id} className="relative h-full flex flex-row gap-2">
                {/* Nửa trái: Logic hiện tại */}
                <button
                  onClick={() => handleTriggerScript(btn)}
                  disabled={isLoading}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccess ? 'from-emerald-600/30 to-emerald-950/60 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse' : displayColor
                    } ${isActive ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md border ${isSuccess ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200' : 'bg-black/60 border-white/10 text-zinc-300'
                      }`}>
                      SLOT 01A
                    </span>
                    {isLoading ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-cyan-300 transition-colors">
                      {btn.title}
                    </div>
                    <div className="text-[9px] text-zinc-400 mt-0.5 line-clamp-2">
                      {btn.desc}
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-zinc-300 group-hover:text-cyan-300 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>

                {/* Nửa phải: Gọi animation_cute.py */}
                <button
                  onClick={() => executeRunScriptApi(btn, 'animation_cute.py')}
                  disabled={isLoading}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl from-pink-600/30 to-pink-900/50 border-pink-400/80 hover:border-pink-300 text-pink-300 shadow-[0_0_15px_rgba(236,72,153,0.3)] hover:scale-[1.02]`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="px-2 py-0.5 text-[9px] font-bold rounded-md border bg-black/60 border-white/10 text-zinc-300">
                      SLOT 01B
                    </span>
                    <span className="w-2 h-2 rounded-full bg-zinc-600" />
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-pink-200 transition-colors">
                      Animation Cute
                    </div>
                    <div className="text-[9px] text-pink-400/70 mt-0.5 line-clamp-2">
                      Phát cử chỉ đáng yêu
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-pink-300 group-hover:text-pink-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>
              </div>
            );
          }

          if (btn.id === 'btn_11' || btn.id === 'btn_alarm_off') {
            return null; // Đã được gộp
          }

          if (btn.id === 'btn_alarm') {
            const btnAlarmOff = BUTTON_CONFIGS.find(b => b.id === 'btn_alarm_off');
            const isSuccessOn = successBtns['btn_alarm'];
            const isSuccessOff = successBtns['btn_alarm_off'];
            const isActiveOn = activeBtn === 'btn_alarm';
            const isActiveOff = activeBtn === 'btn_alarm_off';
            const isLoadingOn = loadingBtn === 'btn_alarm';
            const isLoadingOff = loadingBtn === 'btn_alarm_off';

            return (
              <div key={btn.id} className="relative h-full flex flex-row gap-2">
                {/* Nửa trái: Bật Còi (ON) */}
                <button
                  onClick={() => handleTriggerScript(btn)}
                  disabled={loadingBtn !== null}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccessOn ? 'from-rose-600/30 to-rose-950/60 border-rose-400 text-rose-300 ring-2 ring-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.5)] animate-pulse' : btn.color
                    } ${isActiveOn ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md border ${isSuccessOn ? 'bg-rose-500/30 border-rose-400 text-rose-200' : 'bg-black/60 border-white/10 text-zinc-300'
                      }`}>
                      SLOT 11A
                    </span>
                    {isLoadingOn ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-rose-300 transition-colors">
                      {btn.title}
                    </div>
                    <div className="text-[9px] text-rose-400/70 mt-0.5 line-clamp-2">
                      {btn.desc}
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-rose-300 group-hover:text-rose-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>

                {/* Nửa phải: Tắt Còi (OFF) */}
                <button
                  onClick={() => handleTriggerScript(btnAlarmOff)}
                  disabled={loadingBtn !== null}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccessOff ? 'from-zinc-500/30 to-zinc-800/60 border-zinc-400 text-zinc-300 ring-2 ring-zinc-400 shadow-[0_0_20px_rgba(161,161,170,0.5)] animate-pulse' : btnAlarmOff.color
                    } ${isActiveOff ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md border ${isSuccessOff ? 'bg-zinc-500/30 border-zinc-400 text-zinc-200' : 'bg-black/60 border-white/10 text-zinc-300'
                      }`}>
                      SLOT 11B
                    </span>
                    {isLoadingOff ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-zinc-300 transition-colors">
                      {btnAlarmOff.title}
                    </div>
                    <div className="text-[9px] text-zinc-400/70 mt-0.5 line-clamp-2">
                      {btnAlarmOff.desc}
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-zinc-300 group-hover:text-zinc-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>
              </div>
            );
          }

          if (btn.id === 'btn_10') {
            const btn11 = BUTTON_CONFIGS.find(b => b.id === 'btn_11');
            const isSuccess10 = successBtns['btn_10'];
            const isSuccess11 = successBtns['btn_11'];
            const isActive10 = activeBtn === 'btn_10';
            const isActive11 = activeBtn === 'btn_11';
            const isLoading10 = loadingBtn === 'btn_10';
            const isLoading11 = loadingBtn === 'btn_11';

            return (
              <div key={btn.id} className="relative h-full flex flex-row gap-2">
                {/* Nửa trái: Logic btn_10 (ON) */}
                <button
                  onClick={() => handleTriggerScript(btn)}
                  disabled={loadingBtn !== null}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccess10 ? 'from-emerald-600/30 to-emerald-950/60 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse' : btn.color
                    } ${isActive10 ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md border ${isSuccess10 ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200' : 'bg-black/60 border-white/10 text-zinc-300'
                      }`}>
                      SLOT 10A
                    </span>
                    {isLoading10 ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-emerald-300 transition-colors">
                      {btn.title}
                    </div>
                    <div className="text-[9px] text-emerald-400/70 mt-0.5 line-clamp-2">
                      {btn.desc}
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-emerald-300 group-hover:text-emerald-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>

                {/* Nửa phải: Logic btn_11 (OFF) */}
                <button
                  onClick={() => handleTriggerScript(btn11)}
                  disabled={loadingBtn !== null}
                  className={`w-1/2 relative group rounded-2xl p-3 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccess11 ? 'from-emerald-600/30 to-emerald-950/60 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse' : btn11.color
                    } ${isActive11 ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md border ${isSuccess11 ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200' : 'bg-black/60 border-white/10 text-zinc-300'
                      }`}>
                      SLOT 10B
                    </span>
                    {isLoading11 ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-600" />
                    )}
                  </div>
                  <div className="text-left my-1">
                    <div className="text-xs md:text-sm font-bold tracking-wide text-white group-hover:text-amber-300 transition-colors">
                      {btn11.title}
                    </div>
                    <div className="text-[9px] text-amber-400/70 mt-0.5 line-clamp-2">
                      {btn11.desc}
                    </div>
                  </div>
                  <div className="flex items-center justify-end w-full pt-1.5 border-t border-white/10 text-[9px]">
                    <span className="flex items-center gap-0.5 font-bold text-amber-300 group-hover:text-amber-200 group-hover:translate-x-1 transition-transform">
                      RUN <ArrowRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>
              </div>
            );
          }

          return (
            <div key={btn.id} className="relative h-full">
              <button
                onClick={() => {
                  if (btn.id === 'btn_4') {
                    setOpenDropdown(prev => prev === btn.id ? null : btn.id);
                  } else {
                    handleTriggerScript(btn);
                  }
                }}
                disabled={isLoading && btn.id !== 'btn_4'}
                className={`w-full h-full relative group rounded-2xl p-4 border bg-gradient-to-br transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl ${isSuccess
                  ? 'from-emerald-600/30 to-emerald-950/60 border-emerald-400 text-emerald-300 ring-2 ring-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)] animate-pulse'
                  : displayColor
                  } ${isActive ? 'scale-[0.98]' : 'hover:scale-[1.02]'}`}
              >
                {/* Card Header: Slot Tag & Status indicator */}
                <div className="flex items-center justify-between w-full">
                  <span className={`px-2.5 py-1 text-[10px] font-bold rounded-md border ${isSuccess || isBtn8Paused ? 'bg-emerald-500/30 border-emerald-400 text-emerald-200' : 'bg-black/60 border-white/10 text-zinc-300'
                    }`}>
                    SLOT {btn.slot}
                  </span>

                  {isSuccess ? (
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500 text-black animate-bounce">
                      <CheckCircle className="w-3 h-3 inline mr-1" /> SENT SUCCESS
                    </span>
                  ) : isBtn8Paused ? (
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/30 border border-amber-400 text-amber-300 animate-pulse">
                      <StopCircle className="w-3 h-3 inline mr-1" /> MOVEMENT PAUSED
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
                      <span className="text-amber-300 animate-bounce flex items-center gap-1">
                        {resetClickBadge.includes('TRIPLE') ? <Flame className="w-3 h-3" /> : <Zap className="w-3 h-3" />}
                        {resetClickBadge.includes('TRIPLE') ? 'RESET ALL...' : 'CLICKING...'}
                      </span>
                    ) : isLoading ? (
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3 animate-spin" /> EXECUTING...</span>
                    ) : isSuccess ? (
                      <span className="flex items-center gap-1"><CheckCircle className="w-3 h-3" /> EXECUTED 200 OK</span>
                    ) : btn.id === 'btn_4' ? (
                      <span className="flex items-center gap-1">CHỌN VOICE <ChevronRight className={`w-3 h-3 transition-transform ${openDropdown === 'btn_4' ? 'rotate-90' : ''}`} /></span>
                    ) : (
                      <span className="flex items-center gap-1">RUN SCRIPT <ArrowRight className="w-3 h-3" /></span>
                    )}
                  </span>
                </div>
              </button>

              {/* Dropdown for btn_4 */}
              {btn.id === 'btn_4' && openDropdown === 'btn_4' && (
                <div className="absolute top-full left-0 mt-2 w-full bg-zinc-900 border border-amber-500/50 rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col">
                  <div className="bg-amber-500/20 px-3 py-1.5 text-[10px] font-bold text-amber-300 border-b border-amber-500/30 flex justify-between items-center">
                    <span>CHỌN VOICE TỪ BACKUP</span>
                    <button onClick={() => setOpenDropdown(null)} className="hover:text-white">✕</button>
                  </div>
                  {VOICE_FILES.map(file => (
                    <button
                      key={file}
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenDropdown(null);
                        executeRunScriptApi(btn, file);
                      }}
                      className="px-3 py-2 text-xs text-left text-zinc-300 hover:bg-zinc-800 hover:text-amber-400 transition-colors border-b border-zinc-800/50 last:border-0 truncate"
                      title={file}
                    >
                      ▶ {file}
                    </button>
                  ))}
                </div>
              )}
            </div>
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
              <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold border ${lastResponse.success ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
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
              <Lightbulb className="w-5 h-5 inline mr-1 text-amber-400" /> Chưa có lệnh nào được thực thi. Hãy nhấp vào 1 trong 12 nút bấm phía trên để kiểm tra kết nối Robot hoặc kích chạy kịch bản.
            </div>
          )}

          {/* Execution History Log List */}
          {commandHistory.length > 0 && (
            <div className="pt-2 border-t border-zinc-800/60 space-y-1">
              <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-1">
                <FileText className="w-3 h-3" /> Lịch Sử 5 Lệnh Gần Nhất:
              </div>
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
