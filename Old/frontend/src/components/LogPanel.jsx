import { useRef, useEffect } from 'react';

function formatRoomName(str) {
  if (!str) return str;
  for (let i = 1; i <= 12; i += 1) {
    const roomCode = String(i).padStart(3, '0');
    str = str
      .replace(new RegExp(`DNTU_ROOM_A${roomCode}`, 'g'), `L1-A${i}`)
      .replace(new RegExp(`A${roomCode}`, 'g'), `L1-A${i}`);
  }
  return str;
}

function sensorStatusFromLog(log, values) {
  const status = String(log.device_status || log.status || '').toUpperCase();
  if (status.includes('CRITICAL') || status.includes('ERROR') || status.includes('FIRE')) return 'critical';
  if (status.includes('WARNING')) return 'warning';

  const temp = Number(values.temp);
  const smoke = Number(values.smoke);
  const co2 = Number(values.co2);

  if (!Number.isNaN(smoke) && smoke >= 1) return 'critical';
  if ((!Number.isNaN(temp) && temp >= 40) || (!Number.isNaN(co2) && co2 >= 1000)) return 'critical';
  if ((!Number.isNaN(temp) && temp >= 32) || (!Number.isNaN(co2) && co2 >= 631)) return 'warning';

  return 'normal';
}

function getLogDisplay(title, log, showNormal) {
  if (title === 'AI_DETECTION') {
    if (!showNormal && (log.action_code === 'NO_ACTION' || log.predicted_level === 'normal')) return null;
    return {
      message: `[${(log.predicted_level || 'INFO').toUpperCase()}] ${(log.zone_id || '').replace('DNTU_ROOM_', '')} -> Action: ${log.action_code || 'NONE'}`,
      isCritical: log.predicted_level === 'critical',
      isWarning: log.predicted_level === 'warning'
    };
  }

  if (title === 'ALERT_EVENTS') {
    return {
      message: `[${(log.level || 'ALERT').toUpperCase()}] ${(log.zone_id || '').replace('DNTU_ROOM_', '')} -> ${(log.status || 'ACTIVE')}`,
      isCritical: log.level === 'critical',
      isWarning: log.level === 'warning'
    };
  }

  if (title === 'ROBOT_ACTIONS') {
    return {
      message: `[${log.action_type || 'MOVE'}] ${(log.zone_id || '').replace('DNTU_ROOM_', '')} -> ${log.status || 'PENDING'}`,
      isCritical: log.status === 'PENDING' || log.status === 'ERROR',
      isWarning: false
    };
  }

  if (title === 'OPERATOR_ACK') {
    return {
      message: `[${log.operator_decision || log.decision || 'ACK'}] ${(log.zone_id || '').replace('DNTU_ROOM_', '')}`,
      isCritical: false,
      isWarning: log.result === 'ERROR' || log.operator_decision === 'ERROR_REPORTED'
    };
  }

  if (title === 'ORION_STATE') {
    const deviceCount = Array.isArray(log.devices?.value) ? log.devices.value.length : 0;
    return {
      message: `Sync: ${(log.room || 'System').replace('DNTU_ROOM_', '')} - ${deviceCount} devices`,
      isCritical: false,
      isWarning: false
    };
  }

  if (title === 'RAW_SENSORS') {
    const dev = log.device_id || log.id || 'Device';
    const temp = log.temp ?? log.temperature ?? log.sensor_values?.temperature;
    const smoke = log.smoke ?? log.smoke_status ?? log.sensor_values?.smoke_status;
    const co2 = log.co2 ?? log.air_quality_or_co2 ?? log.sensor_values?.air_quality_or_co2;
    const values = { temp, smoke, co2 };
    const parts = [];

    if (temp !== undefined && temp !== null && temp !== '') parts.push(`Temp: ${temp}C`);
    if (smoke !== undefined && smoke !== null && smoke !== '') parts.push(`Smoke: ${smoke}`);
    if (co2 !== undefined && co2 !== null && co2 !== '') parts.push(`CO2: ${co2}ppm`);

    const status = sensorStatusFromLog(log, values);
    return {
      message: `${dev} | ${parts.length ? parts.join(' | ') : 'No sensor value'}`,
      isCritical: status === 'critical',
      isWarning: status === 'warning'
    };
  }

  return {
    message: JSON.stringify(log),
    isCritical: false,
    isWarning: false
  };
}

export default function LogPanel({ title, data, height, showNormal = true, emptyMessage = 'Chưa có dữ liệu.' }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data]);

  return (
    <div className={`flex flex-col ${height} border-b border-zinc-800`}>
      <div className={`flex justify-between items-center px-4 py-2 border-b bg-zinc-900 bg-opacity-40`}>
        <span className="font-bold text-[10px] tracking-widest text-zinc-400">{title}</span>
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
            const display = getLogDisplay(title, log, showNormal);

            if (!display) return null;

            const message = formatRoomName(display.message);
            const textColor = display.isCritical
              ? 'text-red-400 font-bold'
              : display.isWarning
                ? 'text-amber-300 font-bold'
                : 'text-white opacity-80';

            return (
              <div key={`${title}-${i}-${time}-${message}`} className="mb-2 break-words hover:opacity-100 transition-opacity">
                <span className="text-zinc-500">[{time || 'now'}] </span>
                <span className={textColor}>{message}</span>
              </div>
            );
          })
        ) : (
          <div className="text-zinc-600 italic mt-2">{emptyMessage}</div>
        )}
      </div>
    </div>
  );
}
