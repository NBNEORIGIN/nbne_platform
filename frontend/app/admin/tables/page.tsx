'use client'

import { useState, useEffect } from 'react'
import { getTables, createTable, updateTable, deleteTable } from '@/lib/api'

const ZONES = ['Main', 'Window', 'Terrace', 'Private', 'Bar', '']

export default function TablesAdmin() {
  const [tables, setTables] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<any>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', min_seats: 1, max_seats: 4, zone: '', combinable: false })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    const res = await getTables()
    setTables(res.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  function openNew() {
    setEditing(null)
    setForm({ name: '', min_seats: 1, max_seats: 4, zone: '', combinable: false })
    setShowForm(true)
    setError('')
  }

  function openEdit(t: any) {
    setEditing(t)
    setForm({ name: t.name, min_seats: t.min_seats, max_seats: t.max_seats, zone: t.zone || '', combinable: t.combinable })
    setShowForm(true)
    setError('')
  }

  async function handleSave() {
    if (!form.name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    const res = editing
      ? await updateTable(editing.id, form)
      : await createTable(form)
    setSaving(false)
    if (res.error) { setError(res.error); return }
    setShowForm(false)
    load()
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this table?')) return
    await deleteTable(id)
    load()
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Tables</h1>
        <button onClick={openNew} className="btn btn-primary">+ Add Table</button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '1.25rem', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>{editing ? 'Edit Table' : 'New Table'}</h2>
          {error && <div style={{ color: '#dc2626', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Table 1"
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Min Seats</label>
              <input type="number" min={1} value={form.min_seats} onChange={e => setForm({ ...form, min_seats: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Max Seats</label>
              <input type="number" min={1} value={form.max_seats} onChange={e => setForm({ ...form, max_seats: +e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 500, display: 'block', marginBottom: '0.25rem' }}>Zone</label>
              <select value={form.zone} onChange={e => setForm({ ...form, zone: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
                {ZONES.map(z => <option key={z} value={z}>{z || '(none)'}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input type="checkbox" checked={form.combinable} onChange={e => setForm({ ...form, combinable: e.target.checked })} id="combinable" />
              <label htmlFor="combinable" style={{ fontSize: '0.85rem' }}>Combinable</label>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button onClick={handleSave} disabled={saving} className="btn btn-primary">{saving ? 'Saving...' : 'Save'}</button>
            <button onClick={() => setShowForm(false)} className="btn btn-ghost">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <p style={{ color: '#6b7280' }}>Loading tables...</p>
      ) : tables.length === 0 ? (
        <p style={{ color: '#6b7280' }}>No tables configured yet.</p>
      ) : (
        <div style={{ display: 'grid', gap: '0.5rem' }}>
          {tables.map((t: any) => (
            <div key={t.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '0.85rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong>{t.name}</strong>
                <span style={{ color: '#6b7280', fontSize: '0.85rem', marginLeft: '0.75rem' }}>
                  {t.min_seats}–{t.max_seats} seats
                  {t.zone && ` · ${t.zone}`}
                  {t.combinable && ' · Combinable'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <button onClick={() => openEdit(t)} className="btn btn-ghost" style={{ fontSize: '0.82rem' }}>Edit</button>
                <button onClick={() => handleDelete(t.id)} className="btn btn-ghost" style={{ fontSize: '0.82rem', color: '#dc2626' }}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
