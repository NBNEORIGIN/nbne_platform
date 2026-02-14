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
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

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
    (e) => !dismissed.has(`${e.event_type}-${e.entity_id}`)
  )
  const isSorted = data.state === 'sorted' || visibleEvents.length === 0

  const handleDismiss = (evt: DashboardEvent) => {
    setDismissed((prev) => new Set(prev).add(`${evt.event_type}-${evt.entity_id}`))
  }

  return (
    <div style={{ maxWidth: 620, margin: '0 auto' }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '0.25rem' }}>
          Today
        </h1>
        <div style={{ fontSize: '0.85rem', color: '#9ca3af' }}>
          {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </div>
      </div>

      {/* ── State line ── */}
      {isSorted ? (
        <div style={{
          padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 10,
          border: '1px solid #e5e7eb', backgroundColor: '#fafafa',
        }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 500, color: '#374151' }}>
            No active issues. Sorted.
          </div>
        </div>
      ) : (
        <>
          <div style={{
            fontSize: '0.95rem', color: '#6b7280', marginBottom: '1.25rem',
          }}>
            {visibleEvents.length} issue{visibleEvents.length !== 1 ? 's' : ''} need{visibleEvents.length === 1 ? 's' : ''} attention.
          </div>

          {/* ── Issue cards ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {visibleEvents.map((evt, i) => {
              const isUrgent = evt.severity === 'critical'
              const primary = evt.actions[0]
              const secondary = evt.actions.slice(1)

              return (
                <div key={`${evt.event_type}-${evt.entity_id}-${i}`} style={{
                  border: isUrgent ? '1px solid #fecaca' : '1px solid #e5e7eb',
                  borderRadius: 10,
                  padding: '1.25rem 1.5rem',
                  backgroundColor: isUrgent ? '#fef2f2' : '#fff',
                }}>
                  {/* Title */}
                  <div style={{
                    fontSize: '0.95rem', fontWeight: 600,
                    color: isUrgent ? '#991b1b' : '#111827',
                    marginBottom: '0.35rem',
                  }}>
                    {evt.summary}
                  </div>

                  {/* Impact */}
                  <div style={{
                    fontSize: '0.85rem', color: '#6b7280',
                    marginBottom: '1rem', lineHeight: 1.4,
                  }}>
                    {evt.detail}
                  </div>

                  {/* Primary action */}
                  {primary && (
                    <div style={{ marginBottom: secondary.length > 0 ? '0.75rem' : 0 }}>
                      <button
                        onClick={() => handleDismiss(evt)}
                        style={{
                          display: 'inline-block',
                          padding: '0.5rem 1.25rem',
                          borderRadius: 6,
                          border: 'none',
                          backgroundColor: isUrgent ? '#dc2626' : '#111827',
                          color: '#fff',
                          fontSize: '0.85rem',
                          fontWeight: 500,
                          cursor: 'pointer',
                        }}
                      >
                        {primary.label}
                      </button>
                      <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.35rem' }}>
                        {primary.reason}
                      </div>
                    </div>
                  )}

                  {/* Secondary actions */}
                  {secondary.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.35rem' }}>
                        Other options:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {secondary.map((action, j) => (
                          <button
                            key={j}
                            onClick={() => handleDismiss(evt)}
                            style={{
                              padding: '0.3rem 0.75rem',
                              borderRadius: 5,
                              border: '1px solid #d1d5db',
                              backgroundColor: '#fff',
                              color: '#374151',
                              fontSize: '0.8rem',
                              cursor: 'pointer',
                            }}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
