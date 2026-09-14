import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import { CameraNode, CameraStatus, DepartmentRole } from '../types'
import { Navigation } from 'lucide-react'

interface GisTacticalMapProps {
  cameras: CameraNode[]
  onSelectCamera: (camId: string) => void
  role: DepartmentRole
}

// Function to generate high-tech SVG radar pulse markers
const createTacticalIcon = (status: CameraStatus) => {
  let color = '#00f3ff'
  let ringColor = 'rgba(0, 243, 255, 0.4)'

  if (status === 'ALERT') {
    color = '#ef4444'
    ringColor = 'rgba(239, 68, 68, 0.5)'
  } else if (status === 'CONNECTING') {
    color = '#f59e0b'
    ringColor = 'rgba(245, 158, 11, 0.3)'
  } else if (status === 'FAILED') {
    color = '#7f1d1d'
    ringColor = 'rgba(127, 29, 29, 0.3)'
  } else if (status === 'STANDBY') {
    color = '#64748b'
    ringColor = 'rgba(100, 116, 139, 0.2)'
  }

  const html = `
    <div style="position: relative; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid ${color}; background: ${ringColor};" class="${status === 'ALERT' ? 'radar-pulse-ring' : ''}"></div>
      <div style="position: relative; width: 8px; height: 8px; border-radius: 50%; background: ${color}; box-shadow: 0 0 6px ${color};"></div>
    </div>
  `

  return L.divIcon({
    className: 'custom-tactical-pin',
    html: html,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })
}

export const GisTacticalMap: React.FC<GisTacticalMapProps> = ({
  cameras,
  onSelectCamera,
  role
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)

  // Filter cameras with valid coordinates
  const validCameras = cameras.filter((c) => c.latitude !== null && c.longitude !== null)

  useEffect(() => {
    if (!mapContainerRef.current) return

    // Prevent duplicate map initialization
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove()
      mapInstanceRef.current = null
    }

    // Initialize Leaflet Map centered on Gujarat
    const map = L.map(mapContainerRef.current, {
      center: [22.3094, 72.1362],
      zoom: 7,
      zoomControl: true
    })
    mapInstanceRef.current = map

    // Standard OpenStreetMap tiles — 100% free, no API key, no watermarks
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map)

    // Add Markers for each geocoded camera
    validCameras.forEach((cam) => {
      const marker = L.marker([cam.latitude!, cam.longitude!], {
        icon: createTacticalIcon(cam.status)
      }).addTo(map)

      const alertBadge = cam.status === 'ALERT' 
        ? `<div style="background: rgba(153, 27, 27, 0.4); border: 1px solid #ef4444; color: #fca5a5; font-size: 10px; padding: 4px; border-radius: 4px; margin-bottom: 6px; font-weight: bold;">
             [!] ACTIVE WATCHLIST HIT
           </div>` 
        : ''

      const popupContent = document.createElement('div')
      popupContent.style.fontFamily = 'monospace'
      popupContent.style.fontSize = '12px'
      popupContent.style.color = '#e2e8f0'
      popupContent.style.minWidth = '220px'
      popupContent.style.padding = '4px'

      popupContent.innerHTML = `
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 4px; margin-bottom: 6px;">
          <span style="font-weight: bold; color: #00f3ff; text-transform: uppercase;">${cam.camera_id}</span>
          <span style="background: #1e293b; padding: 1px 6px; border-radius: 4px; font-size: 10px; color: #94a3b8;">${cam.district}</span>
        </div>
        <div style="font-weight: 600; color: #f8fafc; margin-bottom: 4px; font-size: 11px;">${cam.location_name}</div>
        <div style="font-size: 10px; color: #94a3b8; margin-bottom: 6px;">
          LAT: ${cam.latitude?.toFixed(4)} | LON: ${cam.longitude?.toFixed(4)}
        </div>
        ${alertBadge}
        <button id="btn-focus-${cam.camera_id}" style="width: 100%; padding: 5px; background: #0891b2; color: #020617; font-weight: bold; font-size: 11px; border: none; border-radius: 4px; cursor: pointer; text-transform: uppercase; margin-top: 4px;">
          TARGET FOCUS FEED
        </button>
      `

      // Attach click handler to focus button inside popup
      const focusBtn = popupContent.querySelector(`#btn-focus-${cam.camera_id}`)
      if (focusBtn) {
        focusBtn.addEventListener('click', () => {
          onSelectCamera(cam.camera_id)
        })
      }

      marker.bindPopup(popupContent)
    })

    // Handle container resize
    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize()
    })
    resizeObserver.observe(mapContainerRef.current)

    return () => {
      resizeObserver.disconnect()
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [cameras])

  return (
    <div className="relative rounded border border-slate-800 bg-[#060a14] overflow-hidden flex flex-col h-[750px] shadow-2xl">
      {/* Top Map HUD Header */}
      <div className="absolute top-3 left-3 z-[1000] bg-[#070d1c]/90 border border-slate-800/90 rounded px-3 py-2 text-xs font-mono backdrop-blur-md flex items-center gap-4 shadow-lg">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="font-bold text-slate-200">GUJARAT TACTICAL GIS MATRIX</span>
          <span className="text-[10px] text-slate-500">|</span>
          <span className="text-cyan-400 font-semibold">{validCameras.length} GEO-CODED NODES</span>
        </div>

        {/* Legend */}
        <div className="hidden sm:flex items-center gap-3 text-[10px] text-slate-400 border-l border-slate-800 pl-3">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span> NORMAL
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span> ALERT / WATCHLIST
          </span>
        </div>
      </div>

      {/* Leaflet Map DOM Element */}
      <div
        ref={mapContainerRef}
        className="w-full h-full leaflet-dark-filter"
        style={{ background: '#050913' }}
      />
    </div>
  )
}
