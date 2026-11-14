import { SERVER_HTTP } from './server.js'

/** GET a JSON resource from the Guardian server; throws on HTTP errors. */
export async function getJSON(path) {
  const response = await fetch(`${SERVER_HTTP}${path}`)
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`)
  return response.json()
}

/** POST JSON to the Guardian server; returns { ok, status, body }. */
export async function postJSON(path, body = {}) {
  const response = await fetch(`${SERVER_HTTP}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }
  return { ok: response.ok, status: response.status, body: data }
}

export const acknowledge = (incidentId) =>
  postJSON(`/incidents/${encodeURIComponent(incidentId)}/ack`, { by: 'dashboard' })
