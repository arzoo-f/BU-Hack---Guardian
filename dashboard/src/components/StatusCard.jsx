import { ACTIVITY, STATE, stateTone } from '../lib/labels.js'

const LOOK = {
  ok: 'bg-emerald-50 text-emerald-900 ring-emerald-200',
  checking: 'bg-amber-50 text-amber-900 ring-amber-300',
  alert: 'bg-red-600 text-white ring-red-700',
  unknown: 'bg-slate-100 text-slate-800 ring-slate-300',
}

/**
 * The big status: readable from across the room. Without a connection it never claims that all is
 * well; an alert that was already showing stays red.
 */
export default function StatusCard({ incident, activity, status, lastHeard, connection = 'connected' }) {
  const known = stateTone(incident.state)
  const blind = connection === 'connected' && status && status.camera !== 'ok'   // connected, camera off
  const tone = (connection !== 'connected' || blind) && known !== 'alert' ? 'unknown' : known
  if (tone === 'unknown') {
    return (
      <section className={`rounded-3xl p-6 ring-2 sm:p-8 ${LOOK.unknown}`} aria-live="polite">
        <p className="text-sm font-semibold uppercase tracking-widest opacity-80">
          {blind ? 'Camera offline' : 'Not connected'}
        </p>
        <h2 className="mt-1 text-4xl font-extrabold sm:text-5xl">
          {blind ? 'Guardian cannot see the room' : 'Status unknown'}
        </h2>
        <p className="mt-4 text-lg">
          {blind ? 'Falls cannot be noticed until the camera is back. The family is told after 2 minutes.'
            : 'Guardian is not answering this page. Reconnecting by itself...'}
        </p>
      </section>
    )
  }
  const doing = activity ? ACTIVITY[activity.activity] ?? activity.activity : 'Waiting for the room...'
  const headline =
    tone === 'alert' ? 'ALERT - family notified' : tone === 'checking' ? 'Checking in...' : 'All is well'
  return (
    <section className={`rounded-3xl p-6 ring-2 sm:p-8 ${LOOK[tone]}`} aria-live="polite">
      <p className="text-sm font-semibold uppercase tracking-widest opacity-80">
        {incident.state === 'monitoring' ? 'Monitoring' : STATE[incident.state] ?? incident.state}
        {connection !== 'connected' && ' (last known)'}
      </p>
      <h2 className="mt-1 text-4xl font-extrabold sm:text-5xl">{headline}</h2>
      <p className="mt-4 text-2xl font-semibold sm:text-3xl">{doing}</p>
      {activity?.zone && <p className="mt-1 text-lg opacity-80">on the {activity.zone} (safe zone)</p>}
      {tone !== 'ok' && lastHeard && <p className="mt-3 text-lg">{lastHeard}</p>}
      <p className="mt-4 text-sm opacity-75">
        Camera {status?.camera === 'ok' ? `on (${status.fps.toFixed(0)} FPS)` : 'offline'}
      </p>
    </section>
  )
}
