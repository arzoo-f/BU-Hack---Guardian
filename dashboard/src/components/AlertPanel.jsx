import { useEffect, useRef, useState } from 'react'
import { acknowledge } from '../lib/api.js'

/** Beeps every 1.5 s while `active` and sound is enabled (browsers need a click before any sound). */
export function useAlarm(active, enabled) {
  const ctx = useRef(null)
  useEffect(() => {
    if (!active || !enabled) return undefined
    ctx.current ??= new (window.AudioContext || window.webkitAudioContext)()
    const beep = () => {
      const audio = ctx.current
      const osc = audio.createOscillator()
      const gain = audio.createGain()
      osc.frequency.value = 880
      gain.gain.setValueAtTime(0.0001, audio.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.3, audio.currentTime + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.5)
      osc.connect(gain).connect(audio.destination)
      osc.start()
      osc.stop(audio.currentTime + 0.5)
    }
    beep()
    const timer = setInterval(beep, 1500)
    return () => clearInterval(timer)
  }, [active, enabled])
}

/** Red alert: what was heard, why Guardian escalated, and the Acknowledge button. */
export default function AlertPanel({ incidentId, heard, reason }) {
  const [state, setState] = useState('idle')
  const onAck = async () => {
    setState('sending')
    const result = await acknowledge(incidentId).catch(() => ({ ok: false, status: 0 }))
    setState(result.ok ? 'done' : result.status === 409 ? 'already' : 'failed')
  }
  return (
    <section className="rounded-3xl bg-red-50 p-6 ring-2 ring-red-300">
      <h2 className="text-2xl font-bold text-red-800">Someone needs to check on them now</h2>
      <p className="mt-3 text-lg text-red-900">
        <span className="font-semibold">Heard: </span>
        {heard || 'no answer'}
      </p>
      {reason && (
        <p className="mt-1 text-lg text-red-900">
          <span className="font-semibold">Why: </span>
          {reason}
        </p>
      )}
      <button
        type="button"
        onClick={onAck}
        disabled={state === 'sending' || state === 'done'}
        className="mt-5 w-full rounded-2xl bg-red-600 px-6 py-4 text-xl font-bold text-white shadow hover:bg-red-700 disabled:opacity-60 sm:w-auto"
      >
        {state === 'sending' ? 'Sending...' : state === 'done' ? 'Acknowledged' : 'Acknowledge - I am handling it'}
      </button>
      {state === 'failed' && <p className="mt-2 text-red-800">Could not reach Guardian. Try again.</p>}
      {state === 'already' && <p className="mt-2 text-red-800">Someone has already acknowledged this.</p>}
    </section>
  )
}
