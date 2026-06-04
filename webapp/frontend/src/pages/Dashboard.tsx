import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Server, AlertTriangle, RefreshCw } from 'lucide-react'
import { serversApi } from '../api/client'
import { ServerCard } from '../components/ServerCard'
import { CreateServerModal } from '../components/CreateServerModal'
import { EditConfigModal } from '../components/EditConfigModal'
import { LogsModal } from '../components/LogsModal'
import { NetworkInfoBanner } from '../components/NetworkInfoBanner'
import type { Server as ServerT } from '../types'

export function Dashboard() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [editConfig, setEditConfig] = useState<ServerT | null>(null)
  const [viewLogs, setViewLogs] = useState<ServerT | null>(null)

  const {
    data: servers = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['servers'],
    queryFn: serversApi.list,
    refetchInterval: 5000,
  })

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['servers'] })
  const existingPorts = servers.flatMap(s => [s.host_port, s.web_port])
  const runningCount = servers.filter(s => s.status === 'running').length

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2 rounded-xl shadow-sm">
              <Server className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 leading-tight">
                Diagnostic Servers
              </h1>
              <p className="text-xs text-gray-400 leading-tight">DoIP & SOVD Manager</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {servers.length > 0 && (
              <div className="hidden sm:flex items-center gap-1.5 text-sm text-gray-400">
                <span className="w-2 h-2 rounded-full bg-green-400" />
                {runningCount} / {servers.length} running
              </div>
            )}
            <button
              onClick={() => void refetch()}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              New Server
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <NetworkInfoBanner />

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-2xl p-5 text-red-700">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">Cannot connect to backend</p>
              <p className="text-xs text-red-500 mt-0.5">
                Make sure the backend is running on port 8000.{' '}
                <button onClick={() => void refetch()} className="underline hover:text-red-700">
                  Retry
                </button>
              </p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && servers.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-100 p-8 rounded-3xl mb-5">
              <Server className="w-14 h-14 text-indigo-400 mx-auto" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">No diagnostic servers yet</h2>
            <p className="text-gray-400 text-sm mb-6 max-w-sm">
              Create DoIP or SOVD servers. Each runs in its own Docker container on a shared network.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Create First Server
            </button>
          </div>
        )}

        {/* Server grid */}
        {servers.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {servers.map(s => (
              <ServerCard
                key={s.id}
                server={s}
                onRefresh={refresh}
                onEditConfig={setEditConfig}
                onViewLogs={setViewLogs}
              />
            ))}
          </div>
        )}
      </main>

      {showCreate && (
        <CreateServerModal
          onClose={() => setShowCreate(false)}
          onCreated={refresh}
          existingPorts={existingPorts}
        />
      )}
      {editConfig && (
        <EditConfigModal
          server={editConfig}
          onClose={() => setEditConfig(null)}
          onSaved={refresh}
        />
      )}
      {viewLogs && (
        <LogsModal server={viewLogs} onClose={() => setViewLogs(null)} />
      )}
    </div>
  )
}
