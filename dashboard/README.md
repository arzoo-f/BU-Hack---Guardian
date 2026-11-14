# dashboard

React + Vite + Tailwind (+ Recharts for the charts in Stage 7). Shows live status, the skeleton,
incidents with every step and its reason, and the activity data. It never receives video: only
keypoints, labels and events.

Run (from this folder):

```
npm install        # first time only
npm run dev -- --host
npm test           # wording, routing and every component rendered with sample data
```

Open http://localhost:5173 on the laptop, or http://LAPTOP-IP:5173 from a phone on the same
Wi-Fi. The server address is taken from the page address (`src/lib/server.js`), port 8000.

Pages (in the address hash): `#/live`, `#/incidents`, `#/incident/<id>`, `#/settings`.
**Demo mode** (`?demo=1`, or the header button): follows an open incident by itself and returns to
Live 8 s after it ends, so nobody clicks during the recording. **Sound** must be switched on once
with the header button (browsers block sound until a click); alerts then beep.

| File | Purpose |
| --- | --- |
| `src/App.jsx` | header, navigation, demo mode, alarm sound |
| `src/pages/Live.jsx` | status card, alert panel, live incident steps, skeleton |
| `src/pages/Incidents.jsx`, `IncidentDetail.jsx` | incident list; one incident step by step |
| `src/pages/Settings.jsx` | contacts and sensitivity (read-only), "Simulate a fall" |
| `src/components/` | `Skeleton` (canvas + safe zones), `StatusCard`, `Steps`, `AlertPanel` |
| `src/lib/useGuardianSocket.js` | live WebSocket to `/ws/dashboard`, reconnects by itself |
| `src/lib/labels.js` | plain-English wording for activities, states and incident steps |
| `src/lib/api.js`, `router.js`, `server.js` | REST calls, hash routing, server address |
