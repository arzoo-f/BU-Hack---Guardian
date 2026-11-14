import AlertPanel from '../components/AlertPanel.jsx'
import { Empty, Loading, Offline } from '../components/LoadState.jsx'
import Steps from '../components/Steps.jsx'
import { STATE, dateTimeOf, stateTone } from '../lib/labels.js'
import { navigate } from '../lib/router.js'
import { usePolled } from '../lib/usePolled.js'

/** One incident, every step with the reasons. Refreshes while the incident is live. */
export default function IncidentDetail({ id, live }) {
  const liveSteps = live.steps.incidentId === id ? live.steps.list.length : 0
  const liveState = live.incident.id === id ? live.incident.state : null
  const { data, error } = usePolled(`/incidents/${encodeURIComponent(id)}`, 15000,
    `${liveSteps}|${liveState}|${live.connection}`)

  if (!data) {
    if (error?.includes('HTTP 404')) return <Empty>There is no incident {id}.</Empty>
    return error ? <Offline what="incident" error={error} hasData={false} /> : <Loading what="the incident" />
  }
  const replies = data.events.filter((e) => e.kind === 'reply')
  const decisions = data.events.filter((e) => e.kind === 'decision')
  const heard = replies.length ? replies[replies.length - 1].payload.transcript : ''
  return (
    <div className="space-y-4">
      {error && <Offline what="steps" error={error} hasData />}
      <button type="button" className="text-sm font-medium text-sky-700 underline" onClick={() => navigate('incidents')}>
        All incidents
      </button>
      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-2xl font-bold text-slate-900">
          {data.reason === 'found_on_floor' ? 'Found on the floor' : 'Fall'} · {dateTimeOf(data.started_at)}
          {data.simulated && <span className="ml-2 rounded bg-slate-200 px-1.5 align-middle text-sm text-slate-600">TEST</span>}
        </h2>
        <p className="mt-1 text-slate-600">
          Status: <span className="font-semibold">{STATE[data.state] ?? data.state}</span>
          {data.acknowledged_by && ` · acknowledged by ${data.acknowledged_by}`}
        </p>
      </section>
      {stateTone(data.state) === 'alert' && (
        <AlertPanel incidentId={data.id} heard={heard && `“${heard}”`} reason={decisions.length ? decisions[decisions.length - 1].payload.reason : null} />
      )}
      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Step by step</h3>
        <Steps steps={data.events.map((e) => ({ ...e, reason: data.reason, simulated: data.simulated }))} />
      </section>
    </div>
  )
}
