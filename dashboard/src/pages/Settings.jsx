import { useState } from 'react'
import { Loading, Offline } from '../components/LoadState.jsx'
import { postJSON } from '../lib/api.js'
import { usePolled } from '../lib/usePolled.js'

function Row({ label, children }) {
  return (
    <div className="flex flex-wrap justify-between gap-2 py-2">
      <dt className="text-slate-600">{label}</dt>
      <dd className="font-medium text-slate-900">{children}</dd>
    </div>
  )
}

/** Read-only settings (editing is optional in the plan) and a "Simulate fall" button for rehearsals. */
export default function Settings({ connection }) {
  const loaded = usePolled('/settings', 60000, connection)
  const contactList = usePolled('/contacts', 60000, connection)
  const zoneList = usePolled('/zones', 60000, connection)
  const [simulated, setSimulated] = useState(null)
  const settings = loaded.data
  const contacts = contactList.data?.contacts ?? []
  const zones = zoneList.data?.zones ?? []
  const error = loaded.error || contactList.error || zoneList.error

  const simulate = async () => {
    const result = await postJSON('/simulate/fall').catch(() => ({ ok: false }))
    setSimulated(result.ok ? `Simulated fall started (${result.body.incident_id}).` : 'Could not reach Guardian.')
  }

  if (!settings) return error ? <Offline what="settings" error={error} hasData={false} /> : <Loading what="the settings" />
  const c = settings.check_in
  const f = settings.fall_detection
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {error && <div className="lg:col-span-2"><Offline what="settings" error={error} hasData /></div>}
      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-2 text-lg font-bold text-slate-900">Who is told</h2>
        <dl className="divide-y divide-slate-100">
          <Row label="Family alerts">{settings.alerts.telegram ? 'Telegram test group' : 'server log only (no Telegram)'}</Row>
          {contacts.map((contact) => (
            <Row key={contact.name} label={contact.relation || 'contact'}>{contact.name}</Row>
          ))}
          <Row label="Check-in decisions">{settings.alerts.ai === 'OpenAIAgent' ? 'AI (OpenAI) + safety rules' : 'test AI + safety rules'}</Row>
        </dl>
      </section>
      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-2 text-lg font-bold text-slate-900">How sensitive</h2>
        <dl className="divide-y divide-slate-100">
          <Row label="A fall is confirmed after">{f.confirm_after_s} s on the floor</Row>
          <Row label="Lying still on the floor alerts after">{f.found_on_floor_after_s} s</Row>
          <Row label="Still on the floor after a fall: alert after">{c.floor_rule_s} s, whatever was said</Row>
          <Row label="Listening after each question">{c.first_listen_s} s, then {c.second_listen_s} s</Row>
          <Row label="Reminders until someone acknowledges">every {c.realert_every_s / 60} min</Row>
          <Row label="Words that alert at once">{c.help_keywords.join(', ')}</Row>
          <Row label="Safe zones">{zones.map((z) => z.name).join(', ') || 'none'}</Row>
        </dl>
      </section>
      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 lg:col-span-2">
        <h2 className="text-lg font-bold text-slate-900">Rehearsal</h2>
        <p className="mt-1 text-slate-600">Starts a simulated incident, marked TEST, without anyone falling.</p>
        <button type="button" onClick={simulate}
          className="mt-3 rounded-xl bg-slate-800 px-5 py-3 font-semibold text-white hover:bg-slate-900">
          Simulate a fall
        </button>
        {simulated && <p className="mt-2 text-slate-700">{simulated}</p>}
      </section>
    </div>
  )
}
