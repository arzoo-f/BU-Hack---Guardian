import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Empty, Loading, Offline } from '../components/LoadState.jsx'
import { dayLabel, humanMinutes } from '../lib/labels.js'
import { usePolled } from '../lib/usePolled.js'

const REFRESH_MS = 60000
const CARD = 'rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200'
const BLUE = '#2a78d6'
const INK = { muted: '#64748b', grid: '#e2e8f0', axis: '#cbd5e1' }

function ChartTip({ active, payload, format }) {
  if (!active || !payload?.length) return null
  const day = payload[0].payload
  return (
    <div className="rounded-lg bg-white px-3 py-1.5 text-sm shadow-md ring-1 ring-slate-200">
      <p className="font-semibold text-slate-900">{day.label}{day.simulated ? ' (simulated)' : ''}</p>
      <p className="text-slate-600">{day.hasData ? format(payload[0].value) : 'no data'}</p>
    </div>
  )
}

/** One measure per chart (never two scales on one chart): bars per day, today last. */
function DayBars({ title, note, data, dataKey, format, average }) {
  return (
    <section className={CARD}>
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      {note && <p className="text-sm text-slate-500">{note}</p>}
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 16, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid vertical={false} stroke={INK.grid} />
            <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: INK.axis }} tick={{ fill: INK.muted, fontSize: 12 }} interval={0} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: INK.muted, fontSize: 12 }} allowDecimals={false} width={44} />
            <Tooltip cursor={{ fill: 'rgba(15, 23, 42, 0.05)' }} content={<ChartTip format={format} />} />
            {average != null && (
              <ReferenceLine y={average} stroke={INK.muted} strokeDasharray="4 4"
                label={{ value: '7-day average', position: 'insideTopRight', fill: INK.muted, fontSize: 12 }} />
            )}
            <Bar dataKey={dataKey} fill={BLUE} radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

/** Seven days of mobility, the sit-to-stand count and the insight sentences (BUILD_PLAN step 7.5). */
export function InsightsView({ daily }) {
  const days = daily.days.map((d, i) => ({
    ...d,
    label: i === daily.days.length - 1 ? 'Today' : dayLabel(d.date),
    hasData: Object.keys(d.minutes).length > 0,
    active: Math.round(d.active_minutes),
  }))
  const past = days.slice(0, -1).filter((d) => d.hasData)
  const simulated = past.some((d) => d.simulated)
  const average = past.length ? past.reduce((sum, d) => sum + d.active_minutes, 0) / past.length : null
  if (!days.some((d) => d.hasData)) {
    return (
      <Empty>
        No activity recorded yet. Insights appear after Guardian has watched the room for a while; for the demo,
        run <code className="rounded bg-slate-100 px-1">scripts\seed_history.py</code> to add a simulated week.
      </Empty>
    )
  }
  return (
    <div className="space-y-4">
      <section className={CARD}>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-2xl font-bold text-slate-900">Insights</h2>
          {simulated && (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200"
              title="The days before today were generated for the demo; today is real.">
              Earlier days: simulated history
            </span>
          )}
        </div>
        {daily.insights.length ? (
          <ul className="mt-3 space-y-2">
            {daily.insights.map((text) => (
              <li key={text} className="text-lg text-slate-800">{text}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-slate-600">No insights for today yet: nothing has been recorded today.</p>
        )}
      </section>
      <div className="grid gap-4 lg:grid-cols-2">
        <DayBars title="Minutes active per day" note="Standing or walking. Today counts up to now." data={days}
          dataKey="active" format={(v) => `${humanMinutes(v)} active`} average={average} />
        <DayBars title="Stood up from sitting" note="Times per day: a simple sign of leg strength." data={days}
          dataKey="sit_to_stand" format={(v) => `${v} ${v === 1 ? 'time' : 'times'}`} />
      </div>
      <section className={CARD}>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">The same numbers</h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[22rem] text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="py-1.5 font-medium">Day</th>
                <th className="py-1.5 text-right font-medium">Active</th>
                <th className="py-1.5 text-right font-medium">Stood up</th>
                <th className="py-1.5 text-right font-medium">Longest still</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 tabular-nums">
              {days.map((d) => (
                <tr key={d.date}>
                  <td className="py-1.5 text-slate-700">{d.label}{d.simulated ? ' *' : ''}</td>
                  {d.hasData ? (
                    <>
                      <td className="py-1.5 text-right text-slate-900">{humanMinutes(d.active_minutes)}</td>
                      <td className="py-1.5 text-right text-slate-900">{d.sit_to_stand}</td>
                      <td className="py-1.5 text-right text-slate-900">{humanMinutes(d.longest_still_min)}</td>
                    </>
                  ) : (
                    <td colSpan={3} className="py-1.5 text-right text-slate-400">no data</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {simulated && <p className="mt-2 text-xs text-slate-500">* simulated history</p>}
      </section>
    </div>
  )
}

export default function Insights({ connection }) {
  const daily = usePolled('/analytics/daily', REFRESH_MS, connection)
  return (
    <div className="space-y-4">
      {daily.error && <Offline what="insights" error={daily.error} hasData={Boolean(daily.data)} />}
      {daily.data ? <InsightsView daily={daily.data} /> : !daily.error && <Loading what="insights" />}
    </div>
  )
}
