import { useState } from 'react';

const ROOMS = ['L1-A1', 'L1-A2', 'L1-A3', 'L1-A4', 'L1-A5'];

export default function AdminControl() {
  const [status, setStatus] = useState('Sẵn sàng điều chỉnh dữ liệu thiết bị...');
  const [activeRoom, setActiveRoom] = useState(null);
  const [activeAction, setActiveAction] = useState(null);

  const triggerAction = async (action, roomId) => {
    setActiveRoom(roomId);
    setActiveAction(action);
    setStatus(`[${new Date().toLocaleTimeString()}] Đang can thiệp vào cấu hình thiết bị phòng ${roomId}...`);

    let endpoint = '/api/admin/simulate/reset';
    if (action === 'fire') endpoint = '/api/admin/simulate/fire';
    if (action === 'presence') endpoint = '/api/admin/simulate/presence';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: roomId, severity: 'large' }),
      });
      
      const result = await response.json();
      if (result.success) {
        setStatus(`[${new Date().toLocaleTimeString()}] ${result.message}\n⏳ Đang restart thiết bị giả lập (3-5 giây)...`);
      } else {
        setStatus(`Lỗi: ${result.message}`);
      }
    } catch (error) {
      setStatus(`Lỗi kết nối Server: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#121212] text-white p-5 font-sans">
      <div className="max-w-6xl mx-auto bg-[#1e1e1e] p-8 rounded-xl shadow-2xl">
        <h1 className="text-center text-[#ff5252] text-3xl font-bold mb-2">BẢNG ĐIỀU KHIỂN DÀNH CHO GIẢNG VIÊN</h1>
        <p className="text-center text-gray-400 mb-8 text-sm">Quản lý trạng thái các phòng học theo thời gian thực (Gửi lệnh qua MQTT giả lập)</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
          {ROOMS.map(room => {
            const isTarget = activeRoom === room;
            let borderColor = '#444';
            if (isTarget) {
              if (activeAction === 'reset') borderColor = '#555';
              if (activeAction === 'presence') borderColor = '#4CAF50';
              if (activeAction === 'fire') borderColor = '#ff5252';
            }

            return (
              <div 
                key={room} 
                className="bg-[#2a2a2a] rounded-lg p-5 flex flex-col gap-3 transition-colors"
                style={{ borderTop: `4px solid ${borderColor}` }}
              >
                <h3 className="m-0 text-[#ddd] text-xl text-center border-b border-[#444] pb-2 mb-2">Phòng {room}</h3>
                <button 
                  onClick={() => triggerAction('reset', room)} 
                  className="bg-[#555] hover:bg-[#666] text-white font-bold py-3 rounded transition-all cursor-pointer w-full active:scale-95"
                >
                  PHÒNG TRỐNG
                </button>
                <button 
                  onClick={() => triggerAction('presence', room)} 
                  className="bg-[#4CAF50] hover:bg-[#45a049] text-white font-bold py-3 rounded transition-all cursor-pointer w-full active:scale-95"
                >
                  CÓ NGƯỜI
                </button>
                <button 
                  onClick={() => triggerAction('fire', room)} 
                  className="bg-[#ff5252] hover:bg-[#f44336] text-white font-bold py-3 rounded transition-all cursor-pointer w-full active:scale-95"
                >
                  BÁO CHÁY
                </button>
              </div>
            );
          })}
        </div>

        <div className="bg-black p-4 rounded-md font-mono text-green-500 min-h-[50px] text-center mb-8 whitespace-pre-line">
          {status}
        </div>
      </div>
    </div>
  );
}
