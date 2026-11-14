import { useState } from 'react'
import { BAND, bandGroup, humanMinutes } from '../lib/labels.js'

const DAY_MS = 24 * 3600 * 1000
const TICKS = [0, 3, 6, 9, 12, 15, 18, 21, 24]
const GAP_MIN_PCT = 0.3 // segments narrower than this (about 4 min) get no white gap, so short ones stay visible

/** Minutes since the start of the local day -> '09:05' (the server sends the day's start, so no time zone guessing). */
function clock(ms) {
  const minutes = Math.max(0, Math.round(ms / 60000))
  return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`
}

/**
 * One day as a coloured band from midnight to midnight (BUILD_PLAN step 7.4). Grey means no data or
 * nobody in view. Hover or tap a part of the band to see what it was and for how long.
 */
export default function ActivityBand({ timeline, showNow = true }) {
  const [hover, setHover] = useState(null)
  const start = Date.parse(timeline.from)
  const pct = (iso) => ((Date.parse(iso) - start) / DAY_MS) * 100
  const segments = timeline.segments
    .map((s) => ({ ...s, group: bandGroup(s.activity), x: pct(s.from), w: pct(s.to) - pct(s.from) }))
    .filter((s) => s.group && s.w > 0)
  const present = Object.keys(BAND).filter((g) => g !== 'fallen' || segments.some((s) => s.group === 'fallen'))
  const nowX = pct(timeline.now)

  const pick = (event) => {
    const box = event.currentTarget.getBoundingClientRect()
    const x = ((event.clientX - box.left) / box.width) * 100
    const seg = segments.find((s) => x >= s.x && x <= s.x + s.w)
    setHover(seg ? { seg, x: Math.min(Math.max(x, 12), 88) } : null)
  }

  return (
    <div>
      <ul className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-700">
        {present.map((g) => (
          <li key={g} className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded-sm" style={{ background: BAND[g].color }} />
            {BAND[g].label}
          </li>
        ))}
        <li className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-slate-200" />
          No data / not in view
        </li>
      </ul>
      <div className="relative pt-1">
        <div className="relative h-14 cursor-crosshair overflow-hidden rounded-md bg-slate-200"
          onMouseMove={pick} onClick={pick} onMouseLeave={() => setHover(null)}
          role="img" aria-label={`Activity band for ${timeline.date}; the table below lists the same minutes.`}>
          {segments.map((s) => (
            <div key={s.from} className="absolute inset-y-0" style={{ left: `${s.x}%`, width: `${s.w}%` }}>
              <div className={`h-full ${s.w >= GAP_MIN_PCT ? 'mx-px' : ''} ${hover?.seg === s ? 'opacity-80' : ''}`}
                style={{ background: BAND[s.group].color }} />
            </div>
          ))}
          {showNow && nowX > 0 && nowX < 100 && (
            <div className="absolute inset-y-0 w-0.5 bg-slate-900" style={{ left: `${nowX}%` }} />
          )}
        </div>
        {hover && (
          <div className="pointer-events-none absolute -top-14 z-10 -translate-x-1/2 whitespace-nowrap rounded-lg bg-white px-3 py-1.5 text-sm shadow-md ring-1 ring-slate-200"
            style={{ left: `${hover.x}%` }}>
            <span className="font-semibold text-slate-900">{BAND[hover.seg.group].short}</span>
            <span className="ml-2 text-slate-600">
              {clock(Date.parse(hover.seg.from) - start)}-{clock(Date.parse(hover.seg.to) - start)} ·{' '}
              {humanMinutes((Date.parse(hover.seg.to) - Date.parse(hover.seg.from)) / 60000)}
            </span>
          </div>
        )}
        <div className={`relative mt-1 text-xs tabular-nums text-slate-500 ${showNow ? 'h-10' : 'h-5'}`}>
          {TICKS.map((h) => (
            <span key={h} className={`absolute ${h === 0 ? '' : h === 24 ? '-translate-x-full' : '-translate-x-1/2'} ${h % 6 ? 'hidden sm:block' : ''}`}
              style={{ left: `${(h / 24) * 100}%` }}>
              {String(h).padStart(2, '0')}
            </span>
          ))}
          {showNow && nowX > 0 && nowX < 100 && (
            <span className={`absolute top-5 font-semibold text-slate-900 ${nowX > 95 ? '-translate-x-full' : nowX < 5 ? '' : '-translate-x-1/2'}`}
              style={{ left: `${nowX}%` }}>now</span>
          )}
        </div>
      </div>
    </div>
  )
}
