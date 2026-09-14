export type DepartmentRole = 'POLICE' | 'TRAFFIC' | 'MUNICIPAL'
export type ActiveTab = 'MATRIX' | 'GIS_MAP' | 'SCANNER' | 'CENTRAL'
export type CameraStatus = 'ONLINE' | 'STANDBY' | 'ALERT' | 'CONNECTING' | 'FAILED'

export interface CameraNode {
  camera_id: string
  location_name: string
  district: string
  latitude: number | null
  longitude: number | null
  maps_link: string | null
  status: CameraStatus
  fps: number
  is_active?: boolean
  vehicle_count?: number | null
  people_count?: number | null
}

export interface TargetDetection {
  id: string
  camera_id: string
  location: string
  timestamp: string
  type: string
  color: string
  plate_text?: string | null
  confidence: number
  is_stolen?: boolean
  image_url?: string
  scan_status: 'SCANNING' | 'CLEARED' | 'ALERT'
}

export interface SystemTelemetry {
  gpu_name: string
  gpu_temp?: string
  vram_usage: string
  inference_fps?: number
  active_streams?: number
  streaming_cameras?: string[]
  active_cameras?: string[]
  max_streams?: number
  total_nodes?: number
}
