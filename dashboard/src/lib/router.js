import { useEffect, useState } from 'react'

/** Pages live in the address hash: #/live, #/incidents, #/incident/<id>, #/today, #/insights, #/settings. */
export function parseHash(hash) {
  const parts = (hash || '').replace(/^#\/?/, '').split('/').filter(Boolean)
  return { page: parts[0] || 'live', id: parts[1] ? decodeURIComponent(parts[1]) : null }
}

export function navigate(page, id) {
  const target = id ? `#/${page}/${encodeURIComponent(id)}` : `#/${page}`
  if (window.location.hash !== target) window.location.hash = target
}

export function useHashRoute() {
  const [route, setRoute] = useState(() => parseHash(window.location.hash))
  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash))
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}
