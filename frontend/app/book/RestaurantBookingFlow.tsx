'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import { getRestaurantAvailability, getRestaurantAvailableDates, createBooking, setDemoTenant } from '@/lib/api'

const SERIF = "'Playfair Display', Georgia, serif"
const SANS = "'Inter', -apple-system, sans-serif"
const DARK = '#1a1a1a'
const MUTED = '#6b6b6b'
const BG_CREAM = '#FAF8F5'
const BG_WARM = '#F5F0EB'

function formatTime(t: string) { return t }

export default function RestaurantBookingFlow() {
  const tenant = useTenant()
  const searchParams = useSearchParams()
  const demoSlug = searchParams.get('demo') || ''
  const accent = tenant.colour_primary || '#059669'
  const accentLight = accent + '80'
  const bizName = tenant.business_name || 'Restaurant'

  const [step, setStep] = useState(1) // 1=party, 2=date, 3=time, 4=details, 5=confirmed
  const [partySize, setPartySize] = useState(2)
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [selectedDate, setSelectedDate] = useState('')
  const [windows, setWindows] = useState<any[]>([])
  const [selectedSlot, setSelectedSlot] = useState<any>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState<any>(null)

  useEffect(() => {
    if (demoSlug) setDemoTenant(demoSlug)
  }, [demoSlug])

  // Fetch available dates when party size changes
  useEffect(() => {
    if (step >= 2) {
      setLoading(true)
      getRestaurantAvailableDates(partySize).then(res => {
        setAvailableDates(res.data?.dates || [])
        setLoading(false)
      })
    }
  }, [partySize, step])

  // Fetch time slots when date selected
  useEffect(() => {
    if (selectedDate) {
      setLoading(true)
      getRestaurantAvailability(selectedDate, partySize).then(res => {
        setWindows(res.data?.windows || [])
        setLoading(false)
      })
    }
  }, [selectedDate, partySize])

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
      notes: `Party of ${partySize}. ${selectedSlot?.start_time || ''} - ${selectedSlot?.end_time || ''}. ${notes}`,
      date: selectedDate,
      start_time: selectedSlot?.start_time,
      party_size: partySize,
    }

    const res = await createBooking(bookingData)
    setSubmitting(false)
    if (res.error) {
      setError(res.error)
    } else {
      setConfirmed(res.data)
      setStep(5)
    }
  }

  // Calendar component (inline)
  function Calendar() {
    const today = new Date()
    const [viewYear, setViewYear] = useState(today.getFullYear())
    const [viewMonth, setViewMonth] = useState(today.getMonth())
    const firstDay = new Date(viewYear, viewMonth, 1).getDay()
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
    const monthName = new Date(viewYear, viewMonth).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
    const todayStr = today.toISOString().split('T')[0]
    const availSet = new Set(availableDates)

    const cells: (number | null)[] = []
    for (let i = 0; i < firstDay; i++) cells.push(null)
    for (let d = 1; d <= daysInMonth; d++) cells.push(d)

    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <button onClick={() => viewMonth === 0 ? (setViewMonth(11), setViewYear(viewYear - 1)) : setViewMonth(viewMonth - 1)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: MUTED }}>&lsaquo;</button>
          <span style={{ fontFamily: SERIF, fontWeight: 500, fontSize: '0.95rem', color: DARK }}>{monthName}</span>
          <button onClick={() => viewMonth === 11 ? (setViewMonth(0), setViewYear(viewYear + 1)) : setViewMonth(viewMonth + 1)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: MUTED }}>&rsaquo;</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', textAlign: 'center' }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
            <div key={d} style={{ fontSize: '0.7rem', color: accentLight, fontWeight: 600, padding: '0.25rem 0', textTransform: 'uppercase' }}>{d}</div>
          ))}
          {cells.map((day, i) => {
            if (day === null) return <div key={`e${i}`} />
            const dateStr = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
            const isPast = dateStr < todayStr
            const isAvail = availSet.has(dateStr)
            const isSel = dateStr === selectedDate
            const clickable = !isPast && isAvail
            return (
              <button key={dateStr} onClick={() => { if (clickable) { setSelectedDate(dateStr); setSelectedSlot(null); setStep(3) } }} disabled={!clickable}
                style={{
                  width: 36, height: 36, borderRadius: '50%', border: 'none', margin: '0 auto',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.82rem', fontWeight: isSel ? 700 : 400, cursor: clickable ? 'pointer' : 'default',
                  background: isSel ? accent : 'transparent',
                  color: isSel ? '#fff' : isPast ? '#d1d5db' : isAvail ? DARK : '#d1d5db',
                  transition: 'all 0.15s ease',
                }}
              >{day}</button>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: BG_CREAM, fontFamily: SANS }}>
      {/* Header */}
      <header style={{ background: accent, color: '#fff', padding: '1.5rem 1rem', textAlign: 'center' }}>
        <h1 style={{ fontFamily: SERIF, fontSize: '1.5rem', fontWeight: 500, margin: 0 }}>{bizName}</h1>
        <p style={{ fontSize: '0.85rem', opacity: 0.85, margin: '0.25rem 0 0' }}>Reserve a Table</p>
      </header>

      <main style={{ maxWidth: 520, margin: '0 auto', padding: '1.5rem 1rem' }}>
        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', color: '#dc2626', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        {step === 5 && confirmed ? (
          <div style={{ background: '#fff', borderRadius: 10, padding: '2rem', textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>✓</div>
            <h2 style={{ fontFamily: SERIF, fontSize: '1.3rem', color: DARK, marginBottom: '0.5rem' }}>Reservation Confirmed</h2>
            <p style={{ color: MUTED, fontSize: '0.9rem' }}>
              Party of {partySize} on {selectedDate} at {selectedSlot?.start_time}
            </p>
            <p style={{ color: MUTED, fontSize: '0.85rem', marginTop: '0.5rem' }}>
              A confirmation will be sent to {email}
            </p>
          </div>
        ) : (
          <>
            {/* Step 1: Party Size */}
            <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', border: '1px solid rgba(0,0,0,0.06)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.85rem' }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: step >= 1 ? accent : BG_WARM, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: step >= 1 ? '#fff' : accent }}>1</div>
                <h2 style={{ fontFamily: SERIF, fontSize: '1.05rem', fontWeight: 500, color: DARK, margin: 0 }}>Party Size</h2>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map(n => (
                  <button key={n} onClick={() => { setPartySize(n); setStep(2); setSelectedDate(''); setSelectedSlot(null) }}
                    style={{
                      padding: '0.6rem 1rem', borderRadius: 8, border: `1px solid ${partySize === n ? accent : '#e5e7eb'}`,
                      background: partySize === n ? accent : '#fff', color: partySize === n ? '#fff' : DARK,
                      cursor: 'pointer', fontWeight: partySize === n ? 600 : 400, fontSize: '0.9rem',
                      transition: 'all 0.15s ease',
                    }}
                  >{n}{n === 8 ? '+' : ''}</button>
                ))}
              </div>
            </div>

            {/* Step 2: Date */}
            {step >= 2 && (
              <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', border: '1px solid rgba(0,0,0,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.85rem' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: step >= 2 ? accent : BG_WARM, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: step >= 2 ? '#fff' : accent }}>2</div>
                  <h2 style={{ fontFamily: SERIF, fontSize: '1.05rem', fontWeight: 500, color: DARK, margin: 0 }}>Choose Date</h2>
                </div>
                {loading && !selectedDate ? (
                  <p style={{ color: MUTED, fontSize: '0.85rem' }}>Loading available dates...</p>
                ) : (
                  <Calendar />
                )}
              </div>
            )}

            {/* Step 3: Time Window */}
            {step >= 3 && selectedDate && (
              <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', border: '1px solid rgba(0,0,0,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.85rem' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: step >= 3 ? accent : BG_WARM, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: step >= 3 ? '#fff' : accent }}>3</div>
                  <h2 style={{ fontFamily: SERIF, fontSize: '1.05rem', fontWeight: 500, color: DARK, margin: 0 }}>Choose Time</h2>
                </div>
                {loading ? (
                  <p style={{ color: MUTED, fontSize: '0.85rem' }}>Loading available times...</p>
                ) : windows.length === 0 ? (
                  <p style={{ color: MUTED, fontSize: '0.85rem' }}>No availability on this date</p>
                ) : (
                  windows.map((w: any) => (
                    <div key={w.id} style={{ marginBottom: '1rem' }}>
                      <h3 style={{ fontFamily: SERIF, fontSize: '0.9rem', color: DARK, marginBottom: '0.5rem' }}>
                        {w.name} ({w.open_time} – {w.close_time})
                      </h3>
                      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                        {w.slots?.filter((s: any) => s.has_capacity).map((slot: any) => (
                          <button key={slot.start_time}
                            onClick={() => { setSelectedSlot(slot); setStep(4) }}
                            style={{
                              padding: '0.5rem 0.75rem', borderRadius: 6,
                              border: `1px solid ${selectedSlot?.start_time === slot.start_time ? accent : '#e5e7eb'}`,
                              background: selectedSlot?.start_time === slot.start_time ? accent : '#fff',
                              color: selectedSlot?.start_time === slot.start_time ? '#fff' : DARK,
                              cursor: 'pointer', fontSize: '0.82rem', fontWeight: 500,
                              transition: 'all 0.15s ease',
                            }}
                          >{slot.start_time}</button>
                        ))}
                        {w.slots?.filter((s: any) => s.has_capacity).length === 0 && (
                          <p style={{ color: MUTED, fontSize: '0.82rem' }}>Fully booked for {w.name}</p>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Step 4: Your Details */}
            {step >= 4 && selectedSlot && (
              <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', border: '1px solid rgba(0,0,0,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.85rem' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: accent, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#fff' }}>4</div>
                  <h2 style={{ fontFamily: SERIF, fontSize: '1.05rem', fontWeight: 500, color: DARK, margin: 0 }}>Your Details</h2>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <input placeholder="Full Name *" value={name} onChange={e => setName(e.target.value)}
                    style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS }} />
                  <input placeholder="Email *" type="email" value={email} onChange={e => setEmail(e.target.value)}
                    style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS }} />
                  <input placeholder="Phone *" type="tel" value={phone} onChange={e => setPhone(e.target.value)}
                    style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS }} />
                  <textarea placeholder="Special requests or dietary requirements" value={notes} onChange={e => setNotes(e.target.value)} rows={3}
                    style={{ padding: '0.65rem 0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', fontSize: '0.9rem', fontFamily: SANS, resize: 'vertical' }} />
                </div>

                {/* Summary */}
                <div style={{ background: BG_WARM, borderRadius: 8, padding: '1rem', marginTop: '1rem', fontSize: '0.85rem', color: DARK }}>
                  <strong>Reservation Summary</strong>
                  <div style={{ marginTop: '0.5rem', lineHeight: 1.6 }}>
                    Party of {partySize} · {new Date(selectedDate + 'T00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })} · {selectedSlot.start_time}
                  </div>
                </div>

                <button onClick={handleSubmit} disabled={submitting}
                  style={{
                    width: '100%', marginTop: '1rem', padding: '0.85rem', borderRadius: 8,
                    background: accent, color: '#fff', border: 'none', cursor: submitting ? 'wait' : 'pointer',
                    fontWeight: 600, fontSize: '0.95rem', fontFamily: SANS, opacity: submitting ? 0.7 : 1,
                    transition: 'opacity 0.15s ease',
                  }}
                >{submitting ? 'Reserving...' : 'Confirm Reservation'}</button>
              </div>
            )}
          </>
        )}

        <div style={{ textAlign: 'center', padding: '2rem 0 0.5rem', fontSize: '0.72rem', color: accentLight, letterSpacing: '0.03em' }}>
          Powered by NBNE
        </div>
      </main>
    </div>
  )
}
