import { useRef, useEffect, useState, useCallback } from 'react';

function formatRoomName(str) {
  if (!str) return str;
  for (let i = 1; i <= 12; i += 1) {
    const roomCode = 100 + i;
    str = str
      .replace(new RegExp(`DNTU_ROOM_A${roomCode}`, 'g'), `L1-A${i}`)
      .replace(new RegExp(`\\bA${roomCode}\\b`, 'g'), `L1-A${i}`);
  }
  return str;
}

function shortenKey(k) {
  const map = {
    demo_run_id: 'run_id', timestamp: 'time', zone_id: 'zone', room: 'zone',
    device_id: 'device', scenario_id: 'scenario', predicted_level: 'level',
    action_code: 'action', anomaly_score: 'score', sensor_values: '-',
    temperature: 'temp', humidity: 'hum', air_quality_or_co2: 'co2',
    smoke_status: 'smoke', energy_consumption: 'energy', raw_smoke_value: 'rawSmoke',
    device_status: 'status', source: 'source', model: 'model', rationale: 'rationale',
    recommended_action: 'rec_action', source_ai_event_id: 'src_event', expected_label: 'exp_label',
    robot_action_id: 'action_id', action_type: 'action_type', target_device: 'target',
    command: 'cmd', parameters: 'params', operator_id: 'op_id', alert_id: 'alert_id',
    operator_decision: 'decision', result: 'result', note: 'note'
  };
  return map[k] || k;
}

function formatValue(v) {
  if (v === null || v === undefined) return 'null';
  if (typeof v === 'object') {
    if (Array.isArray(v)) {
      if (v.length === 0) return '[]';
      return v.slice(0, 10).map((x) => {
        if (typeof x === 'object') return JSON.stringify(x);
        return String(x);
      }).join(', ');
    }
    const entries = Object.entries(v).slice(0, 6).filter(([, val]) => val !== undefined && val !== null);
    return entries.map(([k, val]) => `${shortenKey(k)}:${formatValue(val)}`).join('; ');
  }
  const s = String(v);
  return s.length > 50 ? s.slice(0, 47) + '...' : s;
}

function getLogDisplay(title, log, showNormal) {
  const parts = [];

  const add = (key, val) => {
    if (val === undefined || val === null || val === '') return;
    parts.push(`${shortenKey(key)}:${formatValue(val)}`);
  };

  const zone = (log.zone_id || log.room || log.device_id || '').replace('DNTU_ROOM_', '');
  if (zone) parts.push(`zone:${zone}`);

  add('scenario', log.scenario_id);
  add('run_id', log.demo_run_id);

  if (title === 'SENSORS') {
    if (!showNormal && (log.device_status === 'NORMAL' || log.device_status === 'normal')) return null;
    add('temp', log.temp ?? log.temperature ?? log.sensor_values?.temperature);
    add('hum', log.humidity ?? log.sensor_values?.humidity);
    add('smoke', log.smoke ?? log.smoke_status ?? log.sensor_values?.smoke_status);
    add('co2', log.co2 ?? log.air_quality_or_co2 ?? log.sensor_values?.air_quality_or_co2);
    add('energy', log.energy_consumption ?? log.energy ?? log.sensor_values?.energy_consumption);
    add('rawSmoke', log.raw_smoke_value ?? log.sensor_values?.raw_smoke_value);
    add('status', log.device_status || log.status);
  }

  if (title === 'ORION_STATE') {
    const room = (log.room || 'System').replace('DNTU_ROOM_', '');
    const devices = Array.isArray(log.devices?.value) ? log.devices.value : [];
    const deviceList = devices.map((d) => d.replace('Device:', '')).join(',');
    return {
      message: `${room} | ${deviceList}`,
      isCritical: false,
      isWarning: false
    };
  }

  if (title === 'AI_DETECTION') {
    if (!showNormal && (log.action_code === 'NO_ACTION' || log.predicted_level === 'normal')) return null;
    add('level', log.predicted_level);
    add('action', log.action_code);
    add('score', log.anomaly_score);
    add('model', log.model);
    add('source', log.source);
    if (log.sensor_values && typeof log.sensor_values === 'object') {
      add('temp', log.sensor_values.temperature);
      add('hum', log.sensor_values.humidity);
      add('co2', log.sensor_values.air_quality_or_co2);
      add('smoke', log.sensor_values.smoke_status);
      add('energy', log.sensor_values.energy_consumption);
      add('rawSmoke', log.sensor_values.raw_smoke_value);
    }
    add('expected', log.expected_label);
    add('rationale', log.rationale);
    add('rec_action', log.recommended_action);
    add('src_event', log.source_ai_event_id);
  }

  if (title === 'ROBOT_ACTIONS') {
    add('action_type', log.action_type);
    add('status', log.status);
    add('target', log.target_device);
    add('cmd', log.command);
    add('alert_id', log.alert_id);
  }

  if (title === 'OPERATOR_ACK') {
    add('op_id', log.operator_id);
    add('alert_id', log.alert_id);
    add('action_id', log.robot_action_id);
    add('decision', log.operator_decision || log.decision);
    add('result', log.result);
    add('note', log.note);
  }

  return {
    message: parts.join(' | '),
    isCritical: (() => {
      const ds = (log.device_status || log.status || '').toUpperCase();
      if (ds === 'CRITICAL' || ds === 'ERROR' || ds === 'FIRE') return true;
      if (log.predicted_level === 'critical') return true;
      const t = Number(log.temp ?? log.temperature ?? log.sensor_values?.temperature ?? 0);
      const s = Number(log.smoke ?? log.smoke_status ?? log.sensor_values?.smoke_status ?? 0);
      const c = Number(log.co2 ?? log.air_quality_or_co2 ?? log.sensor_values?.air_quality_or_co2 ?? 0);
      return t >= 40 || s >= 1 || c >= 1000;
    })(),
    isWarning: (() => {
      const ds = (log.device_status || log.status || '').toUpperCase();
      if (ds === 'WARNING') return true;
      if (log.predicted_level === 'warning') return true;
      const t = Number(log.temp ?? log.temperature ?? log.sensor_values?.temperature ?? 0);
      const c = Number(log.co2 ?? log.air_quality_or_co2 ?? log.sensor_values?.co2 ?? 0);
      return t >= 32 || c >= 631;
    })()
  };
}

export default function LogPanel({ title, data, height, showNormal = true, emptyMessage = 'No data available.', onResize, isCollapsed, onToggleCollapse }) {
  const scrollRef = useRef(null);
  const dragRef = useRef({ startY: 0, startHeight: 0 });
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data, isCollapsed]);

  useEffect(() => {
    if (!isDragging) return;
    const handleMouseMove = (e) => {
      const delta = e.clientY - dragRef.current.startY;
      const newHeight = Math.max(60, dragRef.current.startHeight + delta);
      if (onResize) onResize(newHeight);
    };
    const handleMouseUp = () => setIsDragging(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, onResize]);

  const handleDragStart = useCallback((e) => {
    e.preventDefault();
    dragRef.current = {
      startY: e.clientY,
      startHeight: parseInt(height) || 150
    };
    setIsDragging(true);
  }, [height]);

  if (isCollapsed) {
    return (
      <div className="flex flex-col border-b border-zinc-800 bg-zinc-900/60">
        <div
          className="flex justify-between items-center px-4 py-2 cursor-pointer select-none hover:bg-zinc-800/60 transition-colors"
          onClick={onToggleCollapse}
        >
          <span className="font-bold text-[10px] tracking-widest text-zinc-400">{title}</span>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] text-zinc-500 font-mono tracking-wider">LIVE</span>
            <span className="text-[10px] text-zinc-500">[+]</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col border-b border-zinc-800"
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    >
      <div
        className="flex justify-between items-center px-4 py-2 border-b bg-zinc-900 bg-opacity-40 cursor-pointer select-none hover:bg-zinc-800/60 transition-colors"
        onClick={onToggleCollapse}
      >
        <span className="font-bold text-[10px] tracking-widest text-zinc-400">{title}</span>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-[10px] text-zinc-500 font-mono tracking-wider">LIVE</span>
          <span className="text-[10px] text-zinc-500">[-]</span>
        </div>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-[10px] leading-relaxed bg-[#0c0c0e] custom-scrollbar"
      >
        {data && data.length > 0 ? (
          data.map((log, i) => {
            const display = getLogDisplay(title, log, showNormal);
            if (!display) return null;
            const msg = formatRoomName(display.message);
            const textColor = display.isCritical
              ? 'text-red-400 font-bold'
              : display.isWarning
                ? 'text-amber-300 font-bold'
                : 'text-white opacity-80';
            return (
              <div key={`${title}-${i}`} className="mb-2 break-words hover:opacity-100 transition-opacity">
                <span className={textColor}>{msg}</span>
              </div>
            );
          })
        ) : (
          <div className="text-zinc-600 italic mt-2">{emptyMessage}</div>
        )}
      </div>
      <div
        className="h-2 cursor-row-resize bg-zinc-800 hover:bg-blue-500/40 transition-colors flex-shrink-0"
        onMouseDown={handleDragStart}
      />
    </div>
  );
}
