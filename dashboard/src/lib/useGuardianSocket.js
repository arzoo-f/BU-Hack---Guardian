import { useEffect, useState } from 'react'
import { messageToStep } from './labels.js'
import { DASHBOARD_WS } from './server.js'

const MAX_EVENTS = 30
const MAX_BACKOFF_MS = 3000

/**
 * Live connection to the server's /ws/dashboard (messages follow contracts/dashboard).
 * Reconnects by itself. Returns the connection state, the latest status, activity and pose,
 * the open incident { id, state }, the live steps of the latest incident, and recent events.
 */
export function useGuardianSocket() {
  const [connection, setConnection] = useState('connecting')
  const [status, setStatus] = useState(null)
  const [activity, setActivity] = useState(null)
  const [pose, setPose] = useState(null)
  const [incident, setIncident] = useState({ id: null, state: 'monitoring' })
  const [steps, setSteps] = useState({ incidentId: null, list: [] })
  const [events, setEvents] = useState([])

  useEffect(() => {
    // Local to this effect run, so a closed socket from an earlier run never reconnects.
    let closed = false
    let timer = null
    let delay = 1000
    let ws

    const connect = () => {
      setConnection('connecting')
      ws = new WebSocket(DASHBOARD_WS)
      ws.onopen = () => {
        delay = 1000
        setConnection('connected')
      }
      ws.onmessage = (e) => {
        let msg
        try {
          msg = JSON.parse(e.data)
        } catch {
          return
        }
        if (msg.state) {
          setIncident((old) =>
            old.id === (msg.incident_id ?? null) && old.state === msg.state
              ? old
              : { id: msg.incident_id ?? null, state: msg.state },
          )
        }
        if (msg.type === 'pose') {
          setPose({ ...msg, receivedAt: Date.now() })
          return
        }
        if (msg.type === 'status') setStatus(msg)
        if (msg.type === 'activity') setActivity(msg)
        if (msg.type === 'incident_update' || msg.type === 'decision') {
          const step = messageToStep(msg)
          setSteps((old) =>
            old.incidentId === msg.incident_id
              ? { incidentId: old.incidentId, list: [...old.list, step] }
              : { incidentId: msg.incident_id, list: [step] },
          )
        }
        setEvents((prev) => [msg, ...prev].slice(0, MAX_EVENTS))
      }
      ws.onclose = () => {
        if (closed) return
        setConnection('disconnected')
        timer = setTimeout(connect, delay)
        delay = Math.min(delay * 2, MAX_BACKOFF_MS)
      }
    }

    // Started on the next tick: React's development double start then cancels the timer instead of
    // closing a socket that is still opening (a console warning otherwise).
    timer = setTimeout(connect, 0)
    return () => {
      closed = true
      clearTimeout(timer)
      ws?.close()
    }
  }, [])

  return { connection, status, activity, pose, incident, steps, events }
}
