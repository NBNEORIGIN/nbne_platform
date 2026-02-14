'use client'

import { useEffect, useState } from 'react'
import { getDashboardToday } from '@/lib/api'

// Severity badge styles
const SEV_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: '#dc2626', text: '#fff', label: 'Critical' },
  high:     { bg: '#ea580c', text: '#fff', label: 'High' },
  warning:  { bg: '#d97706', text: '#fff', label: 'Warning' },
  info:     { bg: '#2563eb', text: '#fff', label: 'Info' },
}

function SeverityBadge({ severity }: { severity: string }) {
  const s = SEV_STYLES[severity] || SEV_STYLES.info
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 4,
      fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.02em',
      backgroundColor: s.bg, color: s.text,
    }}>
      {s.label}
    </span>
  )
}

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

  if (loading) return <div className="empty-state">Loading…</div>
  if (error) return <div className="empty-state">Dashboard unavailable: {error}</div>
  if (!data) return <div className="empty-state">No data</div>

  const { state, message, events, summary } = data

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <h1>Today</h1>
        <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted, #666)' }}>
          {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </span>
      </div>

      {/* State banner */}
      {state === 'sorted' ? (
        <div style={{
          padding: '2rem', textAlign: 'center', borderRadius: 8,
          border: '1px solid #d1d5db', backgroundColor: '#f9fafb',
          marginBottom: '1.5rem',
        }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#374151' }}>
            {message}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: '0.5rem' }}>
            All issues resolved. Sorted.
          </div>
        </div>
      ) : (
        <>
          {/* Summary counters */}
          <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="stat-card">
              <div className="stat-number">{summary.total}</div>
              <div className="stat-label">Issues</div>
            </div>
            {summary.critical > 0 && (
              <div className="stat-card" style={{ borderLeft: '3px solid #dc2626' }}>
                <div className="stat-number" style={{ color: '#dc2626' }}>{summary.critical}</div>
                <div className="stat-label">Critical</div>
              </div>
            )}
            {summary.high > 0 && (
              <div className="stat-card" style={{ borderLeft: '3px solid #ea580c' }}>
                <div className="stat-number" style={{ color: '#ea580c' }}>{summary.high}</div>
                <div className="stat-label">High</div>
              </div>
            )}
            {(summary.warning + summary.info) > 0 && (
              <div className="stat-card">
                <div className="stat-number">{summary.warning + summary.info}</div>
                <div className="stat-label">Other</div>
              </div>
            )}
          </div>

          {/* Event list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {events.map((evt, i) => (
              <div key={`${evt.event_type}-${evt.entity_id}-${i}`} style={{
                border: '1px solid #e5e7eb', borderRadius: 8,
                padding: '1rem 1.25rem', backgroundColor: '#fff',
                borderLeft: `4px solid ${SEV_STYLES[evt.severity]?.bg || '#2563eb'}`,
              }}>
                {/* Event header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <SeverityBadge severity={evt.severity} />
                  <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{evt.summary}</span>
                </div>

                {/* Detail */}
                <div style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '0.75rem' }}>
                  {evt.detail}
                </div>

                {/* Actions — ranked, deterministic */}
                {evt.actions.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {evt.actions.map((action, j) => (
                      <div key={j} style={{
                        display: 'flex', alignItems: 'baseline', gap: '0.5rem',
                        fontSize: '0.85rem',
                      }}>
                        <span style={{
                          display: 'inline-block', width: 20, height: 20, lineHeight: '20px',
                          textAlign: 'center', borderRadius: '50%', fontSize: '0.7rem',
                          backgroundColor: '#f3f4f6', color: '#374151', fontWeight: 600, flexShrink: 0,
                        }}>
                          {action.rank}
                        </span>
                        <span style={{ fontWeight: 500 }}>{action.label}</span>
                        <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>— {action.reason}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
