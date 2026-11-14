import { describeStep, timeOf } from '../lib/labels.js'

const DOT = { ok: 'bg-emerald-500', checking: 'bg-amber-500', alert: 'bg-red-600' }

/** An incident, step by step: what was said, heard and decided, and why. */
export default function Steps({ steps }) {
  if (!steps?.length) return <p className="text-slate-500">No steps yet.</p>
  return (
    <ol className="space-y-3">
      {steps.map((step, i) => {
        const s = describeStep(step)
        return (
          <li key={`${step.ts}-${i}`} className="flex gap-3">
            <span className={`mt-2 h-2.5 w-2.5 shrink-0 rounded-full ${DOT[s.tone] ?? DOT.ok}`} aria-hidden />
            <div className="min-w-0">
              <p className="font-semibold text-slate-900">
                <span aria-hidden>{s.icon} </span>
                {s.title}
                <span className="ml-2 text-sm font-normal text-slate-400">{timeOf(step.ts)}</span>
              </p>
              {s.detail && <p className="break-words text-slate-700">{s.detail}</p>}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
