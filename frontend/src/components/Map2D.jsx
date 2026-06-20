import { useEffect, useRef } from 'react';

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

      const scale = Math.min(W / 120, H / 50); // 120x50 virtual
      const cx = W / 2;
      const cy = H / 2;

      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(scale, scale);

      // Corridor
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(-50, -6, 100, 12);

      const drawRoom = (rx, rz, id, color) => {
        ctx.fillStyle = color;
        ctx.strokeStyle = '#00aaff';
        ctx.lineWidth = 0.5;
        ctx.fillRect(rx - 10, rz - 8, 20, 16);
        ctx.strokeRect(rx - 10, rz - 8, 20, 16);

        ctx.fillStyle = '#fff';
        ctx.font = '3px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(id, rx, rz + 1);
      };

      const floorNum = activeFloorIdx || 1;
      
      const ROOMS = [
        // Bottom Row (7 rooms)
        { id: `L${floorNum}-A1`, rx: -75, rz: 16 },
        { id: `L${floorNum}-A3`, rx: -50, rz: 16 },
        { id: `L${floorNum}-A5`, rx: -25, rz: 16 },
        { id: `L${floorNum}-A7`, rx: 0, rz: 16 },
        { id: `L${floorNum}-A9`, rx: 25, rz: 16 },
        { id: `L${floorNum}-A11`, rx: 50, rz: 16 },
        { id: `L${floorNum}-A12`, rx: 75, rz: 16 },
        // Top Row (5 rooms)
        { id: `L${floorNum}-A2`, rx: -50, rz: -16 },
        { id: `L${floorNum}-A4`, rx: -25, rz: -16 },
        { id: `L${floorNum}-A6`, rx: 0, rz: -16 },
        { id: `L${floorNum}-A8`, rx: 25, rz: -16 },
        { id: `L${floorNum}-A10`, rx: 50, rz: -16 },
      ];

      ROOMS.forEach((room) => {
        const id = room.id;
        const sensor = sensorData[id];
        const ds = String(sensor?.device_status || sensor?.status || '').toUpperCase();
        let color = '#0c0c0e';

        if (ds === 'CRITICAL' || ds === 'ERROR' || ds === 'FIRE') {
          color = '#ff0000';
        } else if (ds === 'WARNING') {
          color = '#ffaa00';
        } else if (sensor?.temp >= 40 || sensor?.smoke >= 1 || sensor?.co2 >= 1000) {
          color = '#ff0000';
        } else if (sensor?.temp >= 32 || sensor?.smoke >= 0.5 || sensor?.co2 >= 631) {
          color = '#ffaa00';
        } else if (sensor) {
          color = '#00aa00';
        }

        if (activeRoomId === id) {
          color = '#0055aa';
        }

        drawRoom(room.rx, room.rz, id, color);
      });

      ctx.restore();
    };

    render();
  }, [activeFloorIdx, activeRoomId, sensorData]);

  return (
    <div className={`w-full bg-transparent ${activeRoomId ? 'hidden' : 'block'}`}>
      <div className="px-4 py-2 text-xs font-bold text-blue-400 font-mono tracking-widest border-b border-zinc-800">
        2D MAP
      </div>
      <canvas ref={canvasRef} className="w-full h-[200px]"></canvas>
    </div>
  );
}