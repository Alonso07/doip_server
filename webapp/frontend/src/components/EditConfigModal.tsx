import { useState } from 'react'
import { X, Save, RotateCcw, Info } from 'lucide-react'
import type { Server } from '../types'
import { serversApi } from '../api/client'
import toast from 'react-hot-toast'

interface Props {
  server: Server
  onClose: () => void
  onSaved: () => void
}

type ApiError = { response?: { data?: { detail?: string } } }

export function EditConfigModal({ server, onClose, onSaved }: Props) {
  const [yaml, setYaml] = useState(server.config_yaml)
  const [loading, setLoading] = useState<'save' | 'reload' | null>(null)

  const handleSave = async () => {
    setLoading('save')
    try {
      await serversApi.update(server.id, { config_yaml: yaml })
      toast.success('Configuration saved')
      onSaved()
    } catch {
      toast.error('Failed to save configuration')
    } finally {
      setLoading(null)
    }
  }

  const handleSaveAndReload = async () => {
    setLoading('reload')
    try {
      await serversApi.update(server.id, { config_yaml: yaml })
      await serversApi.reload(server.id)
      toast.success('Saved and server reloaded')
      onSaved()
      onClose()
    } catch (e) {
      toast.error((e as ApiError)?.response?.data?.detail ?? 'Failed to reload')
    } finally {
      setLoading(null)
    }
  }

  const configFile = server.type === 'doip' ? 'gateway.yaml' : 'sovd_gateway.yaml'

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              Edit Config — {server.name}
            </h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-sm text-gray-400 font-mono">{configFile}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  server.type === 'doip'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-purple-100 text-purple-700'
                }`}
              >
                {server.type.toUpperCase()}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-xl">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {server.type === 'sovd' && (
          <div className="mx-5 mt-4 p-3 bg-purple-50 border border-purple-200 rounded-xl flex gap-2 text-sm text-purple-700">
            <Info className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              On first start, the container copies all built-in SOVD config files to{' '}
              <code className="bg-purple-100 px-1 rounded">/config</code> (entities, resources, faults…).
              Edit <code className="bg-purple-100 px-1 rounded">sovd_gateway.yaml</code> here to override
              gateway settings. Entity/resource files remain at their copied paths.
            </span>
          </div>
        )}

        <div className="flex-1 overflow-hidden p-5 pt-4">
          <textarea
            value={yaml}
            onChange={e => setYaml(e.target.value)}
            className="w-full h-full min-h-[480px] px-4 py-3 font-mono text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none bg-gray-950 text-green-300 leading-relaxed"
            placeholder={
              server.type === 'sovd'
                ? '# Leave empty to use built-in config (auto-copied on first start)\n# Add gateway: section below to override settings'
                : '# gateway.yaml'
            }
            spellCheck={false}
          />
        </div>

        <div className="flex items-center justify-between p-5 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            {server.status === 'running'
              ? '⚡ Use "Save & Reload" to apply changes immediately'
              : '💡 Save config then start the server'}
          </p>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-xl hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={loading !== null}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {loading === 'save' ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={handleSaveAndReload}
              disabled={loading !== null}
              className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl disabled:opacity-50 shadow-sm"
            >
              <RotateCcw className={`w-4 h-4 ${loading === 'reload' ? 'animate-spin' : ''}`} />
              {loading === 'reload' ? 'Reloading…' : 'Save & Reload'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
