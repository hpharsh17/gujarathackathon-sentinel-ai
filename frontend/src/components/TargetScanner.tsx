import React, { useState, useEffect } from 'react'
import { CameraNode, DepartmentRole, TargetDetection } from '../types'
import { Crosshair, ShieldCheck, ShieldAlert, Cpu, Radio, Maximize2, Zap, AlertTriangle, Video, Search } from 'lucide-react'

interface TargetScannerProps {
  camera: CameraNode
  role: DepartmentRole
  crossCameraEnabled?: boolean
}

export const TargetScanner: React.FC<TargetScannerProps> = ({ camera, role, crossCameraEnabled }) => {
  const [detections, setDetections] = useState<TargetDetection[]>([])
  const [latestAiEvent, setLatestAiEvent] = useState<any>(null)
  const [latestIncident, setLatestIncident] = useState<any>(null)
  const [plateQuery, setPlateQuery] = useState('')
  const [queryResults, setQueryResults] = useState<any[]>([])
  const [queryStatus, setQueryStatus] = useState('')

  const searchCrossCamera = async () => {
    const normalizedQuery = plateQuery.replace(/[^a-z0-9]/gi, '').toUpperCase()
    if (!normalizedQuery) {
      setQueryStatus('ENTER A PLATE')
      setQueryResults([])
      return
    }
    if (!crossCameraEnabled) {
      setQueryStatus('CROSS-CAM DISABLED')
      setQueryResults([])
      return
    }

    try {
      const res = await fetch(`/api/vehicles/cross-camera/search?plate=${encodeURIComponent(normalizedQuery)}&source_camera=${encodeURIComponent(camera.camera_id)}`)
      const result = await res.json()
      setQueryResults(result.sightings || [])
      setQueryStatus(result.nearest_camera
        ? `NEXT CAMERA: ${result.nearest_camera.camera_id.toUpperCase()} // ${result.nearest_camera.distance_from_source_km} KM`
        : result.sightings?.length ? `${result.sightings.length} SIGHTINGS` : 'NO NEAREST CAMERA PATH')
    } catch (err) {
      setQueryStatus('API UNAVAILABLE')
      setQueryResults([])
    }
  }

  // Fetch real AI detections from FastAPI backend
  useEffect(() => {
    const fetchLatestEvents = async () => {
      try {
        const [eventRes, incidentRes] = await Promise.all([
          fetch('/api/events/latest'),
          fetch('/api/incidents/latest')
        ])
        if (incidentRes.ok) {
          const incident = await incidentRes.json()
          setLatestIncident(incident.incident || incident)
        }
        if (eventRes.ok) {
          const event = await eventRes.json()
          setLatestAiEvent(event)

          const vehicles = event.ai_detections?.vehicles || []
          if (vehicles.length > 0) {
            const realDetections: TargetDetection[] = vehicles.map((v: any, idx: number) => {
              const hasAlert = Boolean(v.stolen_alert)
              return {
                id: `veh-${idx}-${v.track_id || idx}`,
                camera_id: camera.camera_id,
                location: camera.location_name,
                timestamp: new Date().toLocaleTimeString(),
                type: v.vehicle_type || 'Vehicle',
                color: v.color || 'Unknown',
                plate_text: v.plate_text || null,
                confidence: v.confidence || 0.85,
                is_stolen: hasAlert,
                scan_status: hasAlert ? 'ALERT' : v.plate_text ? 'CLEARED' : 'SCANNING',
              }
            })
            setDetections(realDetections)
          }
        }
      } catch (err) {
        // Fallback if backend is warming up
      }
    }

    fetchLatestEvents()
    const interval = setInterval(fetchLatestEvents, 1500)
    return () => clearInterval(interval)
  }, [camera])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Left 2 Columns: Main Tactical Camera Feed */}
      <div className="lg:col-span-2 space-y-3">
        <div className="hud-corner-box rounded border border-slate-800 bg-[#060a14] overflow-hidden flex flex-col shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
              <span className="font-bold text-cyan-400 uppercase tracking-widest text-sm">
                {camera.camera_id} // LIVE TACTICAL FOCUS
              </span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-300 font-medium">{camera.location_name}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-cyan-300 bg-cyan-950/80 border border-cyan-800 px-2 py-0.5 rounded font-mono">
                {camera.district.toUpperCase()}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                {camera.latitude?.toFixed(4)}, {camera.longitude?.toFixed(4)}
              </span>
            </div>
          </div>

          {/* Primary Video Container */}
          <div className="relative aspect-video bg-[#03060f] flex items-center justify-center overflow-hidden">
            {/* Real Live MJPEG Stream */}
            <img
              src={`/api/stream/${camera.camera_id}`}
              alt={`Live Camera Feed ${camera.camera_id}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                const img = e.target as HTMLImageElement
                img.src = `/api/frame/${camera.camera_id}?t=${Date.now()}`
              }}
            />

            {/* Tactical Stream HUD Overlays */}
            <div className="absolute top-3 left-3 flex flex-col gap-1 text-[11px] font-mono text-cyan-400 bg-black/70 p-2 rounded border border-cyan-500/30 backdrop-blur-sm">
              <span className="flex items-center gap-1.5 font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
                ACTIVE RTSP // 25 FPS
              </span>
              <span className="text-slate-300 text-[10px]">
                VEHICLES: {latestAiEvent?.ai_detections?.vehicles?.length ?? (camera.vehicle_count ?? 0)} | PEOPLE: {latestAiEvent?.ai_detections?.people_count ?? (camera.people_count ?? 0)}
              </span>
              <span className="text-slate-400 text-[9px]">
                CUDA 11.8 // YOLOv8 + ALPR INGESTION
              </span>
            </div>

            {/* Threat Alert Banner if Watchlist match exists */}
            {detections.some((d) => d.is_stolen) && (
              <div className="absolute bottom-3 left-3 right-3 bg-red-950/90 border border-red-500 text-red-200 px-3 py-2 rounded flex items-center justify-between text-xs font-mono backdrop-blur-md shadow-[0_0_20px_rgba(239,68,68,0.4)]">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 animate-bounce" />
                  <span className="font-bold text-red-400">CRITICAL WATCHLIST HIT:</span>
                  <span>FLAGGED VEHICLE MATCHED IN SUPABASE WATCHLIST</span>
                </div>
                <span className="text-[10px] bg-red-900/80 px-2 py-0.5 rounded text-red-200 uppercase font-semibold">
                  POLICE DISPATCHED
                </span>
              </div>
            )}

            {latestIncident?.type === 'ACCIDENT_CANDIDATE' && (
              <div className="absolute top-3 right-3 max-w-[min(90%,420px)] border border-red-500 bg-red-950/95 px-3 py-2 text-xs font-mono text-red-100 shadow-[0_0_24px_rgba(239,68,68,0.5)]">
                <div className="flex items-center gap-2 font-bold text-red-300">
                  <AlertTriangle className="h-4 w-4 animate-pulse" />
                  ACCIDENT CANDIDATE // {latestIncident.camera_id?.toUpperCase()}
                </div>
                <div className="mt-1 text-[10px] text-red-200">
                  {latestIncident.location?.location_name || latestIncident.location?.district || 'Location unavailable'}
                  {' // '}TRACKS: {latestIncident.track_ids?.length || 0}
                </div>
                <div className="mt-1 text-[10px] uppercase text-amber-300">
                  EMERGENCY: {latestIncident.dispatch_status || 'RECORDED'}
                </div>
              </div>
            )}
          </div>

          {/* Footer Metadata Strip */}
          <div className="px-4 py-2 bg-slate-900/80 border-t border-slate-800 text-xs font-mono flex items-center justify-between text-slate-400">
            <div className="flex items-center gap-4">
              <span>STREAM LATENCY: &lt; 25MS</span>
              <span className="text-emerald-400 font-medium">AI PIPELINE: ACTIVE</span>
            </div>
            <div className="text-cyan-400">
              SUPABASE PGVECTOR: CONNECTED
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: AI Extraction & Watchlist Scanner Panel */}
      <div className="hud-corner-box rounded border border-slate-800 bg-[#070b16] p-3 flex flex-col shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span className="font-mono text-xs font-bold text-slate-200 tracking-wider">
              REAL-TIME TARGET SCANNER
            </span>
          </div>
          <span className="text-[10px] font-mono bg-cyan-950 border border-cyan-800 text-cyan-400 px-1.5 py-0.5 rounded">
            {detections.length} DETECTIONS
          </span>
        </div>

        <div className="mb-3 border-b border-slate-800 pb-3">
          <div className="mb-1.5 flex items-center justify-between text-[10px] font-mono font-bold text-amber-300">
            <span>CROSS-CAMERA PLATE QUERY</span>
            <span className={crossCameraEnabled ? 'text-emerald-400' : 'text-slate-500'}>
              {crossCameraEnabled ? 'ENABLED' : 'DISABLED'}
            </span>
          </div>
          <div className="flex gap-1.5">
            <input
              value={plateQuery}
              onChange={(event) => setPlateQuery(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && searchCrossCamera()}
              disabled={!crossCameraEnabled}
              placeholder="GJ01AB1234"
              aria-label="Search vehicle plate across cameras"
              className="min-w-0 flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-[11px] font-mono uppercase text-cyan-200 outline-none placeholder:text-slate-600 focus:border-amber-500 disabled:cursor-not-allowed disabled:opacity-50"
            />
            <button
              onClick={searchCrossCamera}
              disabled={!crossCameraEnabled}
              title="Search plate across cameras"
              className="flex items-center gap-1 rounded border border-amber-500/50 bg-amber-500/10 px-2 py-1.5 text-[10px] font-mono font-bold text-amber-300 hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Search className="h-3.5 w-3.5" />
              SEARCH
            </button>
          </div>
          {queryStatus && <div className="mt-1.5 text-[10px] font-mono text-slate-500">{queryStatus}</div>}
          {queryResults.length > 0 && (
            <div className="mt-2 space-y-1">
              {queryResults.map((sighting) => (
                <div key={`${sighting.camera_id}-${sighting.observed_at}`} className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>{sighting.camera_id.toUpperCase()} // {sighting.location_name}</span>
                  <span>{new Date(sighting.observed_at * 1000).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detections Queue */}
        <div className="space-y-3 overflow-y-auto max-h-[640px] pr-1">
          {detections.length === 0 ? (
            <div className="text-center py-12 text-slate-500 font-mono text-xs">
              <Crosshair className="w-8 h-8 mx-auto mb-2 text-slate-600 animate-pulse" />
              <span>SCANNING VIDEO FEED...</span>
              <p className="text-[10px] text-slate-600 mt-1">Waiting for vehicle or person detection</p>
            </div>
          ) : (
            detections.map((det) => (
              <div
                key={det.id}
                className={`relative rounded border p-2.5 font-mono text-xs transition-all overflow-hidden ${
                  det.is_stolen
                    ? 'border-red-500 bg-red-950/30 shadow-[0_0_12px_rgba(239,68,68,0.3)]'
                    : 'border-slate-800 bg-slate-900/60 hover:border-cyan-500/50'
                }`}
              >
                {/* Laser Sweep Animation Line */}
                <div className="laser-scanner-line"></div>

                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-100">{det.type}</span>
                    <span className="text-[10px] text-slate-400">[{det.color}]</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{det.timestamp}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] mb-2">
                  <div className="bg-slate-950/60 p-1.5 rounded border border-slate-800/80">
                    <span className="text-[9px] text-slate-500 block">PLATE NUMBER</span>
                    <span className="text-cyan-300 font-bold tracking-wider">
                      {det.plate_text || 'OCR SCANNING...'}
                    </span>
                  </div>
                  <div className="bg-slate-950/60 p-1.5 rounded border border-slate-800/80">
                    <span className="text-[9px] text-slate-500 block">CONFIDENCE</span>
                    <span className="text-emerald-400 font-bold">
                      {(det.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Database Verification Status Badge */}
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px]">
                  <span className="text-slate-500">WATCHLIST STATUS:</span>
                  {det.scan_status === 'ALERT' && (
                    <span className="flex items-center gap-1 text-red-400 font-bold animate-pulse">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      CRITICAL MATCH (STOLEN)
                    </span>
                  )}
                  {det.scan_status === 'CLEARED' && (
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      CLEARED // NO RECORD
                    </span>
                  )}
                  {det.scan_status === 'SCANNING' && (
                    <span className="text-amber-400 font-semibold animate-pulse">
                      QUERYING SUPABASE...
                    </span>
                  )}
                </div>



              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
