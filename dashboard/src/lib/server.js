// The server runs on port 8000 of the same machine that served this page, so the dashboard
// works both on the laptop (localhost) and from a phone on the same Wi-Fi (laptop's IP).
// Outside a browser (tests) it falls back to localhost.
const where = typeof window !== 'undefined' ? window.location : { hostname: 'localhost', protocol: 'http:' }
const host = where.hostname

export const SERVER_HTTP = `${where.protocol}//${host}:8000`
export const DASHBOARD_WS = `${where.protocol === 'https:' ? 'wss' : 'ws'}://${host}:8000/ws/dashboard`
