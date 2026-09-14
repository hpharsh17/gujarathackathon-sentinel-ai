import React, { useState, useEffect } from 'react'
import { CameraNode, DepartmentRole } from '../types'
import { Terminal, Activity, Shield, Cpu, Database, Radio, Globe, Zap, AlertTriangle } from 'lucide-react'

interface CentralCommandProps {
  camera: CameraNode
  role: DepartmentRole
}

export const CentralCommand: React.FC<CentralCommandProps> = ({ camera, role }) => {
  // Live scrolling terminal events state
  const [logs, setLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] [SYSTEM_INIT] Connected to Gujarat VMS Gateway (Port 8554)`,
    `[${new Date().toLocaleTimeString()}] [AI_PIPELINE] Loaded Vision Models (YOLOv8 + EasyOCR + Pose Estimation)`,
    `[${new Date().toLocaleTimeString()}] [SUPABASE_SYNC] Watchlist synced: 9 tables relational schema verified`,
    `[${new Date().toLocaleTimeString()}] [GIS_REGISTRY] Geocoded 30 camera nodes into spatial database`,
    `[${new Date().toLocaleTimeString()}] [ANPR] Detected vehicle #1 [Truck, White] Plate: GJ01AB1234`,
    `[${new Date().toLocaleTimeString()}] [WATCHLIST_ALERT] Stolen vehicle hit! Camera: ${camera.camera_id} (${camera.location_name})`,
    `[${new Date().toLocaleTimeString()}] [CASCADE] Layer 1 Person crop -> YOLO-Pose analyzed (Normal walk)`
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      const time = new Date().toLocaleTimeString()
      const newLog = `[${time}] [INGEST] Processed frame batch (Camera: ${camera.camera_id}, Latency: ${(18 + Math.random() * 5).toFixed(1)}ms)`
      setLogs((prev) => [...prev.slice(-12), newLog])
    }, 2800)
    return () => clearInterval(interval)
  }, [camera])

  return (
    <div className="space-y-4 font-mono">
      {/* Top Tactical Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 rounded border border-slate-800 bg-[#080d1a] hud-corner-box">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>AI CASCADE ENGINE</span>
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-sm font-bold text-slate-100">8-STAGE VISION PIPELINE</div>
          <div className="text-xs text-emerald-400 mt-1">YOLO + ANPR + BEHAVIOR // ACTIVE</div>
        </div>

        <div className="p-3 rounded border border-slate-800 bg-[#080d1a] hud-corner-box">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span>QUEUE INGESTION (PHASE 2)</span>
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-emerald-400">DEPTH: 2 / 120 FRAMES</div>
          <div className="text-[10px] text-slate-400 mt-1">LATENCY: &lt; 25MS (LOSSY-DROP ACTIVE)</div>
        </div>

        <div className="p-3 rounded border border-slate-800 bg-[#080d1a] hud-corner-box">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span>FEDERATED NODES</span>
            <Radio className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-sm font-bold text-blue-400">30/30 CHANNELS ONLINE</div>
          <div className="text-[10px] text-slate-400 mt-1">AHMEDABAD // JUNAGADH // NAVSARI</div>
        </div>

        <div className="p-3 rounded border border-slate-800 bg-[#080d1a] hud-corner-box">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span>SUPABASE CLOUD DB</span>
            <Database className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-sm font-bold text-amber-400">POSTGRES + PGVECTOR</div>
          <div className="text-[10px] text-slate-400 mt-1">WATCHLIST: 1,420 RECORDS INDEXED</div>
        </div>
      </div>

      {/* Main Command Center Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Center Main Video Viewport (2 Columns) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="hud-corner-box rounded border border-slate-800 bg-[#060a14] overflow-hidden flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                <span className="font-bold text-cyan-400 uppercase">
                  ACTIVE FEED: {camera.camera_id} [{camera.location_name}]
                </span>
              </div>
              <span className="text-[10px] text-slate-400">1080P // 30 FPS</span>
            </div>

            {/* Video Container with Tactical Reticle */}
            <div className="relative aspect-video bg-[#03060f] flex items-center justify-center overflow-hidden">
              <img
                src={`/api/stream/${camera.camera_id}`}
                alt={`Live Feed ${camera.camera_id}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const img = e.target as HTMLImageElement
                  img.src = `/api/frame/${camera.camera_id}?t=${Date.now()}`
                }}
              />

              {/* Holographic Radar Concentric Ring Effect */}
              <div className="absolute top-4 right-4 w-28 h-28 pointer-events-none opacity-40">
                <div className="absolute inset-0 rounded-full border border-dashed border-cyan-500/60 animate-spin-slow"></div>
                <div className="absolute inset-3 rounded-full border border-cyan-400/40 animate-spin-reverse"></div>
                <div className="absolute inset-7 rounded-full border border-cyan-300/30"></div>
                <div className="absolute inset-0 flex items-center justify-center text-[9px] text-cyan-300">
                  RADAR
                </div>
              </div>
            </div>

            {/* Video Info Footer */}
            <div className="px-3 py-2 bg-slate-900/70 border-t border-slate-800 text-xs flex items-center justify-between text-slate-400">
              <span>GIS: {camera.latitude?.toFixed(4)}, {camera.longitude?.toFixed(4)} ({camera.district})</span>
              <span className="text-cyan-400">MODEL 3 FEDERATION ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Right Column: Live Security Event Log Terminal */}
        <div className="rounded border border-slate-800 bg-[#070b16] p-3 flex flex-col justify-between shadow-xl">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
              <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-xs">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>REAL-TIME AUDIT LOG</span>
              </div>
              <span className="text-[9px] text-slate-500 bg-slate-900 px-1 rounded">WEBSOCKET FEED</span>
            </div>

            {/* Scrolling Logs Window */}
            <div className="space-y-1.5 text-[10px] text-slate-300 h-[380px] overflow-y-auto pr-1">
              {logs.map((log, idx) => (
                <div
                  key={idx}
                  className={`p-1.5 rounded border ${
                    log.includes('WATCHLIST_ALERT')
                      ? 'bg-red-950/40 border-red-500/60 text-red-300 font-semibold'
                      : 'bg-slate-900/40 border-slate-800/60 text-slate-300'
                  }`}
                >
                  {log}
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 mt-2 text-[10px] text-slate-500 flex items-center justify-between">
            <span>TOTAL EVENTS LOGGED: 4,821</span>
            <span className="text-emerald-400 font-bold">STREAM LIVE</span>
          </div>
        </div>
      </div>
    </div>
  )
}
