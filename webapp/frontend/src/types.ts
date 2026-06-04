export type ServerType = 'doip' | 'sovd'
export type ServerStatus = 'running' | 'stopped' | 'error'

export interface Server {
  id: string
  name: string
  type: ServerType
  description: string
  status: ServerStatus
  host_port: number
  web_port: number
  container_id: string | null
  ip_address: string | null
  config_yaml: string
  created_at: string
  updated_at: string
}

export interface CreateServerRequest {
  name: string
  type: ServerType
  description?: string
  host_port: number
  web_port: number
  config_yaml?: string
}

export interface UpdateServerRequest {
  name?: string
  description?: string
  config_yaml?: string
}

export interface NetworkInfo {
  name: string
  subnet?: string
  gateway?: string
  exists: boolean
  error?: string
  containers?: Array<{
    id: string
    name: string
    ip: string
  }>
}
