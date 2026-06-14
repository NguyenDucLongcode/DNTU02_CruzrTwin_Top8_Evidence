const express = require('express');
const { MongoClient } = require('mongodb');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

const mongoUrl = process.env.MONGO_URI || 'mongodb://localhost:27017';
const client = new MongoClient(mongoUrl);
let db;

async function syncLogsToMongo() {
    if (!db) return;
    const logMap = {
        'ai': 'logs/ai_detection.jsonl',
        'alerts': 'logs/alert_events.jsonl',
        'state': 'logs/orion_state.jsonl',
        'robot': 'logs/robot_actions.jsonl',
        'sensors': 'logs/sensor_readings.jsonl'
    };

    for (const [colName, filePath] of Object.entries(logMap)) {
        const fullPath = path.join(__dirname, filePath);
        if (fs.existsSync(fullPath)) {
            try {
                const lines = fs.readFileSync(fullPath, 'utf-8').trim().split('\n');
                const docs = lines.slice(-50).map(line => {
                    try { return JSON.parse(line.trim()); } catch(e) { return null; }
                }).filter(Boolean);
                
                if (docs.length > 0) {
                    await db.collection(colName).deleteMany({}); // MVP: Overwrite for latest logs
                    await db.collection(colName).insertMany(docs);
                }
            } catch(e) {
                console.error(`Sync error for ${colName}:`, e.message);
            }
        }
    }
}

async function startServer() {
    try {
        await client.connect();
        db = client.db('cruzrtwin_logs');
        console.log("✅ Node.js Connected to MongoDB");

        // Background worker to sync Python mock logs into MongoDB (Chỉ chạy 1 lần lúc khởi động để lấy data nền)
        await syncLogsToMongo();
        console.log("✅ Initial Data Synced from logs/");

        // 1. API: Get logs directly from MongoDB (Replaces Python file reading)
        app.get('/api/logs/:type', async (req, res) => {
            try {
                const type = req.params.type;
                const docs = await db.collection(type).find({}, { projection: { _id: 0 } }).sort({_id: -1}).limit(20).toArray();
                res.json(docs.reverse());
            } catch (e) {
                res.status(500).json({ error: e.message });
            }
        });

        // 1b. API: Get latest aggregated sensor data for 3D Dashboard
        app.get('/api/db/sensors', async (req, res) => {
            try {
                const docs = await db.collection('sensors').find({}).sort({_id: -1}).limit(100).toArray();
                const result = {};
                
                const defaultRooms = ['A101', 'L1-T1', 'L1-B1', 'L2-T2', 'L2-T3', 'L3-B5', 'L5-T5'];
                for (let r of defaultRooms) {
                    result[r] = { temp: 24 + Math.random()*4, smoke: 10 + Math.random()*5, co2: 400 };
                }

                for (let doc of docs) {
                    let roomId = doc.zone_id ? doc.zone_id.replace('DNTU_ROOM_', '') : null;
                    if (roomId && !result[roomId] || (doc.scenario_id && doc.scenario_id !== 'SCN_NORMAL')) {
                        // Ưu tiên đè data nếu là sự cố
                        result[roomId] = {
                            temp: doc.temperature || 25,
                            smoke: doc.smoke || 10,
                            co2: doc.co2 || 400
                        };
                    }
                }
                res.json(result);
            } catch (e) {
                res.status(500).json({ error: e.message });
            }
        });

        // 1c. API: Kích hoạt sự cố bằng HTTP POST (Không đụng vào file text)
        app.post('/api/simulate', async (req, res) => {
            try {
                const { room, temp, smoke, co2, level, message, event, action, state_status } = req.body;
                const ts = new Date().toISOString();
                
                // Chèn trực tiếp vào MongoDB (thay đổi trạng thái phòng trên RAM/DB, không ghi file)
                if (temp || smoke || co2) {
                    await db.collection('sensors').insertOne({ timestamp: ts, zone_id: `DNTU_ROOM_${room}`, temperature: temp, smoke, co2, scenario_id: "SCN_SIMULATED" });
                }
                if (level) await db.collection('ai').insertOne({ timestamp: ts, level, message, rationale: "Simulated via API" });
                if (event) await db.collection('alerts').insertOne({ timestamp: ts, event, description: "System triggered via API" });
                if (action) await db.collection('robot').insertOne({ timestamp: ts, action, destination: room, task: "Emergency Response" });
                if (state_status) await db.collection('state').insertOne({ timestamp: ts, entity: `Device_${room}`, state: state_status, context: "Orion Context Broker Sync" });
                
                res.json({ success: true, message: `Đã cập nhật sự kiện` });
            } catch (e) {
                res.status(500).json({ error: e.message });
            }
        });

        // 2. API: Default load
        app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, 'dashboard.html'));
        });

        const PORT = 8000;
        app.listen(PORT, () => {
            console.log(`🚀 NPM Server running at http://localhost:${PORT}`);
        });
    } catch(e) {
        console.error("Failed to start server:", e);
    }
}

startServer();
