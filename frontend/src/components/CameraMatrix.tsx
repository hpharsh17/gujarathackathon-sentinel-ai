import React, { useState } from 'react'
import { Search, Filter, ShieldAlert, Eye, Video, CheckSquare, Square, Loader, WifiOff } from 'lucide-react'
import { CameraNode, DepartmentRole } from '../types'

interface CameraMatrixProps {
  cameras: CameraNode[]
  onSelectCamera: (camId: string) => void
  onToggleActiveCamera: (camId: string, active: boolean) => void
  role: DepartmentRole
}

const STATUS_CONFIG = {
  ONLINE:     { dot: 'bg-cyan-400 animate-pulse',  label: 'LIVE',       color: 'text-cyan-400',   border: 'border-cyan-500/50' },
  ALERT:      { dot: 'bg-red-500 animate-pulse',   label: 'ALERT',      color: 'text-red-400',    border: 'border-red-500/60' },
  CONNECTING: { dot: 'bg-amber-400 animate-ping',  label: 'CONNECTING', color: 'text-amber-400',  border: 'border-amber-500/40' },
  FAILED:     { dot: 'bg-red-700',                 label: 'FAILED',     color: 'text-red-500',    border: 'border-red-800/50' },
  STANDBY:    { dot: 'bg-slate-600',               label: 'STANDBY',    color: 'text-slate-500',  border: 'border-slate-800/80' },
}

export const CameraMatrix: React.FC<CameraMatrixProps> = ({
  cameras,
  onSelectCamera,
  onToggleActiveCamera,
  role
}) => {
  const [searchTerm, setSearchTerm]         = useState('')
  const [districtFilter, setDistrictFilter] = useState('ALL')
  const [showActiveOnly, setShowActiveOnly] = useState(false)

  const districts = ['ALL', 'Ahmedabad', 'Junagadh', 'Navsari', 'Rajkot', 'Mehsana', 'Patan', 'Gandhinagar', 'Kutch']
  const activeCount    = cameras.filter(c => c.is_active).length
  const streamingCount = cameras.filter(c => c.status === 'ONLINE' || c.status === 'ALERT').length

  const filtered = cameras.filter(cam => {
    const s = searchTerm.toLowerCase()
    const matchSearch = !s ||
      cam.camera_id.includes(s) ||
      cam.location_name.toLowerCase().includes(s) ||
      cam.district.toLowerCase().includes(s)
    const matchDist   = districtFilter === 'ALL' ||
      cam.district.toLowerCase() === districtFilter.toLowerCase()
    const matchActive = !showActiveOnly || cam.is_active
    return matchSearch && matchDist && matchActive
  })

  // Show up to 9 at a time in tactical grid
  const display = filtered.slice(0, 9)

  return (
    <div className="space-y-3.5">
      {/* ── Compact Tactical Control Toolbar ── */}
      <div className="rounded-lg border border-slate-800/90 bg-[#090e1c] p-2.5 flex flex-wrap items-center justify-between gap-3 shadow-lg">
        {/* Left: Compact Search + District Filters */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Sized Search Input (Not Full-Width) */}
          <div className="relative w-64 md:w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="SEARCH CAMERA, ROAD, DISTRICT..."
              className="w-full pl-9 pr-3 py-1.5 text-xs font-mono bg-slate-900/90 border border-slate-700/80 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          <div className="h-5 w-px bg-slate-800 hidden sm:block"></div>

          {/* District Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <Filter className="w-3.5 h-3.5 text-cyan-400 shrink-0 mr-0.5" />
            {districts.map(d => (
              <button
                key={d}
                onClick={() => setDistrictFilter(d)}
                className={`px-2.5 py-1 rounded text-xs font-mono uppercase whitespace-nowrap border transition-all cursor-pointer ${
                  districtFilter === d
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 font-semibold shadow-[0_0_8px_rgba(0,243,255,0.15)]'
                    : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Active-Only Filter + Live Count */}
        <div className="flex items-center gap-2.5 ml-auto">
          <button
            onClick={() => setShowActiveOnly(v => !v)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono font-semibold border transition-all cursor-pointer ${
              showActiveOnly
                ? 'bg-cyan-950 border-cyan-500 text-cyan-300 shadow-[0_0_10px_rgba(0,243,255,0.2)]'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {showActiveOnly ? <CheckSquare className="w-4 h-4 text-cyan-400" /> : <Square className="w-4 h-4" />}
            <span>ACTIVE ONLY ({activeCount})</span>
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded border border-slate-800 bg-slate-900/90 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span className="text-slate-400">STREAMING: <span className="text-cyan-300 font-bold">{streamingCount}</span></span>
          </div>
        </div>
      </div>

      {/* ── Camera Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {display.map(cam => {
          const cfg = STATUS_CONFIG[cam.status] ?? STATUS_CONFIG.STANDBY
          return (
            <div
              key={cam.camera_id}
              className={`rounded-lg border transition-all overflow-hidden flex flex-col shadow-xl ${cfg.border} bg-[#060913]`}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-3.5 py-2 bg-slate-900/95 border-b border-slate-800 text-xs font-mono">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${cfg.dot}`}></span>
                  <span className="font-bold text-slate-100 text-sm tracking-wide shrink-0">
                    {cam.camera_id.toUpperCase()}
                  </span>
                  <span className="text-slate-600 shrink-0">|</span>
                  <span className="text-slate-300 truncate text-xs font-medium" title={cam.location_name}>
                    {cam.location_name}
                  </span>
                </div>

                <button
                  onClick={() => onToggleActiveCamera(cam.camera_id, !cam.is_active)}
                  className={`shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold border transition-all cursor-pointer ${
                    cam.is_active
                      ? 'bg-cyan-950 border-cyan-500/70 text-cyan-300 shadow-[0_0_8px_rgba(0,243,255,0.2)]'
                      : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-cyan-300 hover:border-cyan-700'
                  }`}
                >
                  {cam.is_active
                    ? <><CheckSquare className="w-3.5 h-3.5 text-cyan-400" /> ACTIVE</>
                    : <><Square className="w-3.5 h-3.5" /> ACTIVATE</>
                  }
                </button>
              </div>

              {/* Video Viewport */}
              <div className="relative aspect-video bg-[#02040a] overflow-hidden">
                {cam.is_active ? (
                  <>
                    <img
                      src={`/api/stream/${cam.camera_id}`}
                      alt={`Live ${cam.camera_id}`}
                      className="w-full h-full object-cover"
                      onError={e => {
                        const img = e.target as HTMLImageElement
                        img.src = `/api/frame/${cam.camera_id}?t=${Date.now()}`
                      }}
                    />
                    {/* Status badge */}
                    <div className={`absolute top-2.5 left-2.5 px-2 py-1 rounded text-xs font-mono font-semibold border backdrop-blur-md flex items-center gap-2 shadow-md ${
                      cam.status === 'CONNECTING'
                        ? 'bg-amber-950/85 border-amber-600/70 text-amber-300'
                        : cam.status === 'FAILED'
                        ? 'bg-red-950/85 border-red-700/70 text-red-300'
                        : 'bg-slate-950/85 border-cyan-500/50 text-cyan-300'
                    }`}>
                      {cam.status === 'CONNECTING'
                        ? <><Loader className="w-3.5 h-3.5 animate-spin text-amber-400" /> CONNECTING...</>
                        : cam.status === 'FAILED'
                        ? <><WifiOff className="w-3.5 h-3.5 text-red-400" /> FAILED (RETRYING)</>
                        : <><span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span> LIVE</>
                      }
                    </div>

                    {cam.status === 'ALERT' && (
                      <div className="absolute top-2.5 right-2.5 bg-red-950/90 border border-red-500 px-2.5 py-1 rounded text-xs font-mono font-bold text-red-200 flex items-center gap-1.5 shadow-[0_0_10px_rgba(239,68,68,0.3)]">
                        <ShieldAlert className="w-3.5 h-3.5 text-red-400" /> ALERT
                      </div>
                    )}
                  </>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-2.5 p-4 text-center">
                    <Video className="w-10 h-10 text-slate-700" />
                    <span className="text-xs font-mono text-slate-500 tracking-wider">STANDBY — FEED OFFLINE</span>
                    <button
                      onClick={() => onToggleActiveCamera(cam.camera_id, true)}
                      className="mt-1 px-3.5 py-1.5 rounded bg-cyan-950/90 border border-cyan-700 text-cyan-300 hover:bg-cyan-900 text-xs font-mono font-bold flex items-center gap-2 transition-all cursor-pointer shadow-[0_0_8px_rgba(0,243,255,0.15)]"
                    >
                      <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                      ENABLE STREAM
                    </button>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-3.5 py-2 bg-slate-900/90 border-t border-slate-800 text-xs font-mono flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={cam.is_active && cam.status === 'ONLINE' ? 'text-cyan-400 font-semibold' : 'text-slate-500'}>
                    VEH: <span className="text-slate-200">{cam.vehicle_count ?? '--'}</span>
                  </span>
                  <span className="text-slate-700">|</span>
                  <span className={cam.is_active && cam.status === 'ONLINE' ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>
                    PPL: <span className="text-slate-200">{cam.people_count ?? '--'}</span>
                  </span>
                  <span className="text-slate-700">|</span>
                  <span className="text-slate-400">{cam.district}</span>
                </div>
                <button
                  onClick={() => onSelectCamera(cam.camera_id)}
                  className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-bold transition-all cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5" /> INSPECT
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
