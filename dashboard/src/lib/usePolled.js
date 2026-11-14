import { useEffect, useState } from 'react'
import { getJSON } from './api.js'

/**
 * GET a resource now and every `everyMs`, and again whenever `key` changes (pass the connection state,
 * so the page reloads as soon as Guardian is back). Keeps the last good data when a refresh fails.
 * A null path fetches nothing.
 */
export function usePolled(path, everyMs, key) {
  const [state, setState] = useState({ data: null, error: null })
  useEffect(() => {
    if (!path) return undefined
    let alive = true
    const load = () =>
      getJSON(path).then(
        (data) => alive && setState({ data, error: null }),
        (e) => alive && setState((s) => ({ data: s.data, error: e.message })),
      )
    load()
    const timer = setInterval(load, everyMs)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [path, everyMs, key])
  return state
}
