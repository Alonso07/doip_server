import { useState } from 'react'
import { X, Plus } from 'lucide-react'
import type { ServerType } from '../types'
import { serversApi } from '../api/client'
import { DOIP_DEFAULT_CONFIG } from '../config-defaults'
import toast from 'react-hot-toast'

interface Props {
  onClose: () => void
  onCreated: () => void
  existingPorts: number[]
}

type ApiError = { response?: { data?: { detail?: string } } }

export function CreateServerModal({ onClose, onCreated, existingPorts }: Props) {
  const [type, setType] = useState<ServerType>('doip')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [hostPort, setHostPort] = useState('')
  const [webPort, setWebPort] = useState('')
  const [configYaml, setConfigYaml] = useState(DOIP_DEFAULT_CONFIG)
  const [loading, setLoading] = useState(false)

  const handleTypeChange = (t: ServerType) => {
    setType(t)
    setConfigYaml(t === 'doip' ? DOIP_DEFAULT_CONFIG : '')
    if (t === 'sovd') setHostPort('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const wp = parseInt(webPort)
    const hp = type === 'doip' ? parseInt(hostPort) : wp

    if (isNaN(wp) || wp < 1024) { toast.error('Invalid web port'); return }
    if (type === 'doip' && (isNaN(hp) || hp < 1024)) { toast.error('Invalid DoIP port'); return }
    if (type === 'doip' && hp === wp) { toast.error('DoIP port and web port must differ'); return }
    if (existingPorts.includes(wp)) { toast.error(`Port ${wp} already in use`); return }
    if (type === 'doip' && existingPorts.includes(hp)) { toast.error(`Port ${hp} already in use`); return }

    setLoading(true)
    try {
      await serversApi.create({
        name,
        type,
        description,
        host_port: hp,
        web_port: wp,
        config_yaml: configYaml,
      })
      toast.success('Server created')
      onCreated()
      onClose()
    } catch (e) {
      toast.error((e as ApiError)?.response?.data?.detail ?? 'Failed to create server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-900">Create Diagnostic Server</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-xl transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {/* Type selector */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Server Type</label>
              <div className="grid grid-cols-2 gap-3">
                {(['doip', 'sovd'] as const).map(t => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => handleTypeChange(t)}
                    className={`py-3 px-4 rounded-xl border-2 text-left transition-all ${
                      type === t
                        ? t === 'doip'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className={`text-sm font-bold ${type === t ? (t === 'doip' ? 'text-blue-700' : 'text-purple-700') : 'text-gray-500'}`}>
                      {t === 'doip' ? '🔵 DoIP Server' : '🟣 SOVD Server'}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {t === 'doip' ? 'ISO 13400 — TCP/UDP + Web Dashboard' : 'ISO 17978-3 — REST API + Web UI'}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Name *</label>
              <input
                required
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
                placeholder="e.g. Engine ECU Gateway"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
              <input
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
                placeholder="Optional"
              />
            </div>

            {/* Ports */}
            <div className={`grid gap-4 ${type === 'doip' ? 'grid-cols-2' : 'grid-cols-1'}`}>
              {type === 'doip' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">DoIP Port *</label>
                  <input
                    required
                    type="number"
                    min={1024}
                    max={65535}
                    value={hostPort}
                    onChange={e => setHostPort(e.target.value)}
                    className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono"
                    placeholder="13400"
                  />
                  <p className="text-xs text-gray-400 mt-1">TCP/UDP host port for DoIP protocol</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Web UI Port *</label>
                <input
                  required
                  type="number"
                  min={1024}
                  max={65535}
                  value={webPort}
                  onChange={e => setWebPort(e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono"
                  placeholder={type === 'doip' ? '8081' : '8080'}
                />
                <p className="text-xs text-gray-400 mt-1">
                  {type === 'doip' ? 'DoIP web dashboard port' : 'SOVD HTTP REST API & UI port'}
                </p>
              </div>
            </div>

            {/* Config YAML */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Configuration (YAML)
                {type === 'sovd' && (
                  <span className="ml-2 text-xs text-purple-600 font-normal">
                    — leave empty to use built-in default
                  </span>
                )}
              </label>
              <textarea
                value={configYaml}
                onChange={e => setConfigYaml(e.target.value)}
                rows={10}
                className="w-full px-3.5 py-3 border border-gray-300 rounded-xl font-mono text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y bg-gray-950 text-green-300"
                placeholder={
                  type === 'sovd'
                    ? '# Leave empty — container copies built-in SOVD config on first run\n# (entities, resources, faults, modes are auto-populated to /config)'
                    : '# gateway.yaml config'
                }
                spellCheck={false}
              />
            </div>
          </div>

          <div className="flex gap-3 justify-end p-6 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl disabled:opacity-50 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              {loading ? 'Creating…' : 'Create Server'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
