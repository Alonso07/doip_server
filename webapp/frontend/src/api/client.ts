import axios from 'axios'
import type { Server, CreateServerRequest, UpdateServerRequest, NetworkInfo } from '../types'

// In dev (vite proxy) and production (nginx proxy) /api is routed to the backend
const api = axios.create({ baseURL: '' })

export const serversApi = {
  list: (): Promise<Server[]> =>
    api.get<Server[]>('/api/servers/').then(r => r.data),

  create: (data: CreateServerRequest): Promise<Server> =>
    api.post<Server>('/api/servers/', data).then(r => r.data),

  get: (id: string): Promise<Server> =>
    api.get<Server>(`/api/servers/${id}`).then(r => r.data),

  update: (id: string, data: UpdateServerRequest): Promise<Server> =>
    api.put<Server>(`/api/servers/${id}`, data).then(r => r.data),

  delete: (id: string): Promise<void> =>
    api.delete(`/api/servers/${id}`).then(r => r.data),

  start: (id: string): Promise<Server> =>
    api.post<Server>(`/api/servers/${id}/start`).then(r => r.data),

  stop: (id: string): Promise<Server> =>
    api.post<Server>(`/api/servers/${id}/stop`).then(r => r.data),

  reload: (id: string): Promise<Server> =>
    api.post<Server>(`/api/servers/${id}/reload`).then(r => r.data),

  logs: (id: string, tail = 200): Promise<string> =>
    api
      .get<string>(`/api/servers/${id}/logs?tail=${tail}`, {
        responseType: 'text',
        transformResponse: [(data: string) => data],
      })
      .then(r => r.data),
}

export const networkApi = {
  info: (): Promise<NetworkInfo> =>
    api.get<NetworkInfo>('/api/network/info').then(r => r.data),
}
