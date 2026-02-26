'use client'

import { useState, useEffect } from 'react'
import { getStaffSlots, createBooking } from '@/lib/api'

interface Props {
  date: string
  time: string
  services: any[]
  staffList: any[]
  onClose: () => void
  onCreated: (booking: any) => void
}

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

export default function NewBookingModal({ date, time, services, staffList, onClose, onCreated }: Props) {
  const [step, setStep] = useState(1)
  const [serviceId, setServiceId] = useState<number | null>(null)
  const [staffId, setStaffId] = useState<number | null>(null)
  const [selectedTime, setSelectedTime] = useState(time)
  const [availableSlots, setAvailableSlots] = useState<any[]>([])
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  const selectedService = services.find(s => s.id === serviceId)
  const selectedStaff = staffList.find(s => s.id === staffId)

  // Fetch available slots when staff + service + date are selected
  useEffect(() => {
    if (!staffId || !serviceId) return
    setSlotsLoading(true)
    setAvailableSlots([])
    getStaffSlots(staffId, serviceId, date).then(res => {
      const slots = res.data?.slots || res.data || []
      setAvailableSlots(slots)
      // Auto-select the closest slot to the clicked time
      if (slots.length > 0) {
        const clickedMinutes = timeToMinutes(time)
        let closest = slots[0]
        let closestDiff = Math.abs(timeToMinutes(closest.start_time) - clickedMinutes)
        for (const slot of slots) {
          const diff = Math.abs(timeToMinutes(slot.start_time) - clickedMinutes)
          if (diff < closestDiff) {
            closest = slot
            closestDiff = diff
          }
        }
        setSelectedTime(closest.start_time)
      }
    }).catch(() => {}).finally(() => setSlotsLoading(false))
  }, [staffId, serviceId, date, time])

  function timeToMinutes(t: string) {
    const [h, m] = t.split(':').map(Number)
    return h * 60 + (m || 0)
  }

  async function handleCreate() {
    if (!serviceId || !staffId || !customerName || !customerEmail || !customerPhone) {
      setError('Please fill in all required fields')
      return
    }
    setCreating(true)
    setError('')
    try {
      const res = await createBooking({
        service: serviceId,
        staff: staffId,
        date,
        time: selectedTime,
        client_name: customerName,
        client_email: customerEmail,
        client_phone: customerPhone,
        notes: notes ? `[Admin booking] ${notes}` : '[Admin booking]',
      })
      if (res.error) {
        setError(res.error)
        setCreating(false)
        return
      }
      onCreated(res.data)
    } catch (e: any) {
      setError(e.message || 'Failed to create booking')
      setCreating(false)
    }
  }

  const dayLabel = new Date(date + 'T12:00:00').toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

  return (
    <div style={overlay} onClick={onClose}>
      <div style={modal} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={header}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>New Booking</h3>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: 2 }}>{dayLabel} at {time}</div>
          </div>
          <button style={closeBtn} onClick={onClose}>✕</button>
        </div>

        {/* Step indicators */}
        <div style={steps}>
          {['Service', 'Staff & Time', 'Customer'].map((label, i) => (
            <div key={label} style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
            }}>
              <div style={{
                width: 24, height: 24, borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.72rem', fontWeight: 700,
                background: step > i + 1 ? '#22c55e' : step === i + 1 ? '#2563eb' : '#e2e8f0',
                color: step >= i + 1 ? '#fff' : '#94a3b8',
              }}>{step > i + 1 ? '✓' : i + 1}</div>
              <span style={{
                fontSize: '0.78rem', fontWeight: step === i + 1 ? 700 : 500,
                color: step === i + 1 ? '#1e293b' : '#94a3b8',
              }}>{label}</span>
            </div>
          ))}
        </div>

        {/* Body */}
        <div style={body}>
          {error && (
            <div style={{
              padding: '0.6rem 0.85rem', background: '#fef2f2', border: '1px solid #fecaca',
              borderRadius: 6, fontSize: '0.82rem', color: '#dc2626', marginBottom: '0.75rem',
            }}>{error}</div>
          )}

          {/* Step 1: Service */}
          {step === 1 && (
            <div>
              <label style={labelStyle}>Select Service</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: 300, overflowY: 'auto' }}>
                {services.filter(s => s.active !== false).map(s => (
                  <button
                    key={s.id}
                    onClick={() => { setServiceId(s.id); setStep(2) }}
                    style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.7rem 0.85rem', borderRadius: 8,
                      border: serviceId === s.id ? '2px solid #2563eb' : '1px solid #e2e8f0',
                      background: serviceId === s.id ? '#eff6ff' : '#fff',
                      cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#1e293b' }}>{s.name}</div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{s.duration_minutes} min</div>
                    </div>
                    <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#2563eb' }}>
                      {formatPrice(s.price_pence)}
                    </div>
                  </button>
                ))}
                {services.length === 0 && (
                  <div style={{ color: '#94a3b8', fontSize: '0.85rem', padding: '1rem', textAlign: 'center' }}>
                    No services configured. Add services in the Services admin page first.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Staff & Time */}
          {step === 2 && (
            <div>
              <label style={labelStyle}>Select Staff Member</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {staffList.filter(s => s.active !== false).map(s => (
                  <button
                    key={s.id}
                    onClick={() => setStaffId(s.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.75rem',
                      padding: '0.6rem 0.85rem', borderRadius: 8,
                      border: staffId === s.id ? '2px solid #2563eb' : '1px solid #e2e8f0',
                      background: staffId === s.id ? '#eff6ff' : '#fff',
                      cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                    }}
                  >
                    <div style={{
                      width: 32, height: 32, borderRadius: '50%', background: '#e0e7ff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.75rem', fontWeight: 700, color: '#4338ca', flexShrink: 0,
                    }}>{(s.name || '?')[0].toUpperCase()}</div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#1e293b' }}>{s.name}</div>
                      {s.role && <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{s.role}</div>}
                    </div>
                  </button>
                ))}
              </div>

              {staffId && (
                <>
                  <label style={labelStyle}>Available Times</label>
                  {slotsLoading ? (
                    <div style={{ color: '#94a3b8', fontSize: '0.85rem', padding: '0.5rem' }}>Loading slots…</div>
                  ) : availableSlots.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', maxHeight: 160, overflowY: 'auto' }}>
                      {availableSlots.map((slot: any) => (
                        <button
                          key={slot.start_time}
                          onClick={() => setSelectedTime(slot.start_time)}
                          style={{
                            padding: '0.35rem 0.65rem', borderRadius: 6, fontSize: '0.82rem',
                            fontWeight: selectedTime === slot.start_time ? 700 : 500,
                            border: selectedTime === slot.start_time ? '2px solid #2563eb' : '1px solid #e2e8f0',
                            background: selectedTime === slot.start_time ? '#2563eb' : '#fff',
                            color: selectedTime === slot.start_time ? '#fff' : '#334155',
                            cursor: 'pointer', fontFamily: 'inherit',
                          }}
                        >{slot.start_time}</button>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: '#94a3b8', fontSize: '0.85rem', padding: '0.5rem' }}>
                      No available slots for this staff member on this date.
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Step 3: Customer Details */}
          {step === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {/* Summary */}
              <div style={{
                padding: '0.65rem 0.85rem', background: '#f8fafc', borderRadius: 8,
                border: '1px solid #e2e8f0', fontSize: '0.82rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Service</span>
                  <span style={{ fontWeight: 600 }}>{selectedService?.name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                  <span style={{ color: '#64748b' }}>Staff</span>
                  <span style={{ fontWeight: 600 }}>{selectedStaff?.name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                  <span style={{ color: '#64748b' }}>Time</span>
                  <span style={{ fontWeight: 600 }}>{selectedTime} on {date}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                  <span style={{ color: '#64748b' }}>Price</span>
                  <span style={{ fontWeight: 700, color: '#2563eb' }}>{selectedService ? formatPrice(selectedService.price_pence) : ''}</span>
                </div>
              </div>

              <div>
                <label style={labelStyle}>Customer Name *</label>
                <input
                  value={customerName} onChange={e => setCustomerName(e.target.value)}
                  placeholder="e.g. Jane Smith"
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Email *</label>
                <input
                  type="email" value={customerEmail} onChange={e => setCustomerEmail(e.target.value)}
                  placeholder="e.g. jane@example.com"
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Phone *</label>
                <input
                  type="tel" value={customerPhone} onChange={e => setCustomerPhone(e.target.value)}
                  placeholder="e.g. 07700 900123"
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Notes (optional)</label>
                <textarea
                  value={notes} onChange={e => setNotes(e.target.value)}
                  placeholder="Internal notes about this booking…"
                  rows={2}
                  style={{ ...inputStyle, resize: 'vertical' as const }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={footer}>
          {step > 1 && (
            <button
              onClick={() => setStep(s => s - 1)}
              style={{
                padding: '0.5rem 1rem', borderRadius: 6, border: '1px solid #e2e8f0',
                background: '#fff', fontSize: '0.82rem', fontWeight: 600, color: '#334155',
                cursor: 'pointer', fontFamily: 'inherit',
              }}
            >← Back</button>
          )}
          <div style={{ flex: 1 }} />
          {step === 2 && staffId && (
            <button
              onClick={() => setStep(3)}
              disabled={!selectedTime || availableSlots.length === 0}
              style={{
                padding: '0.5rem 1.25rem', borderRadius: 6, border: 'none',
                background: (!selectedTime || availableSlots.length === 0) ? '#94a3b8' : '#2563eb',
                fontSize: '0.82rem', fontWeight: 700, color: '#fff',
                cursor: (!selectedTime || availableSlots.length === 0) ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
              }}
            >Next →</button>
          )}
          {step === 3 && (
            <button
              onClick={handleCreate}
              disabled={creating || !customerName || !customerEmail || !customerPhone}
              style={{
                padding: '0.5rem 1.5rem', borderRadius: 6, border: 'none',
                background: creating ? '#94a3b8' : '#22c55e',
                fontSize: '0.82rem', fontWeight: 700, color: '#fff',
                cursor: creating ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
              }}
            >{creating ? 'Creating…' : 'Create Booking'}</button>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Styles ──
const overlay: React.CSSProperties = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  background: 'rgba(0,0,0,0.35)', display: 'flex',
  alignItems: 'center', justifyContent: 'center', zIndex: 1000,
}
const modal: React.CSSProperties = {
  background: '#fff', borderRadius: 12, boxShadow: '0 12px 40px rgba(0,0,0,0.2)',
  width: 460, maxWidth: '94vw', maxHeight: '90vh', overflow: 'hidden',
  display: 'flex', flexDirection: 'column',
}
const header: React.CSSProperties = {
  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  padding: '0.85rem 1.15rem', borderBottom: '1px solid #f1f5f9', background: '#f8fafc',
}
const closeBtn: React.CSSProperties = {
  background: 'none', border: 'none', fontSize: '1.1rem',
  cursor: 'pointer', color: '#64748b', padding: '0.2rem 0.4rem',
}
const steps: React.CSSProperties = {
  display: 'flex', gap: '1rem', padding: '0.65rem 1.15rem',
  borderBottom: '1px solid #f1f5f9', background: '#fff',
}
const body: React.CSSProperties = {
  padding: '1rem 1.15rem', overflowY: 'auto', flex: 1,
}
const footer: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: '0.5rem',
  padding: '0.75rem 1.15rem', borderTop: '1px solid #f1f5f9',
}
const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: '0.78rem', fontWeight: 600,
  color: '#475569', marginBottom: '0.35rem',
}
const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6,
  border: '1px solid #e2e8f0', fontSize: '0.88rem', fontFamily: 'inherit',
  outline: 'none', boxSizing: 'border-box',
}
