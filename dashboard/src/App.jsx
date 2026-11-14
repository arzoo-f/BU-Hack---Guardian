import { useEffect, useRef, useState } from 'react'
import { useAlarm } from './components/AlertPanel.jsx'
import { stateTone } from './lib/labels.js'
import { navigate, useHashRoute } from './lib/router.js'
import { useGuardianSocket } from './lib/useGuardianSocket.js'
import { usePolled } from './lib/usePolled.js'
import IncidentDetail from './pages/IncidentDetail.jsx'
import Incidents from './pages/Incidents.jsx'
import Insights from './pages/Insights.jsx'
import Live from './pages/Live.jsx'
import Settings from './pages/Settings.jsx'
import Today from './pages/Today.jsx'

const PAGES = [
  ['live', 'Live'],
  ['today', 'Today'],
  ['insights', 'Insights'],
  ['incidents', 'Incidents'],
  ['settings', 'Settings'],
]
const BACK_TO_LIVE_MS = 8000

function readDemoFlag() {
  if (new URLSearchParams(window.location.search).get('demo') === '1') return true
  try {
    return window.localStorage.getItem('guardian.demo') === '1'
  } catch {
    return false
  }
}

function ConnectionBadge({ connection }) {
  const look = {
    connected: ['bg-emerald-100 text-emerald-800', 'Connected'],
    connecting: ['bg-amber-100 text-amber-800', 'Connecting...'],
    disconnected: ['bg-slate-200 text-slate-700', 'Offline - retrying'],
  }[connection]
  return <span className={`rounded-full px-3 py-1 text-sm font-medium ${look[0]}`}>{look[1]}</span>
}

/**
 * Demo mode: follow the open incident by itself, and return to Live a few seconds after it ends,
 * so nobody has to click during the recording (BUILD_PLAN step 5.4).
 */
function useDemoMode(enabled, incident) {
  const followed = useRef(null)
  useEffect(() => {
    if (!enabled) return undefined
    if (incident.id && incident.state !== 'monitoring' && incident.state !== 'resolved') {
      followed.current = incident.id
      navigate('incident', incident.id)
      return undefined
    }
    if (followed.current) {
      const timer = setTimeout(() => {
        followed.current = null
        navigate('live')
      }, BACK_TO_LIVE_MS)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [enabled, incident.id, incident.state])
}

export default function App() {
  const live = useGuardianSocket()
  const route = useHashRoute()
  // Re-read every 10 s: zones drawn in the camera's debug window show up without a reload.
  const zones = usePolled('/zones', 10000, live.connection).data?.zones ?? []
  const [demo, setDemo] = useState(readDemoFlag)
  const [sound, setSound] = useState(false)
  const tone = stateTone(live.incident.state)

  useDemoMode(demo, live.incident)
  useAlarm(tone === 'alert', sound)

  const toggleDemo = () => {
    setDemo((on) => {
      try {
        window.localStorage.setItem('guardian.demo', on ? '0' : '1')
      } catch {
        // per-viewer convenience only
      }
      return !on
    })
  }

  let page
  if (route.page === 'incident' && route.id) page = <IncidentDetail id={route.id} live={live} />
  else if (route.page === 'incidents') page = <Incidents incident={live.incident} connection={live.connection} />
  else if (route.page === 'today') page = <Today connection={live.connection} date={route.id} />
  else if (route.page === 'insights') page = <Insights connection={live.connection} />
  else if (route.page === 'settings') page = <Settings connection={live.connection} />
  else page = <Live live={live} zones={zones} />

  return (
    <div className={`min-h-screen ${tone === 'alert' ? 'bg-red-100' : 'bg-slate-50'}`}>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex flex-wrap items-center gap-4">
            <h1 className="text-2xl font-bold text-slate-900">Guardian</h1>
            <nav className="flex flex-wrap gap-1">
              {PAGES.map(([key, label]) => (
                <a key={key} href={`#/${key}`}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium ${route.page === key ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100'}`}>
                  {label}
                </a>
              ))}
            </nav>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setSound((s) => !s)}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 ring-1 ring-slate-300 hover:bg-slate-100">
              {sound ? 'Sound on' : 'Sound off'}
            </button>
            <button type="button" onClick={toggleDemo}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ring-1 ${demo ? 'bg-sky-600 text-white ring-sky-700' : 'text-slate-700 ring-slate-300 hover:bg-slate-100'}`}>
              Demo mode {demo ? 'on' : 'off'}
            </button>
            <ConnectionBadge connection={live.connection} />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4 sm:p-6">{page}</main>
    </div>
  )
}
