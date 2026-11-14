// Dashboard checks without a browser: wording helpers, routing, and every component rendered with
// sample data (server-side rendering), so a crash or a missing word shows up as a failed test.
import { renderToString as renderRaw } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import AlertPanel from './components/AlertPanel.jsx'
import Skeleton from './components/Skeleton.jsx'
import StatusCard from './components/StatusCard.jsx'
import Steps from './components/Steps.jsx'
import ActivityBand from './components/ActivityBand.jsx'
import { Loading, Offline } from './components/LoadState.jsx'
import { bandGroup, dayLabel, describeStep, humanMinutes, messageToStep, stateTone } from './lib/labels.js'
import { parseHash } from './lib/router.js'
import { IncidentList } from './pages/Incidents.jsx'
import { InsightsView } from './pages/Insights.jsx'
import Live from './pages/Live.jsx'
import { TodayView } from './pages/Today.jsx'

// React marks the joins between text pieces with <!-- -->; remove them to search the visible text.
const renderToString = (element) => renderRaw(element).replaceAll('<!-- -->', '')

const TS = '2026-11-14T02:07:12.000Z'
const STEPS = [
  { ts: TS, kind: 'state', payload: { from: 'monitoring', to: 'checkin_1' }, reason: 'fast_fall' },
  { ts: TS, kind: 'speak', payload: { text: 'Are you okay? Please say yes or no.', attempt: 1 } },
  { ts: TS, kind: 'reply', payload: { attempt: 1, transcript: 'help me', heard_speech: true } },
  { ts: TS, kind: 'decision', payload: { action: 'escalate', reason: 'Help keyword heard: "help".', source: 'hard_rule', rule: 2 } },
  { ts: TS, kind: 'state', payload: { from: 'checkin_1', to: 'escalate' } },
  { ts: TS, kind: 'alert', payload: { attempt: 1, sent: true } },
]

describe('wording', () => {
  it('describes each kind of step in plain English', () => {
    expect(describeStep(STEPS[0]).title).toBe('Fall detected')
    expect(describeStep({ ...STEPS[0], reason: 'found_on_floor', simulated: true }).title).toBe('Found on the floor (simulated)')
    expect(describeStep(STEPS[1])).toMatchObject({ title: 'Guardian asked', detail: '“Are you okay? Please say yes or no.”' })
    expect(describeStep(STEPS[2])).toMatchObject({ title: 'Heard', detail: '“help me”' })
    expect(describeStep({ kind: 'reply', payload: { heard_speech: false, transcript: '' } }).title).toBe('No answer heard')
    expect(describeStep({ kind: 'reply', payload: { missing: true } }).title).toBe('No reply arrived')
    expect(describeStep(STEPS[3])).toMatchObject({ title: 'Safety rule 2: alert the family', tone: 'alert' })
    expect(describeStep({ kind: 'decision', payload: { action: 'follow_up', source: 'ai', reason: 'ok' } }).title)
      .toBe('AI: ask whether they need anything')
    expect(describeStep(STEPS[4]).title).toBe('Now: ALERT')
    expect(describeStep(STEPS[5]).title).toBe('Family alerted on Telegram')
    expect(describeStep({ kind: 'alert', payload: { attempt: 2, sent: true } }).title).toBe('Reminder sent to family (#2)')
    expect(describeStep({ kind: 'alert', payload: { attempt: 1, sent: false } }).title).toMatch(/could not be sent/)
    expect(describeStep({ kind: 'alert', payload: { attempt: 1, sent: true, channel: 'log' } }))
      .toMatchObject({ title: 'Family alert #1 written to the test log', detail: 'Telegram is switched off' })
    expect(describeStep({ kind: 'alert', payload: { attempt: 1, sent: true, channel: 'telegram' } }).title)
      .toBe('Family alerted on Telegram')
    expect(describeStep({ kind: 'ack', payload: { by: 'Telegram: Ayesha B' } }).title).toBe('Acknowledged by Telegram: Ayesha B')
    expect(describeStep({ kind: 'request', payload: { request: 'some water' } }).detail).toMatch(/some water/)
    expect(describeStep({ kind: 'state', payload: { event: 'restored_after_restart' } }).tone).toBe('alert')
  })

  it('turns a live decision message into a step', () => {
    const step = messageToStep({ type: 'decision', ts: TS, incident_id: 'inc_001', state: 'checkin_1', action: 'follow_up',
      assessment: 'ok', say: '', request: null, reason: 'Clear yes.', source: 'ai' })
    expect(step).toMatchObject({ kind: 'decision', incident_id: 'inc_001', payload: { action: 'follow_up', reason: 'Clear yes.' } })
  })

  it('uses calm colours except for alerts', () => {
    expect(stateTone('monitoring')).toBe('ok')
    expect(stateTone('checkin_2')).toBe('checking')
    expect(stateTone('follow_up')).toBe('checking')
    expect(stateTone('escalate')).toBe('alert')
  })

  it('reads the page from the address', () => {
    expect(parseHash('')).toEqual({ page: 'live', id: null })
    expect(parseHash('#/incidents')).toEqual({ page: 'incidents', id: null })
    expect(parseHash('#/incident/inc_20261113143454_1')).toEqual({ page: 'incident', id: 'inc_20261113143454_1' })
  })
})

describe('components render', () => {
  const activity = { activity: 'fallen', zone: null }
  const status = { camera: 'ok', fps: 15.04 }

  it('status card in all three moods', () => {
    const ok = renderToString(<StatusCard incident={{ id: null, state: 'monitoring' }} activity={{ activity: 'lying', zone: 'sofa' }} status={status} />)
    expect(ok).toContain('All is well')
    expect(ok.match(/All is well/g)).toHaveLength(1)
    expect(ok).toContain('Monitoring')
    expect(ok).toContain('Lying down')
    expect(ok).toContain('sofa (safe zone)')
    expect(ok).toContain('Camera on (15 FPS)')
    const checking = renderToString(<StatusCard incident={{ id: 'inc_1', state: 'checkin_1' }} activity={activity} status={status} lastHeard="Heard: no answer" />)
    expect(checking).toContain('Checking in...')
    expect(checking).toContain('Heard: no answer')
    const alert = renderToString(<StatusCard incident={{ id: 'inc_1', state: 'escalate' }} activity={activity} status={{ camera: 'offline', fps: 0 }} />)
    expect(alert).toContain('ALERT - family notified')
    expect(alert).toContain('On the floor')
    expect(alert).toContain('Camera offline')
  })

  it('status card never says all is well without a connection, and keeps an alert red', () => {
    const offline = renderToString(<StatusCard incident={{ id: null, state: 'monitoring' }} activity={null} status={null}
      connection="disconnected" />)
    expect(offline).toContain('Status unknown')
    expect(offline).not.toContain('All is well')
    const alert = renderToString(<StatusCard incident={{ id: 'inc_1', state: 'escalate' }} activity={activity} status={status}
      connection="disconnected" />)
    expect(alert).toContain('ALERT - family notified')
    expect(alert).toContain('(last known)')
    const blind = renderToString(<StatusCard incident={{ id: null, state: 'monitoring' }} activity={null}
      status={{ camera: 'offline', fps: 0 }} />)
    expect(blind).toContain('Guardian cannot see the room')
    expect(blind).not.toContain('All is well')
  })

  it('steps, alert panel and skeleton', () => {
    const steps = renderToString(<Steps steps={STEPS} />)
    expect(steps).toContain('Safety rule 2: alert the family')
    expect(steps).toContain('Family alerted on Telegram')
    expect(renderToString(<Steps steps={[]} />)).toContain('No steps yet')
    const panel = renderToString(<AlertPanel incidentId="inc_1" heard="“help me”" reason="Help keyword heard." />)
    expect(panel).toContain('Acknowledge - I am handling it')
    expect(panel).toContain('Help keyword heard.')
    expect(renderToString(<Skeleton pose={null} zones={[]} />)).toContain('Waiting for the camera')
  })

  it('live page during an alert shows the story and the button', () => {
    const live = {
      incident: { id: 'inc_1', state: 'escalate' }, activity, status, pose: null,
      steps: { incidentId: 'inc_1', list: STEPS },
    }
    const html = renderToString(<Live live={live} zones={[{ name: 'sofa', polygon: [[0.4, 0.33], [0.52, 0.33], [0.52, 0.45]] }]} />)
    expect(html).toContain('ALERT - family notified')
    expect(html).toContain('Acknowledge - I am handling it')
    expect(html).toContain('What is happening')
    expect(html).toContain('“help me”')
  })

  it('live page when all is well shows no incident box', () => {
    const live = { incident: { id: null, state: 'monitoring' }, activity: { activity: 'walking' }, status, pose: null,
      steps: { incidentId: null, list: [] } }
    const html = renderToString(<Live live={live} zones={[]} />)
    expect(html).toContain('All is well')
    expect(html).not.toContain('What is happening')
    expect(html).not.toContain('Acknowledge')
  })
})

describe('today and insights', () => {
  const day = (date, active, extra = {}) => ({
    date, minutes: active ? { walking: active, sitting: 300 } : {}, active_minutes: active, sit_to_stand: active ? 9 : 0,
    longest_still_min: active ? 95 : 0, simulated: false, ...extra,
  })
  const TIMELINE = {
    date: '2026-11-14', from: '2026-11-14T00:00:00+08:00', to: '2026-11-15T00:00:00+08:00', now: '2026-11-14T04:00:00+00:00',
    segments: [
      { from: '2026-11-14T01:00:00+00:00', to: '2026-11-14T01:30:00+00:00', activity: 'walking', simulated: false },
      { from: '2026-11-14T01:30:00+00:00', to: '2026-11-14T03:00:00+00:00', activity: 'sitting', simulated: false },
      { from: '2026-11-14T03:00:00+00:00', to: '2026-11-14T03:01:00+00:00', activity: 'absent', simulated: false },
    ],
  }

  it('groups and words the band', () => {
    expect([bandGroup('standing'), bandGroup('walking'), bandGroup('sitting'), bandGroup('fallen'), bandGroup('absent')])
      .toEqual(['active', 'active', 'sitting', 'fallen', null])
    expect(humanMinutes(95)).toBe('1 h 35 min')
    expect(humanMinutes(7.4)).toBe('7 min')
    expect(dayLabel('2026-11-07')).toBe('Sat 7')
  })

  it('band shows the legend, the hours and now; on the floor only when it happened', () => {
    const html = renderToString(<ActivityBand timeline={TIMELINE} />)
    expect(html).toContain('Active (standing or walking)')
    expect(html).toContain('No data / not in view')
    expect(html).toContain('>now<')
    expect(html).not.toContain('On the floor')
    expect(html.match(/left:(\d+(\.\d+)?)%;width:/g)).toHaveLength(2)      // the absent minute is left grey
    const fallen = { ...TIMELINE, segments: [{ ...TIMELINE.segments[0], activity: 'fallen' }] }
    expect(renderToString(<ActivityBand timeline={fallen} />)).toContain('⚠ On the floor')
  })

  it('today page: band, numbers and table; empty day', () => {
    const html = renderToString(<TodayView timeline={TIMELINE} day={day('2026-11-14', 30)} today="2026-11-14" />)
    expect(html).toContain('Today · Sat 14')
    expect(html).toContain('Previous day')
    expect(html).not.toContain('Next day')
    expect(html).not.toContain('Simulated history')
    expect(html).toContain('Stood up from sitting')
    expect(html).toContain('1 h 35 min')
    expect(html).toContain('Time per activity')
    const empty = renderToString(<TodayView timeline={{ ...TIMELINE, segments: [] }} day={day('2026-11-14', 0)} today="2026-11-14" />)
    expect(empty).toContain('Nothing recorded yet today')
    expect(empty).not.toContain('Time per activity')
    const past = { ...TIMELINE, date: '2026-11-13', segments: TIMELINE.segments.map((s) => ({ ...s, simulated: true })) }
    const earlier = renderToString(<TodayView timeline={past} day={day('2026-11-13', 150, { simulated: true })} today="2026-11-14" />)
    expect(earlier).toContain('Day · Fri 13')
    expect(earlier).toContain('Simulated history')
    expect(earlier).toContain('Next day')
    expect(earlier).not.toContain('>now<')
  })

  it('insights page: sentences, simulated label, both charts and the table', () => {
    const days = ['07', '08', '09', '10', '11', '12', '13'].map((n) => day(`2026-11-${n}`, 150, { simulated: true }))
    const daily = { days: [...days, day('2026-11-14', 30)], insights: ['Active 60% less than the 7-day average so far today.', 'Longest still period today: 1 h 35 min.'] }
    const html = renderToString(<InsightsView daily={daily} />)
    expect(html).toContain('Active 60% less than the 7-day average so far today.')
    expect(html).toContain('Earlier days: simulated history')
    expect(html).toContain('Minutes active per day')
    expect(html).toContain('Stood up from sitting')
    expect(html).toContain('Sat 7 *')
    expect(html).toContain('>Today<')
    const real = renderToString(<InsightsView daily={{ days: [day('2026-11-13', 0), day('2026-11-14', 30)], insights: [] }} />)
    expect(real).not.toContain('simulated history')
    expect(real).toContain('no data')
    expect(renderToString(<InsightsView daily={{ days: [day('2026-11-14', 0)], insights: [] }} />)).toContain('No activity recorded yet')
  })
})

describe('loading, offline and empty states', () => {
  it('shared notices', () => {
    expect(renderToString(<Loading what="insights" />)).toContain('Loading insights...')
    expect(renderToString(<Offline what="incidents" error="HTTP 500" hasData={false} />)).toContain('Cannot reach Guardian right now.')
    expect(renderToString(<Offline what="incidents" hasData />)).toContain('showing the last incidents it sent')
  })

  it('incident list: empty and filled', () => {
    expect(renderToString(<IncidentList list={[]} />)).toContain('No incidents yet. That is good news.')
    const html = renderToString(<IncidentList list={[{ id: 'inc_1', started_at: TS, reason: 'fast_fall', state: 'resolved',
      simulated: true, acknowledged_by: 'dashboard' }]} />)
    expect(html).toContain('Fall')
    expect(html).toContain('TEST')
    expect(html).toContain('acknowledged by dashboard')
  })

  it('live page says when Guardian is offline', () => {
    const live = { connection: 'disconnected', incident: { id: null, state: 'monitoring' }, activity: null, status: null,
      pose: null, steps: { incidentId: null, list: [] } }
    expect(renderToString(<Live live={live} zones={[]} />)).toContain('Guardian is not answering')
    expect(renderToString(<Live live={{ ...live, connection: 'connected' }} zones={[]} />)).not.toContain('not answering')
  })
})
