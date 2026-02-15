'use client'

import { useEffect, useState } from 'react'
import { getDashboardToday, logBusinessEvent, getTodayResolved, parseAssistantCommand } from '@/lib/api'

interface DashboardAction {
  label: string
  reason: string
  link: string
  rank: number
  staff_id?: number
}

interface DashboardEvent {
  event_type: string
  severity: string
  summary: string
  detail: string
  why_it_matters?: string
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

interface ResolvedEvent {
  id: number
  event_type: string
  event_type_display: string
  action_label: string
  action_detail: string
  source_event_type: string
  performed_by: string
  created_at: string
}

// Map source event types to BusinessEvent types for logging
const ACTION_EVENT_MAP: Record<string, string> = {
  staff_sick: 'COVER_REQUESTED',
  booking_unassigned: 'BOOKING_ASSIGNED',
  booking_cancelled: 'BOOKING_CANCELLED',
  deposit_missing: 'PAYMENT_REQUESTED',
  leave_pending: 'LEAVE_APPROVED',
  compliance_expiry: 'COMPLIANCE_COMPLETED',
  incident_open: 'INCIDENT_RESOLVED',
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolving, setResolving] = useState<Record<string, string>>({})
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())
  const [resolvedEvents, setResolvedEvents] = useState<ResolvedEvent[]>([])
  const [view, setView] = useState<'active' | 'sorted'>('active')

  // Command bar state
  const [cmdText, setCmdText] = useState('')
  const [cmdResult, setCmdResult] = useState<any>(null)
  const [cmdLoading, setCmdLoading] = useState(false)

  useEffect(() => {
    Promise.all([
      getDashboardToday(),
      getTodayResolved(),
    ]).then(([dashRes, resolvedRes]) => {
      if (dashRes.error) {
        setError(dashRes.error)
      } else {
        setData(dashRes.data)
      }
      if (!resolvedRes.error && resolvedRes.data) {
        setResolvedEvents(resolvedRes.data.events || [])
      }
      setLoading(false)
    })
  }, [])

  const evtKey = (evt: DashboardEvent) => `${evt.event_type}-${evt.entity_id}`

  const handleAction = async (evt: DashboardEvent, action: DashboardAction) => {
    const key = evtKey(evt)
    setResolving((prev: Record<string, string>) => ({ ...prev, [key]: action.label }))

    // Log the business event (no silent mutation)
    const eventType = ACTION_EVENT_MAP[evt.event_type] || 'OWNER_OVERRIDE'
    await logBusinessEvent({
      event_type: eventType,
      action_label: action.label,
      source_event_type: evt.event_type,
      source_entity_type: evt.entity_type,
      source_entity_id: evt.entity_id,
      action_detail: action.reason,
      payload: action.staff_id ? { cover_staff_id: action.staff_id } : {},
    })

    setTimeout(async () => {
      setDismissed((prev: Set<string>) => new Set(prev).add(key))
      setResolving((prev: Record<string, string>) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
      // Refresh resolved events from backend
      const res = await getTodayResolved()
      if (!res.error && res.data) {
        setResolvedEvents(res.data.events || [])
      }
    }, 1500)
  }

  const handleCommand = async () => {
    if (!cmdText.trim()) return
    setCmdLoading(true)
    setCmdResult(null)
    const res = await parseAssistantCommand(cmdText)
    setCmdLoading(false)
    if (!res.error && res.data) {
      setCmdResult(res.data)
    } else {
      setCmdResult({ parsed: false, message: 'Could not process command.' })
    }
  }

  const handleCommandConfirm = async () => {
    if (!cmdResult?.intent) return
    const intent = cmdResult.intent
    await logBusinessEvent({
      event_type: intent.event_type,
      action_label: intent.original_text,
      action_detail: intent.description,
      payload: { ...intent.entities, source: 'assistant_command' },
    })
    setCmdResult(null)
    setCmdText('')
    // Refresh
    const res = await getTodayResolved()
    if (!res.error && res.data) {
      setResolvedEvents(res.data.events || [])
    }
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

  const visibleEvents = data.events
    .filter((e: DashboardEvent) => !dismissed.has(evtKey(e)))
    .slice(0, 5)
  const activeCount = visibleEvents.length
  const allSorted = data.state === 'sorted' || activeCount === 0
  const sortedCount = resolvedEvents.length

  const tog = (on: boolean) => ({
    padding: '0.3rem 0.85rem', borderRadius: 5,
    border: '1px solid #d1d5db',
    backgroundColor: on ? '#111827' : '#fff',
    color: on ? '#fff' : '#6b7280',
    fontSize: '0.8rem', fontWeight: 500 as const, cursor: 'pointer' as const,
  })

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>

      {/* ── Global Command Bar ── */}
      <div style={{
        display: 'flex', gap: '0.5rem', marginBottom: '1.5rem',
        padding: '0.6rem 0.75rem', borderRadius: 8,
        border: '1px solid #e5e7eb', backgroundColor: '#fff',
      }}>
        <input
          type="text"
          value={cmdText}
          onChange={(e: any) => setCmdText(e.target.value)}
          onKeyDown={(e: any) => e.key === 'Enter' && handleCommand()}
          placeholder="Type what happened or what you want to do…"
          style={{
            flex: 1, border: 'none', outline: 'none', fontSize: '0.9rem',
            color: '#111827', backgroundColor: 'transparent',
          }}
        />
        <button
          onClick={handleCommand}
          disabled={cmdLoading || !cmdText.trim()}
          style={{
            padding: '0.35rem 0.75rem', borderRadius: 5, border: 'none',
            backgroundColor: '#111827', color: '#fff',
            fontSize: '0.8rem', fontWeight: 500, cursor: 'pointer',
            opacity: cmdLoading || !cmdText.trim() ? 0.4 : 1,
          }}
        >
          {cmdLoading ? '…' : 'Go'}
        </button>
      </div>

      {/* Command result / confirmation */}
      {cmdResult && (
        <div style={{
          marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: 8,
          border: '1px solid #e5e7eb', backgroundColor: '#fafafa',
        }}>
          {cmdResult.parsed ? (
            <div>
              <div style={{ fontSize: '0.9rem', color: '#111827', marginBottom: '0.5rem' }}>
                {cmdResult.confirmation_message}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={handleCommandConfirm}
                  style={{
                    padding: '0.35rem 0.85rem', borderRadius: 5, border: 'none',
                    backgroundColor: '#111827', color: '#fff',
                    fontSize: '0.8rem', fontWeight: 500, cursor: 'pointer',
                  }}
                >
                  Confirm
                </button>
                <button
                  onClick={() => { setCmdResult(null); setCmdText('') }}
                  style={{
                    padding: '0.35rem 0.85rem', borderRadius: 5,
                    border: '1px solid #d1d5db', backgroundColor: '#fff', color: '#6b7280',
                    fontSize: '0.8rem', cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{cmdResult.message}</div>
          )}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
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
            Sorted{sortedCount > 0 ? ` (${sortedCount})` : ''}
          </button>
        </div>
      </div>

      {/* ── Sorted view: from backend BusinessEvent log ── */}
      {view === 'sorted' ? (
        sortedCount === 0 ? (
          <div style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8, border: '1px solid #e5e7eb', backgroundColor: '#fafafa' }}>
            <div style={{ fontSize: '0.95rem', color: '#6b7280' }}>Nothing resolved yet today.</div>
          </div>
        ) : (
          <div>
            {/* Column headers */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 140px 100px 80px', gap: '0.75rem',
              padding: '0 0 0.4rem 0', borderBottom: '1px solid #e5e7eb', marginBottom: 0,
            }}>
              {['Action taken', 'Who', 'Type', 'Time'].map((h: string) => (
                <div key={h} style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</div>
              ))}
            </div>
            {resolvedEvents.map((r: ResolvedEvent) => {
              const time = new Date(r.created_at)
              return (
                <div key={r.id} style={{
                  display: 'grid', gridTemplateColumns: '1fr 140px 100px 80px', gap: '0.75rem',
                  padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6', alignItems: 'baseline',
                }}>
                  <div style={{ fontSize: '0.88rem', color: '#059669', fontWeight: 500 }}>{r.action_label}</div>
                  <div style={{ fontSize: '0.82rem', color: '#6b7280' }}>{r.performed_by}</div>
                  <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{r.event_type_display}</div>
                  <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{time.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
              )
            })}
          </div>
        )

      /* ── Active: all clear ── */
      ) : allSorted ? (
        <div style={{ padding: '3rem 1.5rem', textAlign: 'center', borderRadius: 8, border: '1px solid #e5e7eb', backgroundColor: '#fafafa' }}>
          <div style={{ fontSize: '0.95rem', color: '#374151', fontWeight: 500 }}>All sorted. You&rsquo;re good.</div>
        </div>

      /* ── Active: 4-column horizontal rows ── */
      ) : (
        <div>
          {/* Column headers */}
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 1.2fr 1fr 1fr', gap: '0.75rem',
            padding: '0 0 0.4rem 0', borderBottom: '1px solid #e5e7eb', marginBottom: 0,
          }}>
            {['What happened', 'Why it matters', 'Action', 'Options'].map((h: string) => (
              <div key={h} style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</div>
            ))}
          </div>

          {/* Issue rows */}
          {visibleEvents.map((evt: DashboardEvent, i: number) => {
            const key = evtKey(evt)
            const isResolving = key in resolving
            const primary = evt.actions[0]
            const secondary = evt.actions.slice(1)

            return (
              <div
                key={`${key}-${i}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '2fr 1.2fr 1fr 1fr',
                  gap: '0.75rem',
                  padding: '0.65rem 0',
                  borderBottom: '1px solid #f3f4f6',
                  alignItems: 'flex-start',
                  opacity: isResolving ? 0.4 : 1,
                  transition: 'opacity 0.3s ease',
                }}
              >
                {isResolving ? (
                  <div style={{ gridColumn: '1 / -1', fontSize: '0.88rem', color: '#374151' }}>
                    {resolving[key]} — awaiting response.
                  </div>
                ) : (
                  <>
                    {/* Col 1 — What happened */}
                    <div style={{ fontSize: '0.88rem', color: '#111827', lineHeight: 1.45 }}>
                      {evt.detail}
                    </div>

                    {/* Col 2 — Why it matters */}
                    <div style={{ fontSize: '0.82rem', color: '#6b7280', lineHeight: 1.4 }}>
                      {evt.why_it_matters || primary?.reason || ''}
                    </div>

                    {/* Col 3 — Primary action */}
                    <div>
                      {primary && (
                        <button
                          onClick={() => handleAction(evt, primary)}
                          style={{
                            padding: '0.35rem 0.75rem', borderRadius: 5, border: 'none',
                            backgroundColor: '#111827', color: '#fff',
                            fontSize: '0.82rem', fontWeight: 500, cursor: 'pointer',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {primary.label}
                        </button>
                      )}
                    </div>

                    {/* Col 4 — Secondary options */}
                    <div style={{ display: 'flex', flexDirection: 'column' as const, gap: '0.2rem' }}>
                      {secondary.map((a: DashboardAction, j: number) => (
                        <span
                          key={j}
                          onClick={() => handleAction(evt, a)}
                          style={{
                            fontSize: '0.78rem', color: '#6b7280', cursor: 'pointer',
                            textDecoration: 'underline', textUnderlineOffset: '2px',
                          }}
                        >
                          {a.label}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
