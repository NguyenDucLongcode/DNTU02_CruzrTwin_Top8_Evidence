import { useRef, useEffect } from 'react';

const COLORS = {
  blue: 'text-blue-400 border-blue-900 bg-blue-950/10',
  red: 'text-red-500 border-red-900 bg-red-950/10',
  amber: 'text-amber-400 border-amber-900 bg-amber-950/10',
  purple: 'text-purple-400 border-purple-900 bg-purple-950/10',
  emerald: 'text-emerald-400 border-emerald-900 bg-emerald-950/10',
};

export default function LogPanel({ title, data, color, height }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data]);

  const colorClass = COLORS[color] || COLORS.blue;

  return (
    <div className={`flex flex-col ${height} border-b border-zinc-800`}>
      <div className={`flex justify-between items-center px-4 py-2 border-b ${colorClass} bg-opacity-20`}>
        <span className="font-bold text-[10px] tracking-widest">{title}</span>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-[10px] text-zinc-500 font-mono tracking-wider">LIVE</span>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-[10px] leading-relaxed bg-[#0c0c0e] custom-scrollbar"
      >
        {data && data.length > 0 ? (
          data.map((log, i) => {
            const timeStr = log.timestamp || new Date().toISOString();
            const timeMatch = timeStr.match(/T(\d{2}:\d{2}:\d{2})/);
            const time = timeMatch ? timeMatch[1] : timeStr.split('T')[1]?.substring(0, 8);
            
            let message = '';
            if (log.type === 'AI') message = `${log.severity} ${log.message}`;
            else if (log.type === 'ALERT') message = `${log.status || 'ALERT'} - ${log.description || ''}`;
            else if (log.type === 'ROBOT') message = `${log.action || 'MOVE'} to ${log.target || ''}`;
            else if (log.type === 'STATE') message = `Entity ${log.id || 'N/A'} Updated`;
            else if (log.type === 'SENSOR') message = `${log.device_id || 'Unknown'}: Temp=${log.temp || 0}C, Smoke=${log.smoke || 0}`;

            return (
              <div key={i} className="mb-2 break-all opacity-80 hover:opacity-100 transition-opacity">
                <span className="text-zinc-500">[{time}] </span>
                <span className={`${colorClass.split(' ')[0]} font-semibold`}>{message || JSON.stringify(log)}</span>
              </div>
            );
          })
        ) : (
          <div className="text-zinc-600 italic mt-2">Chưa có dữ liệu.</div>
        )}
      </div>
    </div>
  );
}
