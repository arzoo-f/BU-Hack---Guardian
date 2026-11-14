import { Empty, Loading, Offline } from '../components/LoadState.jsx'
import { STATE, dateTimeOf, stateTone } from '../lib/labels.js'
import { navigate } from '../lib/router.js'
import { usePolled } from '../lib/usePolled.js'

const BADGE = { ok: 'bg-emerald-100 text-emerald-800', checking: 'bg-amber-100 text-amber-800', alert: 'bg-red-100 text-red-800' }

/** Every incident, newest first. Refreshes when the live incident changes and when Guardian is back. */
export default function Incidents({ incident, connection }) {
  const { data: list, error } = usePolled('/incidents?limit=100', 30000, `${incident.id}|${incident.state}|${connection}`)
  return (
    <div className="space-y-4">
      {error && <Offline what="incidents" error={error} hasData={Boolean(list)} />}
      {list ? <IncidentList list={list} /> : !error && <Loading what="incidents" />}
    </div>
  )
}

export function IncidentList({ list }) {
  if (!list.length) return <Empty>No incidents yet. That is good news.</Empty>
  return (
    <ul className="divide-y divide-slate-100 rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      {list.map((item) => (
        <li key={item.id}>
          <button type="button" onClick={() => navigate('incident', item.id)}
            className="flex w-full flex-wrap items-center justify-between gap-2 p-4 text-left hover:bg-slate-50">
            <span>
              <span className="block font-semibold text-slate-900">
                {item.reason === 'found_on_floor' ? 'Found on the floor' : 'Fall'}
                {item.simulated && <span className="ml-2 rounded bg-slate-200 px-1.5 text-xs text-slate-600">TEST</span>}
              </span>
              <span className="text-sm text-slate-500">
                {dateTimeOf(item.started_at)}
                {item.acknowledged_by && ` · acknowledged by ${item.acknowledged_by}`}
              </span>
            </span>
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${BADGE[stateTone(item.state)]}`}>
              {STATE[item.state] ?? item.state}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
