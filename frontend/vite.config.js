import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function startWebhookPlugin() {
  return {
    name: 'start-webhook-plugin',
    configureServer(server) {
      server.middlewares.use('/start-webhook-server', (req, res) => {
        if (req.method === 'POST') {
          try {
            const rootDir = path.resolve(__dirname, '..')
            const pyScript = path.join(rootDir, 'src', 'fiware', 'webhook_receiver.py')

            let pythonCmd = 'py'
            const envPy = path.join(rootDir, 'env', 'Scripts', 'python.exe')
            const venvPy = path.join(rootDir, '.venv', 'Scripts', 'python.exe')

            if (fs.existsSync(envPy)) {
              pythonCmd = envPy
            } else if (fs.existsSync(venvPy)) {
              pythonCmd = venvPy
            }

            console.log(`[Vite Webhook Launcher] Opening new CMD Terminal for: "${pythonCmd}" "${pyScript}"`)

            const launchCmd = `start "CruzrTwin Webhook Receiver" cmd.exe /k ""${pythonCmd}" "${pyScript}""`
            const child = spawn(launchCmd, [], {
              cwd: rootDir,
              detached: true,
              shell: true
            })
            child.unref()

            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ success: true, message: '🖥️ Đã mở cửa sổ Terminal CMD mới cho Webhook Receiver!' }))
          } catch (e) {
            console.error(`[Vite Webhook Launcher Error]:`, e)
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ success: false, error: e.message || String(e) }))
          }
        } else {
          res.statusCode = 405
          res.end('Method Not Allowed')
        }
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), startWebhookPlugin()],
  server: {
    port: 5002,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            if (res && !res.headersSent) {
              res.writeHead(503, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Backend server offline', details: err.message }));
            }
          });
        }
      },
      '/webhook': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            if (res && !res.headersSent) {
              res.writeHead(503, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Backend server offline', details: err.message }));
            }
          });
        }
      }
    }
  }
})
