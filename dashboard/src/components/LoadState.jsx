// Loading, offline and empty states, the same on every page (BUILD_PLAN step 7.6).

const BOX = 'rounded-2xl bg-white p-6 ring-1 ring-slate-200'

export function Loading({ what }) {
  return (
    <p className={`${BOX} text-slate-500`} role="status">
      Loading {what}...
    </p>
  )
}

/** Could not reach Guardian: with data, a thin note above the last data; without, a box in its place. */
export function Offline({ what, error, hasData }) {
  if (hasData) {
    return (
      <p className="rounded-xl bg-amber-50 px-4 py-2 text-sm text-amber-900 ring-1 ring-amber-200" role="status">
        Guardian is not answering - showing the last {what} it sent. Retrying...
      </p>
    )
  }
  return (
    <div className={`${BOX} text-slate-700`} role="status">
      <p className="font-semibold">Cannot reach Guardian right now.</p>
      <p className="mt-1 text-sm text-slate-500">
        The {what} will appear as soon as the server is back. Retrying by itself{error ? ` (${error})` : ''}.
      </p>
    </div>
  )
}

export function Empty({ children }) {
  return <div className={`${BOX} text-slate-600`}>{children}</div>
}
