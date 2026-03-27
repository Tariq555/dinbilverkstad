const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

let backend = null
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 5001

function waitForServer(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const tick = () => {
      const req = http.get(url, (res) => {
        res.resume()
        resolve()
      })
      req.on('error', () => {
        if (Date.now() - start > timeoutMs) reject(new Error('timeout'))
        else setTimeout(tick, 400)
      })
    }
    tick()
  })
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: { contextIsolation: true }
  })
  win.loadURL(`http://127.0.0.1:${PORT}/`)
}

app.on('ready', async () => {
  const userData = app.getPath('userData')
  const exePath = path.join(process.resourcesPath, 'backend', 'DinBilverkstad.exe')
  const env = { ...process.env, PORT: String(PORT), AUTO_OPEN: '0', DVB_DATA_DIR: path.join(userData) }
  try {
    backend = spawn(exePath, [], { env, detached: false, windowsHide: true })
  } catch (e) {}
  try {
    await waitForServer(`http://127.0.0.1:${PORT}/`, 30000)
  } catch (_) {}
  createWindow()
})

app.on('before-quit', () => {
  if (backend && !backend.killed) {
    try { backend.kill() } catch (_) {}
  }
})
