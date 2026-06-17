import { useEffect, useRef } from 'react';

const ROOM_IDS = ['L1-A1', 'L1-A2', 'L1-A3', 'L1-A4', 'L1-A5'];

export default function Map2D({ activeFloorIdx, activeRoomId, sensorData }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const W = canvas.parentElement.clientWidth;
    const H = 200; // Fixed height for 2D map
    canvas.width = W;
    canvas.height = H;

    const render = () => {
      ctx.clearRect(0, 0, W, H);

      const scale = Math.min(W / 120, H / 50); // 120x50 ảo
      const cx = W / 2;
      const cy = H / 2;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(scale, scale);

      // Hành lang
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(-50, -6, 100, 12);

      const drawRoom = (rx, rz, id, color) => {
        ctx.fillStyle = color;
        ctx.strokeStyle = '#00aaff';
        ctx.lineWidth = 0.5;
        ctx.fillRect(rx - 7, rz - 8, 14, 16);
        ctx.strokeRect(rx - 7, rz - 8, 14, 16);

        ctx.fillStyle = '#fff';
        ctx.font = '3px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(id, rx, rz + 1);
      };

      // Vẽ 5 phòng
      for(let i=0; i<5; i++) {
        let rx = -30 + i*15;
        let id = ROOM_IDS[i];
        
        let sensor = sensorData[id];
        let color = '#0c0c0e';
        
        if (sensor) {
          if (sensor.temp >= 40 || sensor.smoke > 50 || sensor.co2 >= 1000) {
            color = '#aa0000'; // Đỏ cháy
          } else if (sensor.presence === 1) {
            color = '#008844'; // Xanh lá
          }
        }
        
        if (activeRoomId === id) {
          color = '#0055aa'; // Đang chọn
        }

        drawRoom(rx, -16, id, color);
      }

      ctx.restore();
    };

    render();
  }, [activeFloorIdx, activeRoomId, sensorData]);

  return (
    <div className={`w-full bg-black/50 border-t border-zinc-800 ${activeRoomId ? 'hidden' : 'block'}`}>
      <div className="px-4 py-2 text-xs font-bold text-blue-400 font-mono tracking-widest border-b border-zinc-800">
        SƠ ĐỒ 2D
      </div>
      <canvas ref={canvasRef} className="w-full h-[200px]"></canvas>
    </div>
  );
}
