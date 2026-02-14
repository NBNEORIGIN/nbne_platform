'use client'

import { useEffect, useState } from 'react'
import { getDashboardToday } from '@/lib/api'

interface DashboardAction {
  label: string
  reason: string
  link: string
  rank: number
}

interface DashboardEvent {
  event_type: string
  severity: string
  summary: string
  detail: string
  actions: DashboardAction[]
  entity_type: string
  entity_id: number | null
  timestamp: string
}

interface DashboardData {
  state: 'sorted' | 'active'
  message: string
  events: DashboardEvent[]
  summary: { total: number; critical: number; high: number; warning: number; info: number }
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolving, setResolving] = useState<Record<string, string>>({})
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())
  const [resolved, setResolved] = useState<Array<{ evt: DashboardEvent; action: string }>>([])
  const [view, setView] = useState<'active' | 'sorted'>('active')

  useEffect(() => {
    getDashboardToday().then((res) => {
      if (res.error) {
        setError(res.error)
      } else {
        setData(res.data)
      }
      setLoading(false)
    })
  }, [])

  const evtKey = (evt: DashboardEvent) => `${evt.event_type}-${evt.entity_id}`

  const handleAction = (evt: DashboardEvent, label: string) => {
    const key = evtKey(evt)
    setResolving((prev) => ({ ...prev, [key]: label }))
    setTimeout(() => {
      setDismissed((prev) => new Set(prev).add(key))
      setResolved((prev) => [...prev, { evt, action: label }])
      setResolving((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }, 1500)
  }

  if (loading) return (
    <div style={{ padding: '3rem 0', textAlign: 'center', color: '#9ca3af', fontSize: '0.95rem' }}>
      Loading…
    </div>
  )
  if (error) return (
    <div style={{ padding: '3rem 0', textAlign: 'center', color: '#9ca3af', fontSize: '0.95rem' }}>
      Dashboard unavailable.
    </div>
  )
  if (!data) return null

  const visibleEvents = data.events.filter(
    (e: DashboardEvent) => !dismissed.has(evtKey(e))
  )
  const activeCount = visibleEvents.length
  const allSorted = data.state === 'sorted' || activeCount === 0

  const tog = (on: boolean) => ({
    padding: '0.3rem 0.85rem', borderRadius: 5,
    border: '1px solid #d1d5db',
    backgroundColor: on ? '#111827' : '#fff',
    color: on ? '#fff' : '#6b7280',
    fontSize: '0.8rem', fontWeight: 500 as const, cursor: 'pointer' as const,
  })

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '0.15rem' }}>
            Today
          </h1>
          <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
            {allSorted
              ? 'All sorted. You\u2019re good.'
              : `${activeCount} thing${activeCount !== 1 ? 's' : ''} need${activeCount === 1 ? 's' : ''} sorting.`
            }
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.35rem' }}>
          <button onClick={() => setView('active')} style={tog(view === 'active')}>Active</button>
          <button onClick={() => setView('sorted')} style={tog(view === 'sorted')}>
            Sorted{resolved.length > 0 ? ` (${resolved.length})` : ''}
          </button>
        </div>
      </div>

      {/* ── Sorted view ── */}
      {view === 'sorted' ? (
        resolved.length === 0 ? (
          <div style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8, border: '1px solid #e5e7eb', backgroundColor: '#fafafa' }}>
            <div style={{ fontSize: '0.95rem', color: '#6b7280' }}>Nothing resolved yet today.</div>
          </div>
        ) : (
          <div>
            {resolved.map((r, i: number) => (
              <div key={i} style={{
                padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6',
                display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
              }}>
                <div style={{ fontSize: '0.9rem', color: '#374151' }}>{r.evt.detail}</div>
                <div style={{ fontSize: '0.85rem', color: '#059669', fontWeight: 500, flexShrink: 0, marginLeft: '1rem' }}>{r.action}</div>
              </div>
            ))}
          </div>
        )

      /* ── Active: all clear ── */
      ) : allSorted ? (
        <div style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8, border: '1px solid #e5e7eb', backgroundColor: '#fafafa' }}>
          <div style={{ fontSize: '0.95rem', color: '#374151', fontWeight: 500 }}>All sorted. You're good.</div>
        </div>

      /* ── Active: issue rows ── */
      ) : (
        <div>
          {visibleEvents.map((evt: DashboardEvent, i: number) => {
            const key = evtKey(evt)
            const isResolving = key in resolving
            const primary = evt.actions[0]
            const secondary = evt.actions.slice(1)

            return (
              <div key={`${key}-${i}`} style={{
                padding: '0.85rem 0',
                borderBottom: '1px solid #f0f0f0',
                opacity: isResolving ? 0.5 : 1,
                transition: 'opacity 0.3s ease',
              }}>
                {isResolving ? (
                  <div style={{ fontSize: '0.9rem', color: '#374151' }}>
                    {resolving[key]} — awaiting response.
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1.25rem', flexWrap: 'wrap' }}>

                    {/* Situation */}
                    <div style={{ flex: '1 1 280px', fontSize: '0.9rem', color: '#111827', lineHeight: 1.5 }}>
                      {evt.detail}
                    </div>

                    {/* Primary action + reason */}
                    {primary && (
                      <div style={{ flexShrink: 0 }}>
                        <button
                          onClick={() => handleAction(evt, primary.label)}
                          style={{
                            padding: '0.4rem 1rem', borderRadius: 5, border: 'none',
                            backgroundColor: '#111827', color: '#fff',
                            fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', whiteSpace: 'nowrap',
                          }}
                        >
                          {primary.label}
                        </button>

                        {/* Secondary actions as text links */}
                        {secondary.length > 0 && (
                          <div style={{ marginTop: '0.3rem', display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                            {secondary.map((a: DashboardAction, j: number) => (
                              <span
                                key={j}
                                onClick={() => handleAction(evt, a.label)}
                                style={{
                                  fontSize: '0.78rem', color: '#6b7280', cursor: 'pointer',
                                  textDecoration: 'underline', textUnderlineOffset: '2px',
                                }}
                              >
                                {a.label}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Reason — small right-aligned text */}
                    {primary && (
                      <div style={{ flex: '0 0 auto', fontSize: '0.78rem', color: '#9ca3af', maxWidth: 200, lineHeight: 1.4 }}>
                        {primary.reason}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
