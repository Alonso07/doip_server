import { useQuery } from '@tanstack/react-query'
import { Network, Info } from 'lucide-react'
import { networkApi } from '../api/client'

export function NetworkInfoBanner() {
  const { data } = useQuery({
    queryKey: ['network'],
    queryFn: networkApi.info,
    refetchInterval: 15000,
  })

  if (!data) return null

  return (
    <div
      className={`rounded-2xl p-4 flex items-start gap-3 border ${
        data.exists
          ? 'bg-indigo-50 border-indigo-200'
          : 'bg-amber-50 border-amber-200'
      }`}
    >
      <Network
        className={`w-4 h-4 mt-0.5 shrink-0 ${
          data.exists ? 'text-indigo-500' : 'text-amber-500'
        }`}
      />
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-gray-800">{data.name}</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              data.exists
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-100 text-amber-700'
            }`}
          >
            {data.exists ? 'active' : 'not created yet'}
          </span>
          {data.subnet && (
            <span className="text-xs font-mono text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-lg">
              {data.subnet}
            </span>
          )}
          {data.gateway && (
            <span className="text-xs text-gray-400">
              gw: <span className="font-mono">{data.gateway}</span>
            </span>
          )}
        </div>
        {data.containers && data.containers.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {data.containers.map(c => (
              <span
                key={c.id}
                className="text-xs font-mono text-indigo-600 bg-white border border-indigo-200 px-2 py-0.5 rounded-lg"
              >
                {c.name} • {c.ip}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="flex items-center gap-1 text-xs text-gray-400 shrink-0">
        <Info className="w-3.5 h-3.5" />
        <span>Docker Network</span>
      </div>
    </div>
  )
}
