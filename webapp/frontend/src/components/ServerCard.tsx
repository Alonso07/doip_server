import { useState } from 'react'
import {
  Play, Square, RotateCcw, ExternalLink,
  Trash2, Edit3, FileText, Server, Wifi,
} from 'lucide-react'
import type { Server as ServerT } from '../types'
import { serversApi } from '../api/client'
import toast from 'react-hot-toast'

interface Props {
  server: ServerT
  onRefresh: () => void
  onEditConfig: (server: ServerT) => void
  onViewLogs: (server: ServerT) => void
}

const STATUS_RING: Record<string, string> = {
  running: 'ring-2 ring-green-400',
  stopped: 'ring-1 ring-gray-200',
  error: 'ring-2 ring-red-400',
}
const STATUS_BADGE: Record<string, string> = {
  running: 'bg-green-100 text-green-700',
  stopped: 'bg-gray-100 text-gray-500',
  error: 'bg-red-100 text-red-700',
}
const TYPE_BADGE: Record<string, string> = {
  doip: 'bg-blue-100 text-blue-700',
  sovd: 'bg-purple-100 text-purple-700',
}

type ApiError = { response?: { data?: { detail?: string } } }

export function ServerCard({ server, onRefresh, onEditConfig, onViewLogs }: Props) {
  const [loading, setLoading] = useState<string | null>(null)
  const isRunning = server.status === 'running'

  const act = async (label: string, fn: () => Promise<unknown>) => {
    setLoading(label)
    try {
      await fn()
      toast.success(`${label} successful`)
      onRefresh()
    } catch (e) {
      const msg = (e as ApiError)?.response?.data?.detail ?? `${label} failed`
      toast.error(msg)
    } finally {
      setLoading(null)
    }
  }

  const iconBg = server.type === 'doip' ? 'bg-blue-50' : 'bg-purple-50'
  const iconColor = server.type === 'doip' ? 'text-blue-500' : 'text-purple-500'

  return (
    <div
      className={`bg-white rounded-2xl shadow-sm hover:shadow-md transition-all p-5 flex flex-col gap-4 ${STATUS_RING[server.status]}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className={`p-1.5 rounded-xl ${iconBg}`}>
            <Server className={`w-4 h-4 ${iconColor}`} />
          </div>
          <h3 className="font-semibold text-gray-900 truncate text-sm">{server.name}</h3>
        </div>
        <div className="flex gap-1.5 shrink-0">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${TYPE_BADGE[server.type]}`}>
            {server.type.toUpperCase()}
          </span>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_BADGE[server.status]}`}>
            {server.status}
          </span>
        </div>
      </div>

      {server.description && (
        <p className="text-xs text-gray-400 -mt-2 truncate">{server.description}</p>
      )}

      {/* Network info */}
      <div className="bg-gray-50 rounded-xl p-3 space-y-1.5 text-xs">
        {server.ip_address && (
          <div className="flex items-center gap-1.5 text-gray-600">
            <Wifi className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            <span className="font-mono font-semibold">{server.ip_address}</span>
            <span className="text-gray-400">docker IP</span>
          </div>
        )}
        <div className="flex flex-wrap gap-3 text-gray-500">
          {server.type === 'doip' && (
            <span>
              DoIP:{' '}
              <span className="font-mono font-semibold text-gray-700">
                :{server.host_port}
              </span>
            </span>
          )}
          <span>
            Web:{' '}
            <span className="font-mono font-semibold text-gray-700">
              :{server.web_port}
            </span>
          </span>
        </div>
      </div>

      {/* Primary actions */}
      <div className="flex flex-wrap gap-2">
        {isRunning ? (
          <button
            onClick={() => act('Stop', () => serversApi.stop(server.id))}
            disabled={loading !== null}
            className="btn-action bg-red-50 hover:bg-red-100 text-red-700 border-red-200 disabled:opacity-50"
          >
            <Square className="w-3.5 h-3.5" />
            Stop
          </button>
        ) : (
          <button
            onClick={() => act('Start', () => serversApi.start(server.id))}
            disabled={loading !== null}
            className="btn-action bg-green-50 hover:bg-green-100 text-green-700 border-green-200 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            Start
          </button>
        )}

        <button
          onClick={() => act('Reload', () => serversApi.reload(server.id))}
          disabled={loading !== null}
          className="btn-action bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200 disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${loading === 'Reload' ? 'animate-spin' : ''}`} />
          Reload
        </button>

        <button
          onClick={() => window.open(`http://localhost:${server.web_port}`, '_blank')}
          disabled={!isRunning}
          title={isRunning ? `Open web UI at :${server.web_port}` : 'Start server first'}
          className="btn-action bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border-indigo-200 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Web UI
        </button>
      </div>

      {/* Secondary actions */}
      <div className="flex gap-2 border-t border-gray-100 pt-3 -mb-1">
        <button
          onClick={() => onEditConfig(server)}
          className="btn-action bg-amber-50 hover:bg-amber-100 text-amber-700 border-amber-200 flex-1 justify-center"
        >
          <Edit3 className="w-3.5 h-3.5" />
          Edit Config
        </button>

        <button
          onClick={() => onViewLogs(server)}
          disabled={!server.container_id}
          className="btn-action bg-gray-50 hover:bg-gray-100 text-gray-600 border-gray-200 disabled:opacity-40 disabled:cursor-not-allowed flex-1 justify-center"
        >
          <FileText className="w-3.5 h-3.5" />
          Logs
        </button>

        <button
          onClick={() => act('Delete', () => serversApi.delete(server.id))}
          disabled={loading !== null || isRunning}
          title={isRunning ? 'Stop server before deleting' : 'Delete server'}
          className="btn-action bg-gray-50 hover:bg-red-50 text-gray-400 hover:text-red-600 border-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {loading && (
        <p className="text-xs text-center text-gray-400 animate-pulse -mt-2">{loading}…</p>
      )}
    </div>
  )
}
