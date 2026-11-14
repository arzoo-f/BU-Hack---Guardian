// Plain-English wording for everything the dashboard shows.

export const ACTIVITY = {
  standing: 'Standing',
  walking: 'Walking',
  sitting: 'Sitting',
  lying: 'Lying down',
  fallen: 'On the floor',
  absent: 'Not in view',
}

export const STATE = {
  monitoring: 'All is well',
  checkin_1: 'Checking in',
  checkin_2: 'Checking in again',
  follow_up: 'Follow-up',
  escalate: 'ALERT',
  resolved: 'Resolved',
}

/** Calm colours for OK, amber while checking in, red only for alerts (BUILD_PLAN Stage 5 design rules). */
export function stateTone(state) {
  if (state === 'escalate') return 'alert'
  if (state === 'checkin_1' || state === 'checkin_2' || state === 'follow_up') return 'checking'
  return 'ok'
}

const ACTIONS = {
  follow_up: 'ask whether they need anything',
  ask_again: 'ask again',
  escalate: 'alert the family',
  resolve: 'close the incident',
}

export function decidedBy(decision) {
  if (decision.source === 'ai') return 'AI'
  if (decision.rule) return `Safety rule ${decision.rule}`
  return "Guardian's rules"
}

const quoted = (text) => `“${text}”`

/**
 * One incident step (a stored incident_events row, or a live incident_update / decision message)
 * as { icon, title, detail, tone }.
 */
export function describeStep(step) {
  const p = step.payload || {}
  switch (step.kind) {
    case 'state':
      if (p.event === 'fall_detected_again') return { icon: '⚠️', title: 'Another fall was detected', tone: 'checking' }
      if (p.event === 'restored_after_restart') return { icon: '🔄', title: 'Guardian restarted during this incident', tone: 'alert' }
      if (p.event === 'closed_by_real_fall') return { icon: '⏹️', title: 'Closed: a real fall happened', tone: 'ok' }
      if (p.from === 'monitoring') {
        const what = (step.reason || p.reason) === 'found_on_floor' ? 'Found on the floor' : 'Fall detected'
        return { icon: '🧍', title: what + (step.simulated ? ' (simulated)' : ''), tone: 'checking' }
      }
      return { icon: '➡️', title: `Now: ${STATE[p.to] || p.to}`, detail: p.note, tone: stateTone(p.to) }
    case 'speak':
      return { icon: '🔊', title: 'Guardian asked', detail: quoted(p.text), tone: 'checking' }
    case 'reply':
      if (p.heard_speech && p.transcript) return { icon: '👂', title: 'Heard', detail: quoted(p.transcript), tone: 'ok' }
      return { icon: '🔇', title: p.missing ? 'No reply arrived' : 'No answer heard', tone: 'checking' }
    case 'decision': {
      const d = step.decision || p
      return {
        icon: d.action === 'escalate' ? '🚨' : '🧠',
        title: `${decidedBy(d)}: ${ACTIONS[d.action] || d.action}`,
        detail: d.reason,
        tone: d.action === 'escalate' ? 'alert' : 'ok',
      }
    }
    case 'alert':
      if (p.sent && p.channel === 'log') {
        return { icon: '📝', title: `Family alert #${p.attempt} written to the test log`, detail: 'Telegram is switched off', tone: 'alert' }
      }
      return p.sent
        ? { icon: '📱', title: p.attempt > 1 ? `Reminder sent to family (#${p.attempt})` : 'Family alerted on Telegram', tone: 'alert' }
        : { icon: '⏳', title: `Alert #${p.attempt} could not be sent - retrying`, tone: 'alert' }
    case 'ack':
      return { icon: '✅', title: `Acknowledged by ${p.by}`, tone: 'ok' }
    case 'request':
      return { icon: '💬', title: 'They asked for something', detail: `${quoted(p.request)} - family told (not urgent)`, tone: 'ok' }
    default:
      return { icon: '•', title: step.kind, tone: 'ok' }
  }
}

/** A live dashboard message as a step (decision messages carry the decision at the top level). */
export function messageToStep(msg) {
  if (msg.type === 'decision') {
    const { type, ts, incident_id, state, ...decision } = msg
    return { ts, kind: 'decision', payload: decision, incident_id }
  }
  return { ts: msg.ts, kind: msg.kind, payload: msg.payload, reason: msg.reason, simulated: msg.simulated, incident_id: msg.incident_id }
}

export function timeOf(ts) {
  return ts ? new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''
}

export function dateTimeOf(ts) {
  return ts ? new Date(ts).toLocaleString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' }) : ''
}

/**
 * The Today band groups activities by what matters for mobility: standing and walking count as active,
 * like in the server's analytics. Colours are categorical slots 1-3, checked for colour-blind safety in
 * every pairing; "On the floor" uses the reserved alert red and always comes with its label.
 */
export const BAND = {
  active: { label: 'Active (standing or walking)', short: 'Active', color: '#2a78d6' },
  sitting: { label: 'Sitting', short: 'Sitting', color: '#eb6834' },
  lying: { label: 'Lying down', short: 'Lying down', color: '#1baf7a' },
  fallen: { label: '⚠ On the floor', short: '⚠ On the floor', color: '#d03b3b' },
}

export function bandGroup(activity) {
  if (activity === 'standing' || activity === 'walking') return 'active'
  return BAND[activity] ? activity : null
}

/** 95 -> '1 h 35 min'; 7 -> '7 min' (same as the server's human_duration). */
export function humanMinutes(minutes) {
  const m = Math.round(minutes)
  return m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`
}

/** '2026-11-07' -> 'Sat 7' (the date is a local day from the server, so no time zone shift). */
export function dayLabel(isoDate) {
  return new Date(`${isoDate}T12:00:00Z`).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', timeZone: 'UTC' })
}
