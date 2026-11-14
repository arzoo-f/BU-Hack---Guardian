import ActivityBand from '../components/ActivityBand.jsx'
import { Empty, Loading, Offline } from '../components/LoadState.jsx'
import { ACTIVITY, dayLabel, humanMinutes } from '../lib/labels.js'
import { navigate } from '../lib/router.js'
import { usePolled } from '../lib/usePolled.js'

const REFRESH_MS = 30000
const CARD = 'rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200'

function Tile({ label, value, note }) {
  return (
    <div className={CARD}>
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-900">{value}</p>
      {note && <p className="mt-1 text-sm text-slate-500">{note}</p>}
    </div>
  )
}

function shiftDay(isoDate, days) {
  const d = new Date(`${isoDate}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

const NAV = 'rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 ring-1 ring-slate-300 hover:bg-slate-100'

/**
 * One day from the activity log: the band, three numbers and the same minutes as a table.
 * `today` is today's local date; earlier days can be browsed with the arrows.
 */
export function TodayView({ timeline, day, today }) {
  const isToday = timeline.date === today
  const rows = day ? Object.entries(day.minutes).sort((a, b) => b[1] - a[1]) : []
  const simulated = timeline.segments.some((s) => s.simulated)
  const goTo = (date) => (date === today ? navigate('today') : navigate('today', date))
  return (
    <div className="space-y-4">
      <section className={CARD}>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-2xl font-bold text-slate-900">
            {isToday ? 'Today' : 'Day'} · {dayLabel(timeline.date)}
            {simulated && (
              <span className="ml-3 rounded-full bg-slate-100 px-3 py-1 align-middle text-xs font-medium text-slate-600 ring-1 ring-slate-200">
                Simulated history
              </span>
            )}
          </h2>
          <div className="flex gap-2">
            <button type="button" className={NAV} onClick={() => goTo(shiftDay(timeline.date, -1))}>← Previous day</button>
            {!isToday && <button type="button" className={NAV} onClick={() => goTo(shiftDay(timeline.date, 1))}>Next day →</button>}
          </div>
        </div>
        {timeline.segments.length ? (
          <ActivityBand timeline={timeline} showNow={isToday} />
        ) : (
          <Empty>
            {isToday ? 'Nothing recorded yet today. As soon as the camera sees someone, the day fills in here.'
              : 'Nothing was recorded on this day.'}
          </Empty>
        )}
        {isToday && <p className="mt-2 text-sm text-slate-500">From the camera, updated every 30 s.</p>}
      </section>
      {day && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Tile label={isToday ? 'Active today' : 'Active'} value={humanMinutes(day.active_minutes)} note="standing or walking" />
          <Tile label="Stood up from sitting" value={`${day.sit_to_stand} ${day.sit_to_stand === 1 ? 'time' : 'times'}`} />
          <Tile label="Longest still period" value={humanMinutes(day.longest_still_min)} note="sitting or lying without a break" />
        </div>
      )}
      {rows.length > 0 && (
        <section className={CARD}>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Time per activity</h3>
          <table className="w-full text-left">
            <tbody className="divide-y divide-slate-100">
              {rows.map(([activity, minutes]) => (
                <tr key={activity}>
                  <td className="py-1.5 text-slate-700">{ACTIVITY[activity] ?? activity}</td>
                  <td className="py-1.5 text-right font-medium tabular-nums text-slate-900">{humanMinutes(minutes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}

export default function Today({ connection, date }) {
  const band = usePolled(`/analytics/timeline${date ? `?date=${encodeURIComponent(date)}` : ''}`, REFRESH_MS, connection)
  const daily = usePolled('/analytics/daily', REFRESH_MS, connection)
  const error = band.error || daily.error
  const ready = band.data && daily.data
  const day = ready ? daily.data.days.find((d) => d.date === band.data.date) : null
  return (
    <div className="space-y-4">
      {error && <Offline what="activity" error={error} hasData={Boolean(ready)} />}
      {ready ? <TodayView timeline={band.data} day={day} today={daily.data.today.date} />
        : !error && <Loading what="the day's activity" />}
    </div>
  )
}
