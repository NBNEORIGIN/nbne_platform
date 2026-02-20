'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import { getGymTimetable, createBooking, setDemoTenant } from '@/lib/api'

const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_CREAM = '#FAF8F5'
const BG_WARM = '#F5F0EB'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function GymBookingFlow() {
  const tenant = useTenant()
  const searchParams = useSearchParams()
  const demoSlug = searchParams.get('demo') || ''
  const accent = tenant.colour_primary || '#dc2626'
  const accentLight = accent + '80'
  const bizName = tenant.business_name || 'Gym'

  const [step, setStep] = useState(1) // 1=browse, 2=details, 3=confirmed
  const [timetable, setTimetable] = useState<any>(null)
  const [selectedSession, setSelectedSession] = useState<any>(null)
  const [weekOffset, setWeekOffset] = useState(0)
  const [filterDay, setFilterDay] = useState<number | null>(null)
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState<any>(null)

  useEffect(() => {
    if (demoSlug) setDemoTenant(demoSlug)
  }, [demoSlug])

  // Fetch timetable
  useEffect(() => {
    setLoading(true)
    const today = new Date()
    const targetDate = new Date(today)
    targetDate.setDate(today.getDate() + weekOffset * 7)
    const dateStr = targetDate.toISOString().split('T')[0]
    getGymTimetable(dateStr).then(res => {
      setTimetable(res.data)
      setLoading(false)
    })
  }, [weekOffset])

  const sessions = timetable?.sessions || []
  const categories = Array.from(new Set(sessions.map((s: any) => s.class_type?.category).filter(Boolean))) as string[]

  const filtered = sessions.filter((s: any) => {
    if (filterDay !== null && s.day_of_week !== filterDay) return false
    if (filterCategory && s.class_type?.category !== filterCategory) return false
    return true
  })

  async function handleSubmit() {
    if (!name || !email || !phone) {
      setError('Please fill in all required fields')
      return
    }
    setSubmitting(true)
    setError('')

    const bookingData = {
      client_name: name,
      client_email: email,
      client_phone: phone,
      notes: `Class: ${selectedSession.class_type.name}. ${selectedSession.date} ${selectedSession.start_time}. ${notes}`,
      date: selectedSession.date,
      start_time: selectedSession.start_time,
    }

    const res = await createBooking(bookingData)
    setSubmitting(false)
    if (res.error) {
      setError(res.error)
    } else {
      setConfirmed(res.data)
      setStep(3)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: BG_CREAM, fontFamily: SANS }}>
      {/* Header */}
      <header style={{ background: accent, color: '#fff', padding: '1.5rem 1rem', textAlign: 'center' }}>
        <h1 style={{ fontFamily: SERIF, fontSize: '1.5rem', fontWeight: 500, margin: 0 }}>{bizName}</h1>
        <p style={{ fontSize: '0.85rem', opacity: 0.85, margin: '0.25rem 0 0' }}>Class Timetable & Booking</p>
      </header>

      <main style={{ maxWidth: 640, margin: '0 auto', padding: '1.5rem 1rem' }}>
        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', color: '#dc2626', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        {step === 3 && confirmed ? (
          <div style={{ background: '#fff', borderRadius: 10, padding: '2rem', textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>✓</div>
            <h2 style={{ fontFamily: SERIF, fontSize: '1.3rem', color: DARK, marginBottom: '0.5rem' }}>Booking Confirmed</h2>
            <p style={{ color: MUTED, fontSize: '0.9rem' }}>
              {selectedSession.class_type.name} — {selectedSession.day_of_week_display} {selectedSession.start_time}
            </p>
            <p style={{ color: MUTED, fontSize: '0.85rem', marginTop: '0.5rem' }}>
              A confirmation will be sent to {email}
            </p>
          </div>
        ) : step === 2 && selectedSession ? (
          /* Step 2: Your Details */
          <div>
            {/* Session summary */}
            <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', border: '1px solid rgba(0,0,0,0.06)' }}>
              <button onClick={() => { setStep(1); setSelectedSession(null) }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: accent, fontSize: '0.85rem', marginBottom: '0.75rem', padding: 0 }}>
                ← Back to timetable
              </button>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                {selectedSession.class_type.colour && (
                  <div style={{ width: 4, height: 48, borderRadius: 2, background: selectedSession.class_type.colour, flexShrink: 0 }} />
                )}
                <div>
                  <h3 style={{ fontFamily: SERIF, fontSize: '1.1rem', color: DARK, margin: 0 }}>{selectedSession.class_type.name}</h3>
                  <p style={{ color: MUTED, fontSize: '0.85rem', margin: '0.2rem 0 0' }}>
                    {selectedSession.day_of_week_display} · {selectedSession.start_time} – {selectedSession.end_time}
                    {selectedSession.room && ` · ${selectedSession.room}`}
                  </p>
                  {selectedSession.instructor && (
                    <p style={{ color: MUTED, fontSize: '0.82rem', margin: '0.15rem 0 0' }}>
                      with {selectedSession.instructor.name}
                    </p>
                  )}
                  <p style={{ fontSize: '0.8rem', color: selectedSession.spots_remaining <= 3 ? '#dc2626' : '#059669', margin: '0.25rem 0 0', fontWeight: 600 }}>
                    {selectedSession.spots_remaining} spot{selectedSession.spots_remaining !== 1 ? 's' : ''} remaining
                  </p>
                </div>
              </div>
            </div>

            {/* Details form */}
            <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', border: '1px solid rgba(0,0,0,0.06)' }}>
              <h2 style={{ fontFamily: SERIF, fontSize: '1.05rem', fontWeight: 500, color: DARK, marginBottom: '0.85rem' }}>Your Details</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <input placeholder="Full Name *" value={name} onChange={e => setName(e.target.value)}
                  style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS }} />
                <input placeholder="Email *" type="email" value={email} onChange={e => setEmail(e.target.value)}
                  style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS }} />
                <input placeholder="Phone *" type="tel" value={phone} onChange={e => setPhone(e.target.value)}
                  style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS }} />
                <textarea placeholder="Any notes or requirements" value={notes} onChange={e => setNotes(e.target.value)} rows={2}
                  style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS, resize: 'vertical' }} />
              </div>

              {selectedSession.class_type.price_pence > 0 && (
                <div style={{ background: BG_WARM, borderRadius: 8, padding: '0.75rem 1rem', marginTop: '1rem', fontSize: '0.85rem', color: DARK }}>
                  Price: <strong>£{(selectedSession.class_type.price_pence / 100).toFixed(2)}</strong>
                </div>
              )}

              <button onClick={handleSubmit} disabled={submitting}
                style={{
                  width: '100%', marginTop: '1rem', padding: '0.85rem', borderRadius: 8,
                  background: accent, color: '#fff', border: 'none', cursor: submitting ? 'wait' : 'pointer',
                  fontWeight: 600, fontSize: '0.95rem', fontFamily: SANS, opacity: submitting ? 0.7 : 1,
                }}
              >{submitting ? 'Booking...' : 'Book Class'}</button>
            </div>
          </div>
        ) : (
          /* Step 1: Browse Timetable */
          <div>
            {/* Week navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <button onClick={() => setWeekOffset(Math.max(0, weekOffset - 1))} disabled={weekOffset === 0}
                style={{ background: 'none', border: 'none', cursor: weekOffset === 0 ? 'default' : 'pointer', fontSize: '1.1rem', color: weekOffset === 0 ? '#d1d5db' : MUTED }}>&lsaquo; Prev</button>
              <span style={{ fontFamily: SERIF, fontWeight: 500, fontSize: '0.9rem', color: DARK }}>
                {timetable ? `${timetable.week_start} — ${timetable.week_end}` : 'This Week'}
              </span>
              <button onClick={() => setWeekOffset(weekOffset + 1)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: MUTED }}>Next &rsaquo;</button>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <button onClick={() => setFilterDay(null)}
                style={{ padding: '0.4rem 0.7rem', borderRadius: 20, border: `1px solid ${filterDay === null ? accent : '#e5e7eb'}`, background: filterDay === null ? accent : '#fff', color: filterDay === null ? '#fff' : DARK, cursor: 'pointer', fontSize: '0.78rem', fontWeight: 500 }}>
                All Days
              </button>
              {DAYS.map((d, i) => (
                <button key={i} onClick={() => setFilterDay(filterDay === i ? null : i)}
                  style={{ padding: '0.4rem 0.7rem', borderRadius: 20, border: `1px solid ${filterDay === i ? accent : '#e5e7eb'}`, background: filterDay === i ? accent : '#fff', color: filterDay === i ? '#fff' : DARK, cursor: 'pointer', fontSize: '0.78rem', fontWeight: 500 }}>
                  {d.slice(0, 3)}
                </button>
              ))}
            </div>
            {categories.length > 1 && (
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                <button onClick={() => setFilterCategory('')}
                  style={{ padding: '0.4rem 0.7rem', borderRadius: 20, border: `1px solid ${!filterCategory ? accent : '#e5e7eb'}`, background: !filterCategory ? accent : '#fff', color: !filterCategory ? '#fff' : DARK, cursor: 'pointer', fontSize: '0.78rem', fontWeight: 500 }}>
                  All
                </button>
                {categories.map(c => (
                  <button key={c} onClick={() => setFilterCategory(filterCategory === c ? '' : c)}
                    style={{ padding: '0.4rem 0.7rem', borderRadius: 20, border: `1px solid ${filterCategory === c ? accent : '#e5e7eb'}`, background: filterCategory === c ? accent : '#fff', color: filterCategory === c ? '#fff' : DARK, cursor: 'pointer', fontSize: '0.78rem', fontWeight: 500 }}>
                    {c}
                  </button>
                ))}
              </div>
            )}

            {/* Sessions list */}
            {loading ? (
              <p style={{ color: MUTED, textAlign: 'center', padding: '2rem 0' }}>Loading timetable...</p>
            ) : filtered.length === 0 ? (
              <p style={{ color: MUTED, textAlign: 'center', padding: '2rem 0' }}>No classes found</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {filtered.map((s: any) => (
                  <button key={s.id} onClick={() => { if (!s.is_full) { setSelectedSession(s); setStep(2) } }} disabled={s.is_full}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.85rem 1rem',
                      background: '#fff', borderRadius: 8, border: '1px solid rgba(0,0,0,0.06)',
                      cursor: s.is_full ? 'default' : 'pointer', textAlign: 'left', width: '100%',
                      opacity: s.is_full ? 0.5 : 1, transition: 'all 0.15s ease',
                    }}
                  >
                    {s.class_type.colour && (
                      <div style={{ width: 4, height: 40, borderRadius: 2, background: s.class_type.colour, flexShrink: 0 }} />
                    )}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: DARK }}>{s.class_type.name}</span>
                        <span style={{ fontSize: '0.75rem', color: MUTED }}>{s.day_of_week_display}</span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: MUTED, marginTop: '0.15rem' }}>
                        {s.start_time} – {s.end_time}
                        {s.room && ` · ${s.room}`}
                        {s.instructor && ` · ${s.instructor.name}`}
                      </div>
                      <div style={{ fontSize: '0.75rem', marginTop: '0.2rem', color: s.is_full ? '#dc2626' : s.spots_remaining <= 3 ? '#f59e0b' : '#059669', fontWeight: 600 }}>
                        {s.is_full ? 'FULL' : `${s.spots_remaining} spots left`}
                      </div>
                    </div>
                    {s.class_type.price_pence > 0 && (
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: DARK, flexShrink: 0 }}>
                        £{(s.class_type.price_pence / 100).toFixed(2)}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div style={{ textAlign: 'center', padding: '2rem 0 0.5rem', fontSize: '0.72rem', color: accentLight, letterSpacing: '0.03em' }}>
          Powered by NBNE
        </div>
      </main>
    </div>
  )
}
