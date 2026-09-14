import React, { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { CameraMatrix } from './components/CameraMatrix'
import { GisTacticalMap } from './components/GisTacticalMap'
import { TargetScanner } from './components/TargetScanner'
import { CentralCommand } from './components/CentralCommand'
import { GUJARAT_CAMERAS } from './data/cameras'
import { ActiveTab, DepartmentRole, CameraNode } from './types'
import { Terminal, Layers } from 'lucide-react'

export const App: React.FC = () => {
  const [activeTab, setActiveTab]                 = useState<ActiveTab>('MATRIX')
  const [role, setRole]                           = useState<DepartmentRole>('POLICE')
  const [cameras, setCameras]                     = useState<CameraNode[]>(GUJARAT_CAMERAS)
  const [selectedCamId, setSelectedCamId]         = useState<string>('cam01')
  const [crossCameraEnabled, setCrossCameraEnabled] = useState<boolean>(true)

  const selectedCamera = cameras.find(c => c.camera_id === selectedCamId) ?? cameras[0]
  const totalAlerts    = cameras.filter(c => c.status === 'ALERT' && c.is_active).length

  const fetchCameras = async () => {
    try {
      const res = await fetch('/api/cameras')
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) setCameras(data)
      }
    } catch { /* fallback to static */ }
  }

  useEffect(() => {
    fetchCameras()
    const id = setInterval(fetchCameras, 3000)
    return () => clearInterval(id)
  }, [])

  const handleSelectCamera = (camId: string) => {
    setSelectedCamId(camId)
    setActiveTab('SCANNER')
  }

  const handleToggleActive = async (camId: string, active: boolean) => {
    setCameras(prev => prev.map(c =>
      c.camera_id === camId
        ? { ...c, is_active: active, status: active ? 'CONNECTING' : 'STANDBY' }
        : c
    ))
    try {
      await fetch('/api/active-cameras/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_id: camId, active })
      })
      setTimeout(fetchCameras, 1500)
    } catch { /* ignore */ }
  }

  const streamingCount = cameras.filter(c => c.status === 'ONLINE' || c.status === 'ALERT').length
  const activeCount    = cameras.filter(c => c.is_active).length

  return (
    <div className="min-h-screen bg-[#050811] text-slate-200 flex flex-col selection:bg-cyan-500/30">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        role={role}
        setRole={setRole}
        totalAlerts={totalAlerts}
        crossCameraEnabled={crossCameraEnabled}
        onToggleCrossCamera={() => setCrossCameraEnabled(v => !v)}
      />

      <main className="flex-1 p-3 md:p-4 overflow-y-auto max-w-[1920px] w-full mx-auto">
        {activeTab === 'MATRIX' && (
          <CameraMatrix
            cameras={cameras}
            onSelectCamera={handleSelectCamera}
            onToggleActiveCamera={handleToggleActive}
            role={role}
          />
        )}
        {activeTab === 'GIS_MAP' && (
          <GisTacticalMap cameras={cameras} onSelectCamera={handleSelectCamera} role={role} />
        )}
        {activeTab === 'SCANNER' && (
          <TargetScanner
            camera={selectedCamera}
            role={role}
            crossCameraEnabled={crossCameraEnabled}
          />
        )}
        {activeTab === 'CENTRAL' && (
          <CentralCommand camera={selectedCamera} role={role} />
        )}
      </main>

      <footer className="border-t border-slate-800/80 bg-[#080d1a] px-4 py-2.5 flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 z-40 gap-2">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-2 text-cyan-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            SENTINEL VISION AI // GUJARAT HACKATHON
          </span>
          <span className="hidden sm:inline text-slate-600">|</span>
          <span className="hidden sm:inline">
            STREAMS: <span className="text-cyan-300 font-bold">{streamingCount} LIVE</span>
            <span className="text-slate-600 mx-2">/</span>
            <span className="text-slate-400">{activeCount} ACTIVE</span>
          </span>
          <span className="hidden md:flex items-center gap-1.5 text-slate-500">
            <Layers className="w-3.5 h-3.5 text-cyan-500" />
            MJPEG // RTSP OVER TCP
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-500">
            CLEARANCE: <span className="text-amber-400 font-semibold">{role}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-cyan-500" />
            API: <span className="text-emerald-400 font-semibold ml-1">CONNECTED</span>
          </span>
        </div>
      </footer>
    </div>
  )
}

export default App
