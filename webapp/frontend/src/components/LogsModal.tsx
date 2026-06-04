import { useState, useEffect, useRef } from 'react'
import { X, RefreshCw, Download } from 'lucide-react'
import type { Server } from '../types'
import { serversApi } from '../api/client'

interface Props {
  server: Server
  onClose: () => void
}

export function LogsModal({ server, onClose }: Props) {
  const [logs, setLogs] = useState('Loading…')
  const [loading, setLoading] = useState(true)
  const [tail, setTail] = useState(200)
  const bottomRef = useRef<HTMLDivElement>(null)

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const data = await serversApi.logs(server.id, tail)
      setLogs(data || 'No output yet')
    } catch {
      setLogs('Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void fetchLogs() }, [tail])

  useEffect(() => {
    if (!loading) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs, loading])

  const handleDownload = () => {
    const blob = new Blob([logs], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${server.name}-logs.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Logs — {server.name}</h2>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              {server.container_id
                ? `Container: ${server.container_id.slice(0, 12)}`
                : 'No container running'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={tail}
              onChange={e => setTail(parseInt(e.target.value))}
              className="text-sm border border-gray-300 rounded-xl px-3 py-1.5 text-gray-600 outline-none focus:ring-2 focus:ring-blue-500"
            >
              {[50, 200, 500, 1000].map(n => (
                <option key={n} value={n}>
                  Last {n} lines
                </option>
              ))}
            </select>
            <button
              onClick={() => void fetchLogs()}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-600 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-600"
              title="Download logs"
            >
              <Download className="w-4 h-4" />
            </button>
            <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-xl">
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto bg-gray-950 p-5 rounded-b-2xl">
          <pre className="text-green-400 text-xs font-mono whitespace-pre-wrap leading-relaxed break-all">
            {loading ? <span className="animate-pulse">Loading…</span> : logs}
          </pre>
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  )
}
