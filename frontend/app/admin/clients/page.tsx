'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  getLeads, createLead, updateLead, quickAddLead,
  actionContact, actionConvert, actionFollowupDone,
  getLeadNotes, addLeadNote, getLeadHistory,
} from '@/lib/api'

function fmtPrice(pence: number) { return '£' + (pence / 100).toFixed(pence % 100 === 0 ? 0 : 2) }
function fmtDate(d: string | null) { if (!d) return '—'; return new Date(d + 'T00:00:00').toLocaleDateString('en-GB') }

const STATUS_BADGE: Record<string, string> = {
  NEW: 'badge-info', CONTACTED: 'badge-warning', QUALIFIED: 'badge-warning',
  CONVERTED: 'badge-success', LOST: 'badge-danger',
}
const SCORE_BADGE: Record<string, { bg: string; color: string }> = {
  High: { bg: '#dcfce7', color: '#15803d' },
  Medium: { bg: '#fef9c3', color: '#854d0e' },
  Low: { bg: '#fee2e2', color: '#991b1b' },
}
const ACTION_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  Contact: { bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd' },
  Convert: { bg: '#dcfce7', color: '#15803d', border: '#86efac' },
  'Follow up': { bg: '#fef9c3', color: '#854d0e', border: '#fde047' },
  'Follow up today': { bg: '#fed7aa', color: '#9a3412', border: '#fdba74' },
  'Follow up overdue': { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
}
const PIPELINE_COLS = ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED'] as const

type ViewMode = 'table' | 'pipeline'

export default function AdminClientsPage() {
  const [leads, setLeads] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [toast, setToast] = useState<string | null>(null)

  // NL quick-add
  const [nlText, setNlText] = useState('')
  const [nlLoading, setNlLoading] = useState(false)

  // Side panel
  const [selected, setSelected] = useState<any>(null)
  const [notes, setNotes] = useState<any[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [newNote, setNewNote] = useState('')
  const [panelTab, setPanelTab] = useState<'details' | 'notes' | 'history'>('details')

  // Inline editing
  const [editingCell, setEditingCell] = useState<{ id: number; field: string } | null>(null)
  const [editValue, setEditValue] = useState('')

  // Add lead form
  const [showAdd, setShowAdd] = useState(false)

  const flash = useCallback((msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2500) }, [])

  const reload = useCallback(async () => {
    const r = await getLeads()
    setLeads(r.data || [])
    setLoading(false)
  }, [])

  useEffect(() => { reload() }, [reload])

  // Load notes + history when selecting a lead
  useEffect(() => {
    if (!selected) return
    getLeadNotes(selected.id).then(r => setNotes(r.data || []))
    getLeadHistory(selected.id).then(r => setHistory(r.data || []))
  }, [selected?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // --- Handlers ---

  async function handleQuickAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!nlText.trim()) return
    setNlLoading(true)
    const r = await quickAddLead(nlText)
    if (!r.error) { flash(`Added: ${r.data?.name}`); setNlText(''); reload() }
    setNlLoading(false)
  }

  async function handleAction(id: number, action: string) {
    if (action === 'Contact' || action === 'Follow up' || action === 'Follow up today' || action === 'Follow up overdue') {
      if (action === 'Contact') {
        await actionContact(id)
        flash('Contacted — follow-up set for 7 days')
      } else {
        await actionFollowupDone(id)
        flash('Follow-up done — rescheduled +7 days')
      }
    } else if (action === 'Convert') {
      await actionConvert(id)
      flash('Converted to client')
    }
    reload()
    if (selected?.id === id) {
      const r = await getLeads()
      const updated = (r.data || []).find((l: any) => l.id === id)
      if (updated) setSelected(updated)
    }
  }

  async function handleInlineEdit(id: number, field: string, value: string) {
    const payload: any = {}
    if (field === 'value_pence') {
      const num = parseFloat(value.replace(/[£,]/g, ''))
      payload.value_pence = isNaN(num) ? 0 : Math.round(num * 100)
    } else if (field === 'marketing_consent') {
      payload.marketing_consent = value === 'true'
    } else {
      payload[field] = value
    }
    await updateLead(id, payload)
    setEditingCell(null)
    reload()
  }

  async function handleAddNote() {
    if (!selected || !newNote.trim()) return
    await addLeadNote(selected.id, newNote)
    setNewNote('')
    const r = await getLeadNotes(selected.id)
    setNotes(r.data || [])
    getLeadHistory(selected.id).then(r2 => setHistory(r2.data || []))
  }

  async function handleAddLead(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createLead({
      name: fd.get('name'), email: fd.get('email'), phone: fd.get('phone'),
      source: fd.get('source'), value_pence: Math.round(parseFloat(fd.get('value') as string || '0') * 100),
      notes: fd.get('notes'), marketing_consent: fd.get('consent') === 'on',
    })
    setShowAdd(false); flash('Lead added'); reload()
  }

  async function handlePipelineDrop(leadId: number, newStatus: string) {
    await updateLead(leadId, { status: newStatus })
    reload()
  }

  if (loading) return <div className="empty-state">Loading…</div>

  // Filtering
  const filtered = leads
    .filter(l => filter === 'ALL' || l.status === filter)
    .filter(l => !search || (l.name || '').toLowerCase().includes(search.toLowerCase()) || (l.email || '').toLowerCase().includes(search.toLowerCase()))

  // Follow-up reminders
  const followUps = leads.filter(l => l.action_required && (l.action_required.includes('Follow up') || l.action_required === 'Contact') && l.status !== 'CONVERTED' && l.status !== 'LOST')
  const urgentFollowUps = followUps.filter(l => l.action_required?.includes('overdue') || l.action_required === 'Follow up today')

  // Stats
  const pipelineValue = leads.filter(l => !['CONVERTED', 'LOST'].includes(l.status)).reduce((s: number, l: any) => s + (l.value_pence || 0), 0)

  // CSV export URL
  const exportUrl = `/api/django/crm/leads/export/${filter !== 'ALL' ? `?status=${filter}` : ''}`

  // --- Inline edit cell renderer ---
  function EditableCell({ lead, field, display, type = 'text' }: { lead: any; field: string; display: React.ReactNode; type?: string }) {
    const isEditing = editingCell?.id === lead.id && editingCell?.field === field
    if (isEditing) {
      if (field === 'status') {
        return (
          <select autoFocus className="form-input" style={{ padding: '2px 4px', fontSize: '0.8rem', width: '100%' }}
            value={editValue} onChange={e => { handleInlineEdit(lead.id, field, e.target.value) }}>
            {['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )
      }
      if (field === 'source') {
        return (
          <select autoFocus className="form-input" style={{ padding: '2px 4px', fontSize: '0.8rem', width: '100%' }}
            value={editValue} onChange={e => { handleInlineEdit(lead.id, field, e.target.value) }}>
            {['booking', 'website', 'referral', 'social', 'manual', 'other'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )
      }
      return (
        <input autoFocus className="form-input" type={type} style={{ padding: '2px 4px', fontSize: '0.8rem', width: '100%' }}
          value={editValue}
          onChange={e => setEditValue(e.target.value)}
          onBlur={() => handleInlineEdit(lead.id, field, editValue)}
          onKeyDown={e => { if (e.key === 'Enter') handleInlineEdit(lead.id, field, editValue); if (e.key === 'Escape') setEditingCell(null) }}
        />
      )
    }
    return (
      <span onClick={() => { setEditingCell({ id: lead.id, field }); setEditValue(field === 'value_pence' ? (lead.value_pence / 100).toFixed(2) : (lead[field] || '')) }}
        style={{ cursor: 'pointer', borderBottom: '1px dashed var(--color-border)', display: 'inline-block', minWidth: 30 }}
        title="Click to edit">
        {display}
      </span>
    )
  }

  return (
    <div style={{ display: 'flex', gap: '1rem' }}>
      {/* ═══ MAIN COLUMN ═══ */}
      <div style={{ flex: 1, minWidth: 0 }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>CRM</h1>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Pipeline: <strong>{fmtPrice(pipelineValue)}</strong></span>
            <a href={exportUrl} className="btn btn-sm" style={{ textDecoration: 'none' }}>Export CSV</a>
          </div>
        </div>

        {/* Follow-up reminders panel */}
        {urgentFollowUps.length > 0 && (
          <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem' }}>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#92400e', marginBottom: 6 }}>
              {urgentFollowUps.length} client{urgentFollowUps.length !== 1 ? 's' : ''} need{urgentFollowUps.length === 1 ? 's' : ''} follow up
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {urgentFollowUps.slice(0, 5).map((l: any) => (
                <div key={l.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span><strong>{l.name}</strong> — <span style={{ color: l.action_required?.includes('overdue') ? 'var(--color-danger)' : '#92400e' }}>{l.action_required}</span></span>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-sm btn-primary" onClick={() => handleAction(l.id, l.action_required)}>
                      {l.action_required === 'Contact' ? 'Contact' : 'Mark done'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* NL Quick-add */}
        <form onSubmit={handleQuickAdd} style={{ display: 'flex', gap: 6, marginBottom: '0.75rem' }}>
          <input style={{ flex: 1, padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: '0.9rem' }}
            placeholder='Quick add: "John Smith - wants quote for wedding"'
            value={nlText} onChange={e => setNlText(e.target.value)} />
          <button type="submit" className="btn btn-primary" disabled={nlLoading} style={{ whiteSpace: 'nowrap' }}>{nlLoading ? '…' : 'Add'}</button>
        </form>

        {/* Filter bar + view toggle */}
        <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {[{ l: 'All', v: 'ALL' }, { l: 'New', v: 'NEW' }, { l: 'Contacted', v: 'CONTACTED' }, { l: 'Qualified', v: 'QUALIFIED' }, { l: 'Converted', v: 'CONVERTED' }, { l: 'Lost', v: 'LOST' }].map(f => (
            <button key={f.v} className={`filter-pill ${filter === f.v ? 'active' : ''}`} onClick={() => setFilter(f.v)}>{f.l}</button>
          ))}
          <span style={{ width: 1, height: 18, background: 'var(--color-border)', margin: '0 4px' }} />
          <button className={`filter-pill ${viewMode === 'table' ? 'active' : ''}`} onClick={() => setViewMode('table')}>Table</button>
          <button className={`filter-pill ${viewMode === 'pipeline' ? 'active' : ''}`} onClick={() => setViewMode('pipeline')}>Pipeline</button>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
            <input placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)}
              style={{ padding: '0.35rem 0.6rem', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: '0.8rem', width: 160 }} />
            <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(!showAdd)}>{showAdd ? 'Cancel' : '+ Add Lead'}</button>
          </div>
        </div>

        {/* Add lead form */}
        {showAdd && (
          <form onSubmit={handleAddLead} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <div><label className="form-label">Name *</label><input className="form-input" name="name" required /></div>
              <div><label className="form-label">Email</label><input className="form-input" name="email" type="email" /></div>
              <div><label className="form-label">Phone</label><input className="form-input" name="phone" /></div>
              <div><label className="form-label">Source</label>
                <select className="form-input" name="source">
                  <option value="manual">Manual</option><option value="website">Website</option><option value="referral">Referral</option>
                  <option value="social">Social</option><option value="booking">Booking</option><option value="other">Other</option>
                </select>
              </div>
              <div><label className="form-label">Value (£)</label><input className="form-input" name="value" type="number" step="0.01" defaultValue="0" /></div>
              <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: '0.85rem' }}><input type="checkbox" name="consent" /> GDPR Consent</label>
              </div>
              <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Notes</label><input className="form-input" name="notes" /></div>
            </div>
            <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Add Lead</button></div>
          </form>
        )}

        {/* ═══ TABLE VIEW ═══ */}
        {viewMode === 'table' && (
          filtered.length === 0 ? (
            <div className="empty-cta"><div className="empty-cta-title">No leads match</div><div className="empty-cta-desc">Add a lead above or adjust filters.</div></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '22%' }}>Who</th>
                    <th style={{ width: '10%' }}>Value</th>
                    <th style={{ width: '18%' }}>Action Required</th>
                    <th style={{ width: '10%' }}>Score</th>
                    <th style={{ width: '10%' }}>Follow Up</th>
                    <th style={{ width: '10%' }}>Status</th>
                    <th style={{ width: '10%' }}>Source</th>
                    <th style={{ width: '10%' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(l => {
                    const actionStyle = ACTION_COLORS[l.action_required] || { bg: '#f3f4f6', color: '#6b7280', border: '#d1d5db' }
                    const scoreBadge = SCORE_BADGE[l.client_score_label] || SCORE_BADGE.Low
                    const isOverdue = l.follow_up_date && new Date(l.follow_up_date + 'T00:00:00') < new Date(new Date().toISOString().split('T')[0] + 'T00:00:00')
                    const isToday = l.follow_up_date === new Date().toISOString().split('T')[0]

                    return (
                      <tr key={l.id}
                        onClick={() => { setSelected(l); setPanelTab('details') }}
                        style={{
                          cursor: 'pointer',
                          background: selected?.id === l.id ? '#f0f9ff' : isOverdue ? '#fef2f2' : isToday ? '#fffbeb' : undefined,
                        }}>
                        <td>
                          <div style={{ fontWeight: 600 }}>
                            <EditableCell lead={l} field="name" display={l.name} />
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'flex', gap: 8, marginTop: 2 }}>
                            {l.email && <a href={`mailto:${l.email}`} onClick={e => e.stopPropagation()} style={{ color: 'var(--color-primary)' }} title="Email">{l.email}</a>}
                            {l.phone && <a href={`tel:${l.phone}`} onClick={e => e.stopPropagation()} style={{ color: 'var(--color-primary)' }} title="Call">{l.phone}</a>}
                          </div>
                        </td>
                        <td>
                          <EditableCell lead={l} field="value_pence" display={<span style={{ fontWeight: 600 }}>{fmtPrice(l.value_pence)}</span>} />
                        </td>
                        <td>
                          {l.action_required ? (
                            <span style={{ padding: '3px 8px', borderRadius: 6, fontSize: '0.75rem', fontWeight: 700, background: actionStyle.bg, color: actionStyle.color, border: `1px solid ${actionStyle.border}` }}>
                              {l.action_required}
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>—</span>
                          )}
                        </td>
                        <td>
                          <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700, background: scoreBadge.bg, color: scoreBadge.color }}>
                            {l.client_score_label}
                          </span>
                        </td>
                        <td>
                          <EditableCell lead={l} field="follow_up_date" type="date"
                            display={<span style={{ fontSize: '0.8rem', color: isOverdue ? 'var(--color-danger)' : isToday ? '#92400e' : 'var(--color-text-muted)', fontWeight: isOverdue || isToday ? 700 : 400 }}>{fmtDate(l.follow_up_date)}</span>} />
                        </td>
                        <td>
                          <EditableCell lead={l} field="status"
                            display={<span className={`badge ${STATUS_BADGE[l.status] || 'badge-neutral'}`}>{l.status}</span>} />
                        </td>
                        <td>
                          <EditableCell lead={l} field="source"
                            display={<span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{l.source}</span>} />
                        </td>
                        <td onClick={e => e.stopPropagation()}>
                          {l.action_required && (
                            <button className={`btn btn-sm ${l.action_required.includes('overdue') ? 'btn-danger' : 'btn-primary'}`}
                              onClick={() => handleAction(l.id, l.action_required)}>
                              {l.action_required === 'Contact' ? 'Contact now' : l.action_required === 'Convert' ? 'Convert' : 'Done'}
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )
        )}

        {/* ═══ PIPELINE VIEW ═══ */}
        {viewMode === 'pipeline' && (
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${PIPELINE_COLS.length}, 1fr)`, gap: '0.75rem', minHeight: 300 }}>
            {PIPELINE_COLS.map(col => {
              const colLeads = leads.filter(l => l.status === col)
              return (
                <div key={col}
                  onDragOver={e => e.preventDefault()}
                  onDrop={e => { const id = parseInt(e.dataTransfer.getData('leadId')); if (id) handlePipelineDrop(id, col) }}
                  style={{ background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 8, padding: '0.75rem', minHeight: 200 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>{col}</span>
                    <span className={`badge ${STATUS_BADGE[col]}`} style={{ fontSize: '0.65rem' }}>{colLeads.length}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {colLeads.map(l => (
                      <div key={l.id} draggable
                        onDragStart={e => e.dataTransfer.setData('leadId', String(l.id))}
                        onClick={() => { setSelected(l); setPanelTab('details') }}
                        style={{
                          background: '#fff', border: '1px solid var(--color-border)', borderRadius: 6,
                          padding: '0.5rem 0.65rem', cursor: 'grab', fontSize: '0.85rem',
                        }}>
                        <div style={{ fontWeight: 600, marginBottom: 2 }}>{l.name}</div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{fmtPrice(l.value_pence)}</span>
                          {l.action_required && (
                            <span style={{ fontSize: '0.65rem', padding: '1px 5px', borderRadius: 4, background: (ACTION_COLORS[l.action_required] || ACTION_COLORS.Contact).bg, color: (ACTION_COLORS[l.action_required] || ACTION_COLORS.Contact).color }}>
                              {l.action_required}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ═══ SIDE PANEL ═══ */}
      {selected && (
        <div style={{ width: 320, flexShrink: 0, background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', alignSelf: 'flex-start', position: 'sticky', top: '1rem', maxHeight: 'calc(100vh - 2rem)', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>{selected.name}</h3>
              <span className={`badge ${STATUS_BADGE[selected.status]}`} style={{ marginTop: 4 }}>{selected.status}</span>
            </div>
            <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--color-text-muted)' }}>×</button>
          </div>

          {/* Contact details */}
          <div style={{ fontSize: '0.85rem', marginBottom: '0.75rem' }}>
            {selected.email && <div style={{ marginBottom: 4 }}><a href={`mailto:${selected.email}`} style={{ color: 'var(--color-primary)' }}>{selected.email}</a></div>}
            {selected.phone && <div style={{ marginBottom: 4 }}><a href={`tel:${selected.phone}`} style={{ color: 'var(--color-primary)' }}>{selected.phone}</a></div>}
            <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
              {selected.email && <a href={`mailto:${selected.email}`} className="btn btn-sm" style={{ textDecoration: 'none', fontSize: '0.75rem' }}>Email</a>}
              {selected.phone && <a href={`tel:${selected.phone}`} className="btn btn-sm" style={{ textDecoration: 'none', fontSize: '0.75rem' }}>Call</a>}
            </div>
          </div>

          {/* Key info */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.8rem', marginBottom: '0.75rem', padding: '0.5rem', background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 6 }}>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Value:</span> <strong>{fmtPrice(selected.value_pence)}</strong></div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Score:</span> <strong>{selected.client_score_label}</strong></div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Source:</span> {selected.source}</div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Follow up:</span> {fmtDate(selected.follow_up_date)}</div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Consent:</span> {selected.marketing_consent ? '✓ Yes' : 'No'}</div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Created:</span> {fmtDate(selected.created_at?.split('T')[0])}</div>
          </div>

          {/* Action button */}
          {selected.action_required && (
            <button className={`btn ${selected.action_required.includes('overdue') ? 'btn-danger' : 'btn-primary'}`}
              style={{ width: '100%', marginBottom: '0.75rem' }}
              onClick={() => handleAction(selected.id, selected.action_required)}>
              {selected.action_required === 'Contact' ? 'Contact now' : selected.action_required === 'Convert' ? 'Convert to client' : 'Mark follow-up done'}
            </button>
          )}

          {/* Panel tabs */}
          <div className="tabs" style={{ marginBottom: '0.5rem' }}>
            {(['details', 'notes', 'history'] as const).map(t => (
              <button key={t} className={`tab ${panelTab === t ? 'active' : ''}`} onClick={() => setPanelTab(t)} style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
                {t === 'details' ? 'Details' : t === 'notes' ? 'Notes' : 'History'}
              </button>
            ))}
          </div>

          {/* Details tab */}
          {panelTab === 'details' && (
            <div style={{ fontSize: '0.85rem' }}>
              {selected.notes && <div style={{ marginBottom: 8 }}><span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>Notes:</span><div>{selected.notes}</div></div>}
              {selected.tags && <div style={{ marginBottom: 8 }}><span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>Tags:</span> {selected.tags}</div>}
              {selected.last_contact_date && <div><span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>Last contact:</span> {fmtDate(selected.last_contact_date)}</div>}
            </div>
          )}

          {/* Notes tab */}
          {panelTab === 'notes' && (
            <div>
              <div style={{ display: 'flex', gap: 4, marginBottom: '0.5rem' }}>
                <input className="form-input" style={{ flex: 1, fontSize: '0.8rem', padding: '0.3rem 0.5rem' }}
                  placeholder="Add a note…" value={newNote} onChange={e => setNewNote(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleAddNote() }} />
                <button className="btn btn-sm btn-primary" onClick={handleAddNote}>Add</button>
              </div>
              {notes.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '1rem 0' }}>No notes yet</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  {notes.map((n: any) => (
                    <div key={n.id} style={{ padding: '0.4rem 0.5rem', background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 6, fontSize: '0.8rem' }}>
                      <div>{n.text}</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{new Date(n.created_at).toLocaleString('en-GB')}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* History tab */}
          {panelTab === 'history' && (
            <div>
              {history.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '1rem 0' }}>No history yet</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {history.map((h: any) => (
                    <div key={h.id} style={{ padding: '0.35rem 0.5rem', borderLeft: '3px solid var(--color-primary)', fontSize: '0.8rem' }}>
                      <div style={{ fontWeight: 600 }}>{h.action}</div>
                      {h.detail && <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{h.detail}</div>}
                      <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>{new Date(h.created_at).toLocaleString('en-GB')}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', bottom: '2rem', left: '50%', transform: 'translateX(-50%)', padding: '0.5rem 1.25rem', borderRadius: 6, backgroundColor: '#111827', color: '#fff', fontSize: '0.82rem', fontWeight: 500, zIndex: 1001 }}>
          {toast}
        </div>
      )}
    </div>
  )
}
