import React from 'react'
import { Shield, Radio, Cpu, MapPin, Grid, Crosshair, Terminal, ToggleLeft, ToggleRight } from 'lucide-react'
import { DepartmentRole, ActiveTab } from '../types'

interface NavbarProps {
  activeTab: ActiveTab
  setActiveTab: (tab: ActiveTab) => void
  role: DepartmentRole
  setRole: (role: DepartmentRole) => void
  totalAlerts: number
  crossCameraEnabled: boolean
  onToggleCrossCamera: () => void
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  role,
  setRole,
  totalAlerts,
  crossCameraEnabled,
  onToggleCrossCamera
}) => {
  return (
    <header className="border-b border-slate-800/80 bg-[#080d1a]/95 backdrop-blur sticky top-0 z-50">
      {/* Top Telemetry Strip */}
      <div className="flex items-center justify-between px-4 py-1.5 border-b border-slate-800/50 text-xs font-mono tracking-wider text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            SYS_STAT: OPERATIONAL
          </span>
          <span className="hidden sm:inline text-slate-600">|</span>
          <span className="hidden sm:flex items-center gap-1.5 text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            AI INFERENCE: ACTIVE
          </span>
          <span className="hidden md:inline text-slate-600">|</span>
          <span className="hidden md:flex items-center gap-1.5 text-slate-300">
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            30 NODES FEDERATED
          </span>
        </div>

        {/* Department RBAC Mode Selector */}
        <div className="flex items-center gap-2">
          <span className="text-slate-500 uppercase text-xs">FEDERATED VIEW:</span>
          <div className="inline-flex rounded border border-slate-800 bg-slate-900/80 p-0.5">
            <button
              onClick={() => setRole('POLICE')}
              className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition-all cursor-pointer ${
                role === 'POLICE'
                  ? 'bg-blue-600/30 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              POLICE C2
            </button>
            <button
              onClick={() => setRole('TRAFFIC')}
              className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition-all cursor-pointer ${
                role === 'TRAFFIC'
                  ? 'bg-amber-600/30 text-amber-300 border border-amber-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              TRAFFIC DEPT
            </button>
            <button
              onClick={() => setRole('MUNICIPAL')}
              className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition-all cursor-pointer ${
                role === 'MUNICIPAL'
                  ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              MUNICIPAL
            </button>
          </div>
        </div>
      </div>

      {/* Main Command Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-2.5 gap-3">
        {/* Logo & System Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded border border-cyan-500/50 bg-cyan-950/40 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(0,243,255,0.25)] shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-wider text-slate-100 font-mono">
                SENTINEL TACTICAL C2
              </h1>
              <span className="text-xs px-2 py-0.5 bg-cyan-950/80 border border-cyan-700/60 text-cyan-300 rounded font-mono font-semibold">
                GUJARAT VMS
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono tracking-tight">
              8-CAPABILITY AI CASCADING ENGINE // FEDERATED MIDDLEWARE
            </p>
          </div>
        </div>

        {/* 4 Interactive Command Tabs */}
        <nav className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-md p-1">
          <button
            onClick={() => setActiveTab('MATRIX')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded text-xs font-mono tracking-wider transition-all cursor-pointer ${
              activeTab === 'MATRIX'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,243,255,0.15)] font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Grid className="w-4 h-4" />
            <span>[1] 9-CAM MATRIX</span>
          </button>

          <button
            onClick={() => setActiveTab('GIS_MAP')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded text-xs font-mono tracking-wider transition-all cursor-pointer ${
              activeTab === 'GIS_MAP'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,243,255,0.15)] font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <MapPin className="w-4 h-4" />
            <span>[2] GUJARAT GIS</span>
          </button>

          <button
            onClick={() => setActiveTab('SCANNER')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded text-xs font-mono tracking-wider transition-all cursor-pointer ${
              activeTab === 'SCANNER'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,243,255,0.15)] font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Crosshair className="w-4 h-4" />
            <span>[3] TARGET SCANNER</span>
            {totalAlerts > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-red-600 text-white text-[10px] font-bold animate-pulse">
                {totalAlerts}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('CENTRAL')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded text-xs font-mono tracking-wider transition-all cursor-pointer ${
              activeTab === 'CENTRAL'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,243,255,0.15)] font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>[4] CENTRAL C2</span>
          </button>
        </nav>

        {/* Cross-Cam Correlation Toggle */}
        <button
          onClick={onToggleCrossCamera}
          title={crossCameraEnabled ? 'Disable cross-camera correlation' : 'Enable cross-camera correlation'}
          className={`flex items-center gap-2 px-3 py-1.5 rounded border text-xs font-mono font-bold tracking-wider transition-all cursor-pointer ${
            crossCameraEnabled
              ? 'border-cyan-500/60 bg-cyan-950/70 text-cyan-300 shadow-[0_0_10px_rgba(0,243,255,0.2)]'
              : 'border-slate-800 bg-slate-900 text-slate-500 hover:text-slate-300 hover:border-slate-700'
          }`}
        >
          {crossCameraEnabled ? (
            <ToggleRight className="w-4 h-4 text-cyan-400" />
          ) : (
            <ToggleLeft className="w-4 h-4 text-slate-500" />
          )}
          <span>CROSS-CAM {crossCameraEnabled ? 'ACTIVE' : 'OFF'}</span>
        </button>
      </div>
    </header>
  )
}
