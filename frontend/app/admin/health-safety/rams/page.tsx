'use client'

import { useState, useEffect, useCallback } from 'react'
import { getRams, createRams, deleteRams } from '@/lib/api'

function fmtDate(d: string | null) {
  if (!d) return '—'
  return new Date(d + 'T00:00:00').toLocaleDateString('en-GB')
}

export default function RamsListPage() {
  const [rams, setRams] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')
  const [creating, setCreating] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const res = await getRams()
    if (res.data) setRams(Array.isArray(res.data) ? res.data : [])
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate() {
    if (!title.trim()) return
    setCreating(true)
    const res = await createRams({ title: title.trim(), description: desc.trim() })
    if (res.data?.id) {
      window.location.href = `/admin/health-safety/rams/${res.data.id}`
    } else {
      setCreating(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this RAMS document permanently?')) return
    await deleteRams(id)
    setRams(prev => prev.filter(r => r.id !== id))
  }

  if (loading) return <div className="empty-state">Loading RAMS documents…</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>RAMS Documents</h2>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
            Risk Assessments & Method Statements
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreate(true)}
        >+ New RAMS</button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
          <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem' }}>Create New RAMS</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            <input
              placeholder="RAMS title (e.g. Roof Access Works — 12 High St)"
              value={title}
              onChange={e => setTitle(e.target.value)}
              style={{ padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #e2e8f0', fontSize: '0.88rem', fontFamily: 'inherit' }}
              autoFocus
            />
            <textarea
              placeholder="Brief description (optional)"
              value={desc}
              onChange={e => setDesc(e.target.value)}
              rows={2}
              style={{ padding: '0.5rem 0.75rem', borderRadius: 6, border: '1px solid #e2e8f0', fontSize: '0.88rem', fontFamily: 'inherit', resize: 'vertical' }}
            />
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-primary btn-sm" onClick={handleCreate} disabled={creating || !title.trim()}>
                {creating ? 'Creating…' : 'Create & Edit'}
              </button>
              <button className="btn btn-outline btn-sm" onClick={() => { setShowCreate(false); setTitle(''); setDesc('') }}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {rams.length === 0 ? (
        <div className="empty-state">
          No RAMS documents yet. Click <strong>+ New RAMS</strong> to create one.
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {rams.map(r => (
            <div key={r.id} className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <a href={`/admin/health-safety/rams/${r.id}`} style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--color-primary)', textDecoration: 'none' }}>
                  {r.title}
                </a>
                {r.reference_number && <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginLeft: '0.5rem' }}>Ref: {r.reference_number}</span>}
                {r.description && <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{r.description}</div>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                <span className={`badge ${r.status === 'ACTIVE' ? 'badge-success' : r.status === 'EXPIRED' ? 'badge-danger' : 'badge-warning'}`}>
                  {r.status}
                </span>
                {r.completion && (
                  <span style={{ fontSize: '0.75rem', color: r.completion.complete ? '#16a34a' : '#f59e0b', fontWeight: 600 }}>
                    {r.completion.percentage}%
                  </span>
                )}
                {r.expiry_date && <span style={{ fontSize: '0.75rem', color: r.is_expired ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>{r.is_expired ? 'Expired' : 'Expires'}: {fmtDate(r.expiry_date)}</span>}
                <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)', opacity: 0.7 }} onClick={() => handleDelete(r.id)} title="Delete">🗑</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
