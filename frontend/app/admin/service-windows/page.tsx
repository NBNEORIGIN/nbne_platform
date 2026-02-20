'use client'

import { useState, useEffect } from 'react'
import { getServiceWindows, createServiceWindow, updateServiceWindow, deleteServiceWindow } from '@/lib/api'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function ServiceWindowsAdmin() {
  const [windows, setWindows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<any>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', day_of_week: 0, open_time: '12:00', close_time: '14:30', last_booking_time: '13:30', turn_time_minutes: 90, max_covers: 50 })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    const res = await getServiceWindows()
    setWindows(res.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  function openNew() {
    setEditing(null)
    setForm({ name: '', day_of_week: 0, open_time: '12:00', close_time: '14:30', last_booking_time: '13:30', turn_time_minutes: 90, max_covers: 50 })
    setShowForm(true)
    setError('')
  }

  function openEdit(w: any) {
    setEditing(w)
    setForm({
      name: w.name, day_of_week: w.day_of_week,
      open_time: w.open_time?.slice(0, 5) || '12:00',
      close_time: w.close_time?.slice(0, 5) || '14:30',
      last_booking_time: w.last_booking_time?.slice(0, 5) || '13:30',
      turn_time_minutes: w.turn_time_minutes || 90,
      max_covers: w.max_covers || 50,
    })
    setShowForm(true)
    setError('')
  }

  async function handleSave() {
    if (!form.name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    const res = editing
      ? await updateServiceWindow(editing.id, form)
      : await createServiceWindow(form)
    setSaving(false)
    if (res.error) { setError(res.error); return }
    setShowForm(false)
    load()
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this service window?')) return
    await deleteServiceWindow(id)
    load()
  }

  // Group by day
  const grouped: Record<number, any[]> = {}
  windows.forEach(w => {
    if (!grouped[w.day_of_week]) grouped[w.day_of_week] = []
    grouped[w.day_of_week].push(w)
  })

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Service Windows</h1>
        <button onClick={openNew} className="btn btn-primary">+ Add Window</button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '1.25rem', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>{editing ? 'Edit Service Window' : 'New Service Window'}</h2>
          {error && <div style={{ color: '#dc2626', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Lunch, Dinner"
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Day</label>
              <select value={form.day_of_week} onChange={e => setForm({ ...form, day_of_week: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Open Time</label>
              <input type="time" value={form.open_time} onChange={e => setForm({ ...form, open_time: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Close Time</label>
              <input type="time" value={form.close_time} onChange={e => setForm({ ...form, close_time: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Last Booking Time</label>
              <input type="time" value={form.last_booking_time} onChange={e => setForm({ ...form, last_booking_time: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Turn Time (mins)</label>
              <input type="number" min={15} value={form.turn_time_minutes} onChange={e => setForm({ ...form, turn_time_minutes: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Max Covers</label>
              <input type="number" min={1} value={form.max_covers} onChange={e => setForm({ ...form, max_covers: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button onClick={handleSave} disabled={saving} className="btn btn-primary">{saving ? 'Saving...' : 'Save'}</button>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <p style={{ color: '#6b7280' }}>Loading service windows...</p>
      ) : windows.length === 0 ? (
        <p style={{ color: '#6b7280' }}>No service windows configured yet.</p>
      ) : (
        DAYS.map((day, i) => {
          const dayWindows = grouped[i]
          if (!dayWindows || dayWindows.length === 0) return null
          return (
            <div key={i} style={{ marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#374151', marginBottom: '0.5rem' }}>{day}</h3>
              <div style={{ display: 'grid', gap: '0.4rem' }}>
                {dayWindows.map((w: any) => (
                  <div key={w.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{w.name}</strong>
                      <span style={{ color: '#6b7280', fontSize: '0.85rem', marginLeft: '0.75rem' }}>
                        {w.open_time?.slice(0, 5)} – {w.close_time?.slice(0, 5)} · Last booking {w.last_booking_time?.slice(0, 5)} · {w.turn_time_minutes}min turn · {w.max_covers} covers
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button onClick={() => openEdit(w)} className="btn btn-ghost" style={{ fontSize: '0.82rem' }}>Edit</button>
                      <button onClick={() => handleDelete(w.id)} className="btn btn-ghost" style={{ fontSize: '0.82rem', color: '#dc2626' }}>Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
