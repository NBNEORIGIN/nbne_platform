'use client'

import { useState, useEffect } from 'react'
import { getClassSessions, getClassTypes, getBookableStaff, createClassSession, updateClassSession, deleteClassSession } from '@/lib/api'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function TimetableAdmin() {
  const [sessions, setSessions] = useState<any[]>([])
  const [classTypes, setClassTypes] = useState<any[]>([])
  const [instructors, setInstructors] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<any>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ class_type: '', instructor: '', day_of_week: 0, start_time: '09:00', end_time: '09:45', room: '', override_capacity: '' as string })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    const [sessRes, ctRes, staffRes] = await Promise.all([
      getClassSessions(),
      getClassTypes(),
      getBookableStaff(),
    ])
    setSessions(sessRes.data || [])
    setClassTypes(ctRes.data || [])
    setInstructors(staffRes.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  function openNew() {
    setEditing(null)
    setForm({ class_type: classTypes[0]?.id || '', instructor: '', day_of_week: 0, start_time: '09:00', end_time: '09:45', room: '', override_capacity: '' })
    setShowForm(true)
    setError('')
  }

  function openEdit(s: any) {
    setEditing(s)
    setForm({
      class_type: s.class_type,
      instructor: s.instructor || '',
      day_of_week: s.day_of_week,
      start_time: s.start_time?.slice(0, 5) || '09:00',
      end_time: s.end_time?.slice(0, 5) || '09:45',
      room: s.room || '',
      override_capacity: s.override_capacity != null ? String(s.override_capacity) : '',
    })
    setShowForm(true)
    setError('')
  }

  async function handleSave() {
    if (!form.class_type) { setError('Class type is required'); return }
    setSaving(true)
    setError('')
    const payload: any = {
      class_type: Number(form.class_type),
      day_of_week: form.day_of_week,
      start_time: form.start_time,
      end_time: form.end_time,
      room: form.room,
    }
    if (form.instructor) payload.instructor = Number(form.instructor)
    else payload.instructor = null
    if (form.override_capacity) payload.override_capacity = Number(form.override_capacity)
    else payload.override_capacity = null

    const res = editing
      ? await updateClassSession(editing.id, payload)
      : await createClassSession(payload)
    setSaving(false)
    if (res.error) { setError(res.error); return }
    setShowForm(false)
    load()
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this session?')) return
    await deleteClassSession(id)
    load()
  }

  // Group by day
  const grouped: Record<number, any[]> = {}
  sessions.forEach(s => {
    if (!grouped[s.day_of_week]) grouped[s.day_of_week] = []
    grouped[s.day_of_week].push(s)
  })

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Timetable</h1>
        <button onClick={openNew} className="btn btn-primary" disabled={classTypes.length === 0}>+ Add Session</button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '1.25rem', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>{editing ? 'Edit Session' : 'New Session'}</h2>
          {error && <div style={{ color: '#dc2626', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Class Type</label>
              <select value={form.class_type} onChange={e => setForm({ ...form, class_type: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                <option value="">Select...</option>
                {classTypes.map((ct: any) => <option key={ct.id} value={ct.id}>{ct.name}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Instructor</label>
              <select value={form.instructor} onChange={e => setForm({ ...form, instructor: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                <option value="">(none)</option>
                {instructors.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Day</label>
              <select value={form.day_of_week} onChange={e => setForm({ ...form, day_of_week: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Room</label>
              <input value={form.room} onChange={e => setForm({ ...form, room: e.target.value })} placeholder="e.g. Studio 1"
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Start Time</label>
              <input type="time" value={form.start_time} onChange={e => setForm({ ...form, start_time: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>End Time</label>
              <input type="time" value={form.end_time} onChange={e => setForm({ ...form, end_time: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Override Capacity (blank = use class default)</label>
              <input type="number" min={1} value={form.override_capacity} onChange={e => setForm({ ...form, override_capacity: e.target.value })} placeholder="Leave blank for default"
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
        <p style={{ color: '#6b7280' }}>Loading timetable...</p>
      ) : sessions.length === 0 ? (
        <p style={{ color: '#6b7280' }}>No sessions configured yet. Add class types first, then create sessions.</p>
      ) : (
        DAYS.map((day, i) => {
          const daySessions = grouped[i]
          if (!daySessions || daySessions.length === 0) return null
          return (
            <div key={i} style={{ marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#374151', marginBottom: '0.5rem' }}>{day}</h3>
              <div style={{ display: 'grid', gap: '0.4rem' }}>
                {daySessions.map((s: any) => (
                  <div key={s.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <strong>{s.class_type_name || 'Class'}</strong>
                      <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                        {s.start_time?.slice(0, 5)} – {s.end_time?.slice(0, 5)}
                        {s.room && ` · ${s.room}`}
                        {s.instructor_name && ` · ${s.instructor_name}`}
                        {s.capacity && ` · cap ${s.capacity}`}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button onClick={() => openEdit(s)} className="btn btn-ghost" style={{ fontSize: '0.82rem' }}>Edit</button>
                      <button onClick={() => handleDelete(s.id)} className="btn btn-ghost" style={{ fontSize: '0.82rem', color: '#dc2626' }}>Delete</button>
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
