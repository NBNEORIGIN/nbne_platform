'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  getWiggumDashboard, completeComplianceItem, deleteComplianceItem,
  createComplianceItem, parseComplianceCommand,
  getIncidents, createIncident, updateIncidentStatus,
  getAccidents, createAccident,
  getComplianceDocuments, getRams,
} from '@/lib/api'

type View = 'active' | 'sorted'
type Tab = 'today' | 'register' | 'incidents' | 'accidents' | 'documents'

const BANNER_STYLES: Record<string, { bg: string; border: string; color: string; icon: string }> = {
  green: { bg: '#f0fdf4', border: '#22c55e', color: '#15803d', icon: '✓' },
  amber: { bg: '#fffbeb', border: '#f59e0b', color: '#92400e', icon: '!' },
  red:   { bg: '#fef2f2', border: '#ef4444', color: '#991b1b', icon: '✕' },
}

export default function HealthSafetyPage() {
  const [tab, setTab] = useState<Tab>('today')
  const [view, setView] = useState<View>('active')
  const [loading, setLoading] = useState(true)
  const [wiggum, setWiggum] = useState<any>(null)
  const [selectedItem, setSelectedItem] = useState<any>(null)

  // NL input
  const [nlText, setNlText] = useState('')
  const [nlResult, setNlResult] = useState<any>(null)
  const [nlLoading, setNlLoading] = useState(false)

  // Register
  const [showAddItem, setShowAddItem] = useState(false)
  const [itemForm, setItemForm] = useState({ title: '', category: '', item_type: 'LEGAL', frequency_type: 'annual', next_due_date: '', notes: '', plain_english_why: '' })

  // Incidents
  const [incidents, setIncidents] = useState<any[]>([])
  const [showAddInc, setShowAddInc] = useState(false)

  // Accidents
  const [accidents, setAccidents] = useState<any[]>([])
  const [showAddAcc, setShowAddAcc] = useState(false)

  // Documents
  const [docs, setDocs] = useState<any[]>([])
  const [rams, setRams] = useState<any[]>([])

  const loadAll = useCallback(async () => {
    setLoading(true)
    const [w, inc, acc, dc, rm] = await Promise.all([
      getWiggumDashboard(),
      getIncidents(),
      getAccidents(),
      getComplianceDocuments(),
      getRams(),
    ])
    if (w.data) setWiggum(w.data)
    if (inc.data) setIncidents(inc.data)
    if (acc.data) setAccidents(acc.data)
    if (dc.data) setDocs(dc.data)
    if (rm.data) setRams(rm.data)
    setLoading(false)
  }, [])

  useEffect(() => { loadAll() }, [loadAll])

  async function handleComplete(id: number) {
    await completeComplianceItem(id)
    setSelectedItem(null)
    loadAll()
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this compliance item?')) return
    await deleteComplianceItem(id)
    loadAll()
  }

  async function handleAddItem(e: React.FormEvent) {
    e.preventDefault()
    if (!itemForm.title.trim()) return
    await createComplianceItem(itemForm)
    setShowAddItem(false)
    setItemForm({ title: '', category: '', item_type: 'LEGAL', frequency_type: 'annual', next_due_date: '', notes: '', plain_english_why: '' })
    loadAll()
  }

  async function handleNlSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!nlText.trim()) return
    setNlLoading(true)
    const res = await parseComplianceCommand(nlText)
    setNlResult(res.data)
    setNlLoading(false)
    if (res.data?.action === 'complete' && res.data?.item_id) {
      setSelectedItem(wiggum?.action_items?.find((a: any) => a.id === res.data.item_id) || null)
    }
  }

  async function handleNlConfirm() {
    if (nlResult?.action === 'complete' && nlResult?.item_id) {
      await completeComplianceItem(nlResult.item_id)
      setNlResult(null)
      setNlText('')
      loadAll()
    }
  }

  async function handleAddIncident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createIncident({
      title: fd.get('title'), description: fd.get('description'),
      severity: fd.get('severity'), location: fd.get('location'),
      incident_date: new Date().toISOString(),
      riddor_reportable: fd.get('riddor') === 'on',
    })
    setShowAddInc(false)
    loadAll()
  }

  async function handleAddAccident(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    await createAccident({
      date: fd.get('date'), time: fd.get('time') || null,
      location: fd.get('location'), person_involved: fd.get('person_involved'),
      person_role: fd.get('person_role'), description: fd.get('description'),
      severity: fd.get('severity'), riddor_reportable: fd.get('riddor') === 'on',
      reported_by: fd.get('reported_by'),
    })
    setShowAddAcc(false)
    loadAll()
  }

  if (loading) return <div className="empty-state">Loading…</div>

  const w = wiggum || { status_level: 'green', status_message: 'Loading…', action_items: [], sorted_items: [], counts: {}, score: 0, score_label: 'Safe' }
  const banner = BANNER_STYLES[w.status_level] || BANNER_STYLES.green
  const openInc = incidents.filter(i => i.status === 'OPEN' || i.status === 'INVESTIGATING')
  const openAcc = accidents.filter(a => a.status !== 'CLOSED')

  // Merged documents
  const allDocs = [
    ...docs.map(d => ({ ...d, source: 'vault' })),
    ...rams.map(r => ({ id: `rams-${r.id}`, title: r.title, document_type: 'rams', is_current: r.status === 'ACTIVE', is_expired: r.status === 'EXPIRED', expiry_date: r.expiry_date, source: 'rams' })),
  ]

  const TABS: { key: Tab; label: string; badge?: number }[] = [
    { key: 'today', label: 'Today', badge: w.action_items?.length || 0 },
    { key: 'register', label: 'Register' },
    { key: 'incidents', label: 'Incidents', badge: openInc.length },
    { key: 'accidents', label: 'Accidents', badge: openAcc.length },
    { key: 'documents', label: 'Documents' },
  ]

  return (
    <div>
      {/* ═══ HEADER ═══ */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Health &amp; Safety — Today</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{w.score_label}</span>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: banner.color }}>{w.score}%</span>
        </div>
      </div>

      {/* ═══ STATUS BANNER ═══ */}
      <div style={{
        background: banner.bg, borderLeft: `5px solid ${banner.border}`,
        padding: '1rem 1.25rem', borderRadius: 8, marginBottom: '1.25rem',
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: '1.5rem', fontWeight: 800, color: banner.color, lineHeight: 1 }}>{banner.icon}</span>
        <span style={{ fontSize: '1.05rem', fontWeight: 600, color: banner.color }}>{w.status_message}</span>
      </div>

      {/* ═══ NATURAL LANGUAGE INPUT ═══ */}
      <form onSubmit={handleNlSubmit} style={{ marginBottom: '1.25rem', display: 'flex', gap: 8 }}>
        <input
          style={{ flex: 1, padding: '0.6rem 0.9rem', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: '0.95rem' }}
          placeholder="Type a command… e.g. &quot;Upload fire risk assessment&quot; or &quot;Log accident Ben cut hand&quot;"
          value={nlText} onChange={e => setNlText(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={nlLoading} style={{ whiteSpace: 'nowrap' }}>
          {nlLoading ? '…' : 'Go'}
        </button>
      </form>

      {nlResult && (
        <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.9rem' }}>{nlResult.message}</span>
          <div style={{ display: 'flex', gap: 6 }}>
            {nlResult.action === 'complete' && nlResult.item_id && (
              <button className="btn btn-sm btn-primary" onClick={handleNlConfirm}>Yes, mark complete</button>
            )}
            <button className="btn btn-sm" onClick={() => { setNlResult(null); setNlText('') }}>Dismiss</button>
          </div>
        </div>
      )}

      {/* ═══ TABS ═══ */}
      <div className="tabs" style={{ marginBottom: '1rem' }}>
        {TABS.map(t => (
          <button key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
            {(t.badge ?? 0) > 0 && t.key !== 'today' && (
              <span style={{ marginLeft: 6, background: 'var(--color-danger)', color: '#fff', borderRadius: 999, padding: '1px 6px', fontSize: '0.7rem', fontWeight: 700 }}>{t.badge}</span>
            )}
          </button>
        ))}
      </div>

      {/* ═══════════════════════════════════════════ */}
      {/* ═══ TODAY TAB — WIGGUM LOOP ═══ */}
      {/* ═══════════════════════════════════════════ */}
      {tab === 'today' && (
        <div>
          {/* Active / Sorted toggle */}
          <div style={{ display: 'flex', gap: 4, marginBottom: '1rem' }}>
            <button className={`filter-pill ${view === 'active' ? 'active' : ''}`} onClick={() => setView('active')}>Active</button>
            <button className={`filter-pill ${view === 'sorted' ? 'active' : ''}`} onClick={() => setView('sorted')}>Sorted</button>
          </div>

          {view === 'active' ? (
            /* ── ACTION TABLE ── */
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                {w.action_items.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-success)' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>Sorted</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>Nothing needs doing right now.</div>
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th style={{ width: '30%' }}>What</th>
                          <th style={{ width: '25%' }}>Why it matters</th>
                          <th style={{ width: '15%' }}>When</th>
                          <th style={{ width: '15%' }}>Do this</th>
                          <th style={{ width: '15%' }}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {w.action_items.map((a: any) => (
                          <tr key={a.id} onClick={() => setSelectedItem(a)} style={{ cursor: 'pointer', background: selectedItem?.id === a.id ? '#f0f9ff' : undefined }}>
                            <td>
                              <div style={{ fontWeight: 600 }}>{a.what}</div>
                              {a.item_type === 'LEGAL' && <span style={{ fontSize: '0.7rem', color: 'var(--color-danger)', fontWeight: 600 }}>Legal requirement</span>}
                            </td>
                            <td style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{a.why}</td>
                            <td>
                              <span style={{ fontSize: '0.85rem', fontWeight: a.status === 'OVERDUE' ? 700 : 400, color: a.status === 'OVERDUE' ? 'var(--color-danger)' : undefined }}>
                                {a.days_info || '—'}
                              </span>
                            </td>
                            <td>
                              <button className={`btn btn-sm ${a.status === 'OVERDUE' && a.item_type === 'LEGAL' ? 'btn-danger' : 'btn-primary'}`}
                                onClick={(e) => { e.stopPropagation(); handleComplete(a.id) }}>
                                {a.do_this}
                              </button>
                            </td>
                            <td>
                              <button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); handleDelete(a.id) }} style={{ opacity: 0.5 }}>Del</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* ── GUIDANCE PANEL ── */}
              {selectedItem && (
                <div style={{ width: 300, flexShrink: 0, background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1.25rem' }}>
                  <h3 style={{ fontSize: '0.95rem', marginBottom: 8, color: 'var(--color-text)' }}>What this means</h3>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>{selectedItem.what}</div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: 12 }}>
                    {selectedItem.plain_english_why || selectedItem.why}
                  </p>
                  {selectedItem.description && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', lineHeight: 1.4, marginBottom: 12 }}>
                      {selectedItem.description}
                    </p>
                  )}
                  {selectedItem.legal_reference && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontStyle: 'italic', marginBottom: 12 }}>
                      Ref: {selectedItem.legal_reference}
                    </p>
                  )}
                  <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => handleComplete(selectedItem.id)}>
                    {selectedItem.do_this}
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* ── SORTED VIEW ── */
            <div>
              {w.sorted_items.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted)' }}>
                  <div style={{ fontSize: '1.1rem', marginBottom: 4 }}>Nothing completed recently</div>
                  <div style={{ fontSize: '0.85rem' }}>Items you complete will appear here.</div>
                </div>
              ) : (
                <div>
                  {w.sorted_items.filter((s: any) => s.when === 'today').length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h3 style={{ fontSize: '0.95rem', color: 'var(--color-success)', marginBottom: 8 }}>Completed today</h3>
                      {w.sorted_items.filter((s: any) => s.when === 'today').map((s: any) => (
                        <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
                          <span style={{ color: 'var(--color-success)', fontWeight: 700 }}>✓</span>
                          <span style={{ fontWeight: 500 }}>{s.title}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>{s.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {w.sorted_items.filter((s: any) => s.when !== 'today').length > 0 && (
                    <div>
                      <h3 style={{ fontSize: '0.95rem', color: 'var(--color-text-muted)', marginBottom: 8 }}>This week</h3>
                      {w.sorted_items.filter((s: any) => s.when !== 'today').map((s: any) => (
                        <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
                          <span style={{ color: 'var(--color-success)' }}>✓</span>
                          <span>{s.title}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>{s.when}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ═══════ REGISTER TAB ═══════ */}
      {tab === 'register' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
            <button className="btn btn-primary" onClick={() => setShowAddItem(!showAddItem)}>{showAddItem ? 'Cancel' : '+ Add Item'}</button>
          </div>

          {showAddItem && (
            <form onSubmit={handleAddItem} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Title *</label><input className="form-input" value={itemForm.title} onChange={e => setItemForm({ ...itemForm, title: e.target.value })} required /></div>
                <div><label className="form-label">Category</label><input className="form-input" value={itemForm.category} onChange={e => setItemForm({ ...itemForm, category: e.target.value })} placeholder="e.g. Fire Safety" /></div>
                <div><label className="form-label">Type</label><select className="form-input" value={itemForm.item_type} onChange={e => setItemForm({ ...itemForm, item_type: e.target.value })}><option value="LEGAL">Legal Requirement</option><option value="BEST_PRACTICE">Best Practice</option></select></div>
                <div><label className="form-label">Frequency</label><select className="form-input" value={itemForm.frequency_type} onChange={e => setItemForm({ ...itemForm, frequency_type: e.target.value })}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option><option value="biennial">Every 2 Years</option><option value="5_year">Every 5 Years</option><option value="ad_hoc">Ad Hoc</option></select></div>
                <div><label className="form-label">Next Due Date</label><input className="form-input" type="date" value={itemForm.next_due_date} onChange={e => setItemForm({ ...itemForm, next_due_date: e.target.value })} /></div>
                <div><label className="form-label">Why it matters</label><input className="form-input" value={itemForm.plain_english_why} onChange={e => setItemForm({ ...itemForm, plain_english_why: e.target.value })} placeholder="Plain English explanation" /></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary">Add Item</button>
              </div>
            </form>
          )}

          {(w.counts?.total || 0) === 0 && !showAddItem ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No compliance items yet</div>
              <div className="empty-cta-desc">Add your first item or run the UK starter checklist from the backend.</div>
              <button className="btn btn-primary" onClick={() => setShowAddItem(true)}>+ Add Item</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>What</th><th>Type</th><th>Frequency</th><th>Status</th><th>Next Due</th><th></th></tr></thead>
                <tbody>
                  {w.action_items.concat(
                    (wiggum as any)?._all_items || []
                  ).length === 0 && (
                    <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>All items shown in Today tab</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ INCIDENTS TAB ═══════ */}
      {tab === 'incidents' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
            <button className="btn btn-primary" onClick={() => setShowAddInc(!showAddInc)}>{showAddInc ? 'Cancel' : '+ Report Incident'}</button>
          </div>

          {showAddInc && (
            <form onSubmit={handleAddIncident} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Title *</label><input className="form-input" name="title" required /></div>
                <div><label className="form-label">Location</label><input className="form-input" name="location" /></div>
                <div><label className="form-label">Severity</label><select className="form-input" name="severity"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option></select></div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" name="riddor" /> RIDDOR Reportable</label></div>
                <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Description *</label><textarea className="form-input" name="description" required rows={3} /></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Submit</button></div>
            </form>
          )}

          {incidents.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No incidents</div>
              <div className="empty-cta-desc">Report incidents as they happen.</div>
              <button className="btn btn-primary" onClick={() => setShowAddInc(true)}>+ Report Incident</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Incident</th><th>Severity</th><th>RIDDOR</th><th>Date</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {incidents.map(inc => (
                    <tr key={inc.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{inc.title}</div>
                        {inc.location && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{inc.location}</div>}
                      </td>
                      <td><span className={`badge ${inc.severity === 'HIGH' || inc.severity === 'CRITICAL' ? 'badge-danger' : inc.severity === 'MEDIUM' ? 'badge-warning' : 'badge-info'}`}>{inc.severity}</span></td>
                      <td>{inc.riddor_reportable ? <span className="badge badge-danger">Yes</span> : <span style={{ color: 'var(--color-text-muted)' }}>No</span>}</td>
                      <td style={{ fontSize: '0.85rem' }}>{inc.incident_date ? new Date(inc.incident_date).toLocaleDateString() : '—'}</td>
                      <td><span className={`badge ${inc.status === 'OPEN' ? 'badge-danger' : inc.status === 'INVESTIGATING' ? 'badge-warning' : 'badge-success'}`}>{inc.status}</span></td>
                      <td>{(inc.status === 'OPEN' || inc.status === 'INVESTIGATING') && <button className="btn btn-sm" onClick={() => updateIncidentStatus(inc.id, 'RESOLVED').then(loadAll)}>Resolve</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ ACCIDENTS TAB ═══════ */}
      {tab === 'accidents' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
            <button className="btn btn-primary" onClick={() => setShowAddAcc(!showAddAcc)}>{showAddAcc ? 'Cancel' : '+ Log Accident'}</button>
          </div>

          {showAddAcc && (
            <form onSubmit={handleAddAccident} style={{ background: 'var(--color-bg-alt, #f9fafb)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label className="form-label">Date *</label><input className="form-input" name="date" type="date" required defaultValue={new Date().toISOString().split('T')[0]} /></div>
                <div><label className="form-label">Time</label><input className="form-input" name="time" type="time" /></div>
                <div><label className="form-label">Person Involved *</label><input className="form-input" name="person_involved" required /></div>
                <div><label className="form-label">Role</label><select className="form-input" name="person_role"><option value="Staff">Staff</option><option value="Client">Client</option><option value="Visitor">Visitor</option><option value="Contractor">Contractor</option></select></div>
                <div><label className="form-label">Location</label><input className="form-input" name="location" /></div>
                <div><label className="form-label">Severity</label><select className="form-input" name="severity"><option value="MINOR">Minor</option><option value="MODERATE">Moderate</option><option value="MAJOR">Major</option><option value="FATAL">Fatal</option></select></div>
                <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Description *</label><textarea className="form-input" name="description" required rows={3} /></div>
                <div><label className="form-label">Reported By</label><input className="form-input" name="reported_by" /></div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" name="riddor" /> RIDDOR Reportable</label></div>
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}><button type="submit" className="btn btn-primary">Log Accident</button></div>
            </form>
          )}

          {accidents.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No accidents logged</div>
              <div className="empty-cta-desc">Log workplace accidents here.</div>
              <button className="btn btn-primary" onClick={() => setShowAddAcc(true)}>+ Log Accident</button>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Person</th><th>Severity</th><th>RIDDOR</th><th>Date</th><th>Status</th></tr></thead>
                <tbody>
                  {accidents.map(a => (
                    <tr key={a.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{a.person_involved}</div>
                        {a.location && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{a.location}</div>}
                      </td>
                      <td><span className={`badge ${a.severity === 'MAJOR' || a.severity === 'FATAL' ? 'badge-danger' : a.severity === 'MODERATE' ? 'badge-warning' : 'badge-info'}`}>{a.severity}</span></td>
                      <td>{a.riddor_reportable ? <span className="badge badge-danger">Yes</span> : <span style={{ color: 'var(--color-text-muted)' }}>No</span>}</td>
                      <td style={{ fontSize: '0.85rem' }}>{a.date}</td>
                      <td><span className={`badge ${a.status === 'CLOSED' ? 'badge-info' : 'badge-warning'}`}>{a.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ DOCUMENTS TAB ═══════ */}
      {tab === 'documents' && (
        <div>
          {allDocs.length === 0 ? (
            <div className="empty-cta">
              <div className="empty-cta-title">No documents</div>
              <div className="empty-cta-desc">Policies, certificates, insurance documents and RAMS will appear here.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
              {allDocs.map(doc => (
                <div key={doc.id} style={{ background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8, padding: '1rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{doc.title}</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
                    <span className={`badge ${doc.is_expired ? 'badge-danger' : 'badge-success'}`}>{doc.is_expired ? 'Expired' : 'Current'}</span>
                    <span className="badge badge-neutral">{(doc.document_type || '').replace(/_/g, ' ')}</span>
                  </div>
                  {doc.expiry_date && <div style={{ fontSize: '0.8rem', color: doc.is_expired ? 'var(--color-danger)' : 'var(--color-text-muted)' }}>{doc.is_expired ? 'Expired' : 'Expires'}: {doc.expiry_date}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
