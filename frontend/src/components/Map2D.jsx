import { useEffect, useRef } from 'react';

function getRoomColor(sensor, ds, aRoom, roomId) {
  if (aRoom === roomId) {
    return { color: '#00ff00', isAlert: false };
  }
  if (!sensor) return { color: '#0c0c0e', isAlert: false };
  if (ds === 'CRITICAL' || ds === 'ERROR' || ds === 'FIRE' || sensor?.temp >= 40 || sensor?.smoke >= 1 || sensor?.co2 >= 1000) {
    return { color: '#ff0000', isAlert: true };
  }
  if (ds === 'WARNING' || sensor?.temp >= 32 || sensor?.smoke >= 0.5 || sensor?.co2 >= 631) {
    return { color: '#ffaa00', isAlert: true };
  }
  return { color: '#00ff00', isAlert: false };
}

export default function Map2D({ activeFloorIdx, activeRoomId, sensorData }) {
  const canvasRef = useRef(null);
  const sensorDataRef = useRef(sensorData);
  const activeRoomIdRef = useRef(activeRoomId);
  const activeFloorIdxRef = useRef(activeFloorIdx);

  useEffect(() => { sensorDataRef.current = sensorData; }, [sensorData]);
  useEffect(() => { activeRoomIdRef.current = activeRoomId; }, [activeRoomId]);
  useEffect(() => { activeFloorIdxRef.current = activeFloorIdx; }, [activeFloorIdx]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const W = canvas.parentElement.clientWidth;
    const H = 200;
    canvas.width = W;
    canvas.height = H;

    let reqId;

    const render = () => {
      reqId = requestAnimationFrame(render);
      const sd = sensorDataRef.current;
      const aRoom = activeRoomIdRef.current;
      const floorNum = activeFloorIdxRef.current || 1;

      // Blink factor: oscillates 0→1→0
      const blink = (Math.sin(Date.now() * 0.006) + 1) / 2;

      ctx.clearRect(0, 0, W, H);

      const scale = Math.min(W / 120, H / 50);
      const cx = W / 2;
      const cy = H / 2;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(scale, scale);

      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(-50, -6, 100, 12);

      const drawRoom = (rx, rz, id, baseColor, isAlert) => {
        if (isAlert) {
          // Lerp between baseColor and dark for blinking
          const r = parseInt(baseColor.slice(1, 3), 16);
          const g = parseInt(baseColor.slice(3, 5), 16);
          const b = parseInt(baseColor.slice(5, 7), 16);
          const darkR = Math.round(r * (0.3 + 0.7 * blink));
          const darkG = Math.round(g * (0.3 + 0.7 * blink));
          const darkB = Math.round(b * (0.3 + 0.7 * blink));
          ctx.fillStyle = `rgb(${darkR},${darkG},${darkB})`;
        } else {
          ctx.fillStyle = baseColor;
        }
        ctx.strokeStyle = '#00aaff';
        ctx.lineWidth = 0.5;
        ctx.fillRect(rx - 10, rz - 8, 20, 16);
        ctx.strokeRect(rx - 10, rz - 8, 20, 16);

        // Alert glow border
        if (isAlert) {
          ctx.strokeStyle = baseColor === '#ff0000' ? `rgba(255,0,0,${0.3 + 0.7 * blink})` : `rgba(255,170,0,${0.3 + 0.7 * blink})`;
          ctx.lineWidth = 1;
          ctx.strokeRect(rx - 11, rz - 9, 22, 18);
        }

        ctx.fillStyle = '#fff';
        ctx.font = '3px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(id, rx, rz + 1);
      };

      const ROOMS = [
        { id: `L${floorNum}-A1`, rx: -75, rz: 16 },
        { id: `L${floorNum}-A3`, rx: -50, rz: 16 },
        { id: `L${floorNum}-A5`, rx: -25, rz: 16 },
        { id: `L${floorNum}-A7`, rx: 0, rz: 16 },
        { id: `L${floorNum}-A9`, rx: 25, rz: 16 },
        { id: `L${floorNum}-A11`, rx: 50, rz: 16 },
        { id: `L${floorNum}-A12`, rx: 75, rz: 16 },
        { id: `L${floorNum}-A2`, rx: -50, rz: -16 },
        { id: `L${floorNum}-A4`, rx: -25, rz: -16 },
        { id: `L${floorNum}-A6`, rx: 0, rz: -16 },
        { id: `L${floorNum}-A8`, rx: 25, rz: -16 },
        { id: `L${floorNum}-A10`, rx: 50, rz: -16 },
      ];

      ROOMS.forEach((room) => {
        const id = room.id;
        const sensor = sd[id];
        const ds = String(sensor?.device_status || sensor?.status || '').toUpperCase();
        const { color, isAlert } = getRoomColor(sensor, ds, aRoom, id);
        drawRoom(room.rx, room.rz, id, color, isAlert);
      });

      ctx.restore();
    };

    render();
    return () => cancelAnimationFrame(reqId);
  }, []);

  return (
    <div className={`w-full bg-transparent ${activeRoomId ? 'hidden' : 'block'}`}>
      <canvas ref={canvasRef} className="w-full h-[200px]"></canvas>
    </div>
  );
}