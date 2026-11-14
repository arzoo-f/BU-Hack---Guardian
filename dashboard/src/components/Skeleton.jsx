import { useEffect, useRef } from 'react'

// MediaPipe's 33-point pose skeleton (same as the room agent and the alert picture).
const CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 7], [0, 4], [4, 5], [5, 6], [6, 8], [9, 10],
  [11, 12], [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], [17, 19],
  [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], [18, 20], [11, 23],
  [12, 24], [23, 24], [23, 25], [24, 26], [25, 27], [26, 28], [27, 29],
  [28, 30], [29, 31], [30, 32], [27, 31], [28, 32],
]
const W = 640
const H = 480
const MIN_VISIBILITY = 0.3
const STALE_MS = 3000

/** The live skeleton on a plain background, with the safe zones. Never a camera image. */
export default function Skeleton({ pose, zones = [], tone = 'ok' }) {
  const canvas = useRef(null)
  const stale = !pose || Date.now() - pose.receivedAt > STALE_MS

  useEffect(() => {
    const ctx = canvas.current?.getContext('2d')
    if (!ctx) return
    ctx.fillStyle = '#0f172a'
    ctx.fillRect(0, 0, W, H)
    for (const zone of zones) {
      ctx.beginPath()
      zone.polygon.forEach(([x, y], i) => (i ? ctx.lineTo(x * W, y * H) : ctx.moveTo(x * W, y * H)))
      ctx.closePath()
      ctx.fillStyle = 'rgba(56, 189, 248, 0.15)'
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.8)'
      ctx.lineWidth = 2
      ctx.fill()
      ctx.stroke()
      ctx.fillStyle = 'rgba(125, 211, 252, 0.9)'
      ctx.font = '16px system-ui, sans-serif'
      ctx.fillText(`${zone.name} (safe zone)`, zone.polygon[0][0] * W + 6, zone.polygon[0][1] * H + 20)
    }
    if (!pose?.keypoints) return
    const pts = pose.keypoints.map(([x, y, v]) => [x * W, y * H, v])
    const bone = tone === 'alert' ? '#fca5a5' : tone === 'checking' ? '#fcd34d' : '#e2e8f0'
    ctx.globalAlpha = stale ? 0.3 : 1
    ctx.strokeStyle = bone
    ctx.lineWidth = 5
    ctx.lineCap = 'round'
    for (const [a, b] of CONNECTIONS) {
      if (pts[a][2] >= MIN_VISIBILITY && pts[b][2] >= MIN_VISIBILITY) {
        ctx.beginPath()
        ctx.moveTo(pts[a][0], pts[a][1])
        ctx.lineTo(pts[b][0], pts[b][1])
        ctx.stroke()
      }
    }
    ctx.fillStyle = '#fb923c'
    for (const [x, y, v] of pts) {
      if (v >= MIN_VISIBILITY) {
        ctx.beginPath()
        ctx.arc(x, y, 5, 0, Math.PI * 2)
        ctx.fill()
      }
    }
    ctx.globalAlpha = 1
  }, [pose, zones, tone, stale])

  return (
    <div className="relative overflow-hidden rounded-2xl bg-slate-900">
      <canvas ref={canvas} width={W} height={H} className="block h-auto w-full" aria-label="Live skeleton" />
      {stale && (
        <p className="absolute inset-x-0 bottom-3 text-center text-sm text-slate-400">
          {pose ? 'No person in view right now' : 'Waiting for the camera...'}
        </p>
      )}
      <p className="absolute right-3 top-2 text-xs text-slate-500">skeleton only - no video leaves the room</p>
    </div>
  )
}
