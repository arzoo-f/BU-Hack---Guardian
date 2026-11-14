import AlertPanel from '../components/AlertPanel.jsx'
import Skeleton from '../components/Skeleton.jsx'
import StatusCard from '../components/StatusCard.jsx'
import Steps from '../components/Steps.jsx'
import { stateTone } from '../lib/labels.js'
import { navigate } from '../lib/router.js'
import { usePolled } from '../lib/usePolled.js'

/**
 * What matters right now: status, live skeleton, and the open incident as it unfolds. The steps come
 * from the server's record of the incident (reloaded at every live step), so a page opened or
 * reconnected in the middle of an incident still shows the whole story.
 */
export default function Live({ live, zones }) {
  const { incident, activity, status, pose, steps } = live
  const tone = stateTone(incident.state)
  const liveSteps = steps.incidentId && steps.incidentId === incident.id ? steps.list : []
  const open = incident.id && tone !== 'ok'
  const stored = usePolled(open ? `/incidents/${encodeURIComponent(incident.id)}` : null, 15000,
    `${liveSteps.length}|${incident.state}|${live.connection}`).data
  const current = stored && stored.id === incident.id && stored.events.length >= liveSteps.length
    ? stored.events.map((e) => ({ ...e, reason: stored.reason, simulated: stored.simulated }))
    : liveSteps
  const lastReply = [...current].reverse().find((s) => s.kind === 'reply')
  const lastDecision = [...current].reverse().find((s) => s.kind === 'decision')
  const heard = lastReply
    ? lastReply.payload.heard_speech && lastReply.payload.transcript
      ? `“${lastReply.payload.transcript}”`
      : 'no answer'
    : null
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {live.connection === 'disconnected' && (
        <p className="rounded-xl bg-amber-50 px-4 py-2 text-sm text-amber-900 ring-1 ring-amber-200 lg:col-span-2" role="status">
          Guardian is not answering - what you see below may be out of date. Reconnecting by itself...
        </p>
      )}
      <div className="space-y-4">
        <StatusCard incident={incident} activity={activity} status={status} lastHeard={heard && `Heard: ${heard}`}
          connection={live.connection} />
        {tone === 'alert' && incident.id && (
          <AlertPanel incidentId={incident.id} heard={heard} reason={lastDecision?.payload?.reason} />
        )}
        {incident.id && tone !== 'ok' && (
          <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">What is happening</h2>
              <button type="button" className="text-sm font-medium text-sky-700 underline"
                onClick={() => navigate('incident', incident.id)}>Full details</button>
            </div>
            <Steps steps={current} />
          </section>
        )}
      </div>
      <Skeleton pose={pose} zones={zones} tone={tone} />
    </div>
  )
}
