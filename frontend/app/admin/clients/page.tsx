'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  getLeads, createLead, updateLead, deleteLead, quickAddLead,
  actionContact, actionConvert, actionFollowupDone,
  getLeadNotes, addLeadNote, getLeadHistory,
  getLeadMessages, addLeadMessage, parseEmailForLead, parseEmailCreateLead, extractEmailDetails,
  getRevenueStats, getLeadRevenue,
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

const SOURCE_LABELS: Record<string, string> = {
  booking: 'Booking', website: 'Website', referral: 'Referral',
  social: 'Social', manual: 'Manual', other: 'Other',
}
const FUNNEL_COLORS: Record<string, string> = {
  NEW: '#3b82f6', CONTACTED: '#f59e0b', QUALIFIED: '#8b5cf6', CONVERTED: '#22c55e', LOST: '#ef4444',
}

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
  const [messages, setMessages] = useState<any[]>([])
  const [newNote, setNewNote] = useState('')
  const [panelTab, setPanelTab] = useState<'details' | 'activity' | 'history' | 'revenue'>('details')

  // Activity message composer
  const [msgType, setMsgType] = useState<string>('note')
  const [msgBody, setMsgBody] = useState('')
  const [msgSubject, setMsgSubject] = useState('')

  // AI Email analyzer
  const [showAnalyzer, setShowAnalyzer] = useState(false)
  const [analyzerText, setAnalyzerText] = useState('')
  const [analyzerLoading, setAnalyzerLoading] = useState(false)
  const [analyzerResult, setAnalyzerResult] = useState<any>(null)

  // Inline editing
  const [editingCell, setEditingCell] = useState<{ id: number; field: string } | null>(null)
  const [editValue, setEditValue] = useState('')

  // Add lead form
  const [showAdd, setShowAdd] = useState(false)
  const [addEnquiry, setAddEnquiry] = useState('')
  const [addExtracting, setAddExtracting] = useState(false)
  const [addName, setAddName] = useState('')
  const [addEmail, setAddEmail] = useState('')
  const [addPhone, setAddPhone] = useState('')
  const [addSource, setAddSource] = useState('manual')
  const [addValue, setAddValue] = useState('0')
  const [addNotes, setAddNotes] = useState('')
  const [addConsent, setAddConsent] = useState(false)
  const [addExtracted, setAddExtracted] = useState<any>(null)

  // Revenue tracking
  const [revStats, setRevStats] = useState<any>(null)
  const [leadRev, setLeadRev] = useState<any>(null)
  const [showRevenue, setShowRevenue] = useState(false)

  const flash = useCallback((msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2500) }, [])

  const reload = useCallback(async () => {
    const r = await getLeads()
    setLeads(r.data || [])
    setLoading(false)
  }, [])

  useEffect(() => { reload() }, [reload])

  // Load revenue stats
  useEffect(() => {
    getRevenueStats().then(r => setRevStats(r.data || null))
  }, [leads.length]) // eslint-disable-line react-hooks/exhaustive-deps

  // Load notes + history + messages + revenue when selecting a lead
  useEffect(() => {
    if (!selected) return
    getLeadNotes(selected.id).then(r => setNotes(r.data || []))
    getLeadHistory(selected.id).then(r => setHistory(r.data || []))
    getLeadMessages(selected.id).then(r => setMessages(r.data || []))
    getLeadRevenue(selected.id).then(r => setLeadRev(r.data || null))
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

  async function handleDelete(id: number, name: string) {
    if (!confirm(`Delete lead "${name}"? This cannot be undone.`)) return
    await deleteLead(id)
    flash(`Deleted: ${name}`)
    if (selected?.id === id) setSelected(null)
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

  async function handleAddMessage() {
    if (!selected || !msgBody.trim()) return
    await addLeadMessage(selected.id, { message_type: msgType, subject: msgSubject, body: msgBody })
    setMsgBody(''); setMsgSubject('')
    const r = await getLeadMessages(selected.id)
    setMessages(r.data || [])
    getLeadHistory(selected.id).then(r2 => setHistory(r2.data || []))
  }

  async function handleAnalyzeEmail(mode: 'new' | 'existing') {
    if (!analyzerText.trim()) return
    setAnalyzerLoading(true)
    try {
      if (mode === 'new') {
        const r = await parseEmailCreateLead(analyzerText)
        if (!r.error) {
          setAnalyzerResult(r.data?.parsed || null)
          flash(`Lead created: ${r.data?.lead?.name}`)
          reload()
          if (r.data?.lead) { setSelected(r.data.lead); setPanelTab('activity') }
        } else {
          flash('AI parsing failed')
        }
      } else if (selected) {
        const r = await parseEmailForLead(selected.id, analyzerText)
        if (!r.error) {
          setAnalyzerResult(r.data?.parsed || null)
          flash('Email analyzed and saved')
          if (r.data?.lead) setSelected(r.data.lead)
          getLeadMessages(selected.id).then(r2 => setMessages(r2.data || []))
          reload()
        } else {
          flash('AI parsing failed')
        }
      }
    } finally {
      setAnalyzerLoading(false)
    }
  }

  function resetAddForm() {
    setAddEnquiry(''); setAddName(''); setAddEmail(''); setAddPhone('')
    setAddSource('manual'); setAddValue('0'); setAddNotes(''); setAddConsent(false); setAddExtracted(null)
  }

  async function handleAiExtract() {
    if (!addEnquiry.trim()) return
    setAddExtracting(true)
    try {
      const r = await extractEmailDetails(addEnquiry)
      if (!r.error && r.data?.parsed) {
        const p = r.data.parsed
        if (p.name) setAddName(p.name)
        if (p.email) setAddEmail(p.email)
        if (p.phone) setAddPhone(p.phone)
        if (p.source) setAddSource(p.source)
        if (p.summary) setAddNotes(p.summary)
        if (p.estimated_value) {
          try { setAddValue(String(parseFloat(String(p.estimated_value).replace(/[£,]/g, '')))) } catch {}
        }
        setAddExtracted(p)
        flash('Details extracted — review and click Add Lead')
        return
      }
      flash('AI extraction failed — fill in manually')
    } finally {
      setAddExtracting(false)
    }
  }

  async function handleAddLead(e: React.FormEvent) {
    e.preventDefault()
    if (!addName.trim()) return
    await createLead({
      name: addName, email: addEmail, phone: addPhone,
      source: addSource, value_pence: Math.round(parseFloat(addValue || '0') * 100),
      notes: addNotes, marketing_consent: addConsent,
    })
    setShowAdd(false); resetAddForm(); flash('Lead added'); reload()
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
            <button className={`filter-pill ${showRevenue ? 'active' : ''}`} onClick={() => setShowRevenue(!showRevenue)} style={{ fontSize: '0.8rem' }}>
              {showRevenue ? 'Hide Revenue' : 'Revenue'}
            </button>
            <a href={exportUrl} className="btn btn-sm" style={{ textDecoration: 'none' }}>Export CSV</a>
          </div>
        </div>

        {/* ═══ REVENUE DASHBOARD ═══ */}
        {showRevenue && revStats && (
          <div style={{ marginBottom: '1rem' }}>
            {/* KPI row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <div className="stat-card" style={{ padding: '0.6rem 0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Pipeline</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--color-primary)' }}>{fmtPrice(revStats.pipeline_value_pence)}</div>
              </div>
              <div className="stat-card" style={{ padding: '0.6rem 0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Converted Revenue</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#15803d' }}>{fmtPrice(revStats.converted_revenue_pence)}</div>
              </div>
              <div className="stat-card" style={{ padding: '0.6rem 0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Leads</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{revStats.total_leads}</div>
              </div>
              <div className="stat-card" style={{ padding: '0.6rem 0.75rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Conversion Rate</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{revStats.overall_conversion_rate}%</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              {/* Conversion Funnel */}
              <div style={{ background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 8, padding: '0.75rem' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Conversion Funnel</div>
                {revStats.funnel && (['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'] as const).map(stage => {
                  const f = revStats.funnel[stage]
                  if (!f) return null
                  const maxCount = Math.max(...Object.values(revStats.funnel).map((v: any) => v.count || 0), 1)
                  const pct = (f.count / maxCount) * 100
                  return (
                    <div key={stage} style={{ marginBottom: 6 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 2 }}>
                        <span style={{ fontWeight: 600 }}>{stage}</span>
                        <span>{f.count} leads · {fmtPrice(f.value_pence)}</span>
                      </div>
                      <div style={{ height: 8, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${pct}%`, background: FUNNEL_COLORS[stage], borderRadius: 4, transition: 'width 0.3s' }} />
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Source Attribution */}
              <div style={{ background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 8, padding: '0.75rem' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Revenue by Source</div>
                {revStats.sources && revStats.sources.length > 0 ? (
                  <table style={{ width: '100%', fontSize: '0.78rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <th style={{ textAlign: 'left', padding: '2px 4px', fontWeight: 600 }}>Source</th>
                        <th style={{ textAlign: 'right', padding: '2px 4px', fontWeight: 600 }}>Leads</th>
                        <th style={{ textAlign: 'right', padding: '2px 4px', fontWeight: 600 }}>Conv.</th>
                        <th style={{ textAlign: 'right', padding: '2px 4px', fontWeight: 600 }}>Rate</th>
                        <th style={{ textAlign: 'right', padding: '2px 4px', fontWeight: 600 }}>Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {revStats.sources.map((s: any) => (
                        <tr key={s.source} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '3px 4px', fontWeight: 500 }}>{SOURCE_LABELS[s.source] || s.source}</td>
                          <td style={{ padding: '3px 4px', textAlign: 'right' }}>{s.leads}</td>
                          <td style={{ padding: '3px 4px', textAlign: 'right' }}>{s.converted}</td>
                          <td style={{ padding: '3px 4px', textAlign: 'right', color: s.conversion_rate >= 50 ? '#15803d' : s.conversion_rate >= 20 ? '#854d0e' : 'var(--color-text-muted)' }}>{s.conversion_rate}%</td>
                          <td style={{ padding: '3px 4px', textAlign: 'right', fontWeight: 600 }}>{fmtPrice(s.revenue_pence)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '1rem 0' }}>No source data yet</div>
                )}
              </div>
            </div>
          </div>
        )}

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
            {/* Enquiry notes + AI extract */}
            <div style={{ marginBottom: 10 }}>
              <label className="form-label" style={{ fontWeight: 700 }}>Enquiry Notes (Verbal or Written)</label>
              <textarea className="form-input" rows={3} style={{ width: '100%', resize: 'vertical' }}
                placeholder="Paste or type the enquiry details here…"
                value={addEnquiry} onChange={e => setAddEnquiry(e.target.value)} />
              <button type="button" onClick={handleAiExtract} disabled={addExtracting || !addEnquiry.trim()}
                style={{ marginTop: 6, padding: '0.4rem 0.8rem', fontSize: '0.85rem', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
                {addExtracting ? '⏳ Extracting…' : '✨ 🤖 AI Extract Details'}
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <div><label className="form-label">Name *</label><input className="form-input" value={addName} onChange={e => setAddName(e.target.value)} required /></div>
              <div><label className="form-label">Email</label><input className="form-input" type="email" value={addEmail} onChange={e => setAddEmail(e.target.value)} /></div>
              <div><label className="form-label">Phone</label><input className="form-input" value={addPhone} onChange={e => setAddPhone(e.target.value)} /></div>
              <div><label className="form-label">Source</label>
                <select className="form-input" value={addSource} onChange={e => setAddSource(e.target.value)}>
                  <option value="manual">Manual</option><option value="website">Website</option><option value="referral">Referral</option>
                  <option value="social">Social</option><option value="booking">Booking</option><option value="other">Other</option>
                </select>
              </div>
              <div><label className="form-label">Value (£)</label><input className="form-input" type="number" step="0.01" value={addValue} onChange={e => setAddValue(e.target.value)} /></div>
              <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: '0.85rem' }}><input type="checkbox" checked={addConsent} onChange={e => setAddConsent(e.target.checked)} /> GDPR Consent</label>
              </div>
              <div style={{ gridColumn: '1 / -1' }}><label className="form-label">Notes</label><textarea className="form-input" rows={2} style={{ width: '100%', resize: 'vertical' }} placeholder="Additional notes about the enquiry…" value={addNotes} onChange={e => setAddNotes(e.target.value)} /></div>
            </div>
            {addExtracted && (
              <div style={{ marginTop: 8, padding: '0.5rem', background: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: 6, fontSize: '0.78rem' }}>
                <div style={{ fontWeight: 600, color: '#7c3aed', marginBottom: 4 }}>🤖 AI Extraction</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {addExtracted.enquiry_type && <span><span style={{ color: '#9ca3af' }}>Type:</span> <strong style={{ textTransform: 'capitalize' }}>{addExtracted.enquiry_type}</strong></span>}
                  {addExtracted.urgency && <span><span style={{ color: '#9ca3af' }}>Urgency:</span> <strong style={{ color: addExtracted.urgency === 'high' ? '#dc2626' : addExtracted.urgency === 'medium' ? '#d97706' : '#16a34a' }}>{addExtracted.urgency}</strong></span>}
                </div>
                {addExtracted.summary && <div style={{ marginTop: 2 }}><span style={{ color: '#9ca3af' }}>Summary:</span> {addExtracted.summary}</div>}
                {addExtracted.suggested_reply_points?.length > 0 && (
                  <div style={{ marginTop: 2 }}><span style={{ color: '#9ca3af' }}>Reply points:</span>
                    <ul style={{ margin: '2px 0 0 16px', padding: 0, fontSize: '0.72rem' }}>
                      {addExtracted.suggested_reply_points.map((p: string, i: number) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
            <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button type="button" onClick={() => { setShowAdd(false); resetAddForm() }} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={!addName.trim()}>Add Lead</button>
            </div>
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
                          <div style={{ display: 'flex', gap: 4, alignItems: 'center', justifyContent: 'flex-end' }}>
                            {l.action_required && (
                              <button className={`btn btn-sm ${l.action_required.includes('overdue') ? 'btn-danger' : 'btn-primary'}`}
                                onClick={() => handleAction(l.id, l.action_required)}>
                                {l.action_required === 'Contact' ? 'Contact now' : l.action_required === 'Convert' ? 'Convert' : 'Done'}
                              </button>
                            )}
                            <button className="btn btn-sm"
                              title="Delete lead"
                              style={{ background: 'transparent', color: '#9ca3af', border: 'none', padding: '4px 6px', fontSize: '0.85rem' }}
                              onClick={() => handleDelete(l.id, l.name)}>
                              🗑
                            </button>
                          </div>
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

          {/* Delete */}
          <button className="btn btn-sm"
            style={{ width: '100%', marginBottom: '0.75rem', background: 'transparent', color: '#9ca3af', border: '1px solid #e5e7eb', fontSize: '0.8rem' }}
            onClick={() => handleDelete(selected.id, selected.name)}>
            🗑 Delete Lead
          </button>

          {/* Panel tabs */}
          <div className="tabs" style={{ marginBottom: '0.5rem' }}>
            {(['details', 'activity', 'history', 'revenue'] as const).map(t => (
              <button key={t} className={`tab ${panelTab === t ? 'active' : ''}`} onClick={() => setPanelTab(t)} style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
                {t === 'details' ? 'Details' : t === 'activity' ? 'Activity' : t === 'history' ? 'History' : 'Revenue'}
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

          {/* Activity tab */}
          {panelTab === 'activity' && (
            <div>
              {/* Message composer */}
              <div style={{ marginBottom: '0.6rem', padding: '0.5rem', background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 6 }}>
                <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                  {(['note', 'email_in', 'email_out', 'call', 'sms'] as const).map(t => (
                    <button key={t} onClick={() => setMsgType(t)}
                      style={{ padding: '2px 6px', fontSize: '0.65rem', borderRadius: 4, border: '1px solid', cursor: 'pointer',
                        borderColor: msgType === t ? 'var(--color-primary)' : '#e5e7eb',
                        background: msgType === t ? 'var(--color-primary)' : '#fff',
                        color: msgType === t ? '#fff' : '#6b7280' }}>
                      {t === 'note' ? '📝 Note' : t === 'email_in' ? '📨 In' : t === 'email_out' ? '📤 Out' : t === 'call' ? '📞 Call' : '💬 SMS'}
                    </button>
                  ))}
                  <button onClick={() => { setShowAnalyzer(!showAnalyzer); setAnalyzerResult(null) }}
                    style={{ marginLeft: 'auto', padding: '2px 6px', fontSize: '0.65rem', borderRadius: 4, border: '1px solid #c084fc', cursor: 'pointer',
                      background: showAnalyzer ? '#7c3aed' : '#faf5ff', color: showAnalyzer ? '#fff' : '#7c3aed' }}>
                    🤖 AI Analyze
                  </button>
                </div>
                {(msgType === 'email_in' || msgType === 'email_out') && (
                  <input className="form-input" style={{ fontSize: '0.75rem', padding: '0.25rem 0.4rem', marginBottom: 4, width: '100%' }}
                    placeholder="Subject…" value={msgSubject} onChange={e => setMsgSubject(e.target.value)} />
                )}
                <div style={{ display: 'flex', gap: 4 }}>
                  <textarea className="form-input" rows={2} style={{ flex: 1, fontSize: '0.75rem', padding: '0.3rem 0.4rem', resize: 'vertical' }}
                    placeholder={msgType === 'note' ? 'Add a note…' : msgType === 'call' ? 'Call notes…' : 'Paste or type message…'}
                    value={msgBody} onChange={e => setMsgBody(e.target.value)} />
                  <button className="btn btn-sm btn-primary" style={{ alignSelf: 'flex-end' }} onClick={handleAddMessage} disabled={!msgBody.trim()}>Add</button>
                </div>
              </div>

              {/* AI Email Analyzer */}
              {showAnalyzer && (
                <div style={{ marginBottom: '0.6rem', padding: '0.5rem', background: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: 6 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#7c3aed', marginBottom: 4 }}>🤖 AI Email Analyzer</div>
                  <textarea className="form-input" rows={4} style={{ width: '100%', fontSize: '0.75rem', padding: '0.3rem 0.4rem', marginBottom: 6, resize: 'vertical' }}
                    placeholder="Paste an email enquiry here — AI will extract name, email, phone, classify the enquiry, and suggest reply points…"
                    value={analyzerText} onChange={e => { setAnalyzerText(e.target.value); setAnalyzerResult(null) }} />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-sm" disabled={analyzerLoading || !analyzerText.trim()}
                      style={{ background: '#7c3aed', color: '#fff', border: 'none', fontSize: '0.72rem' }}
                      onClick={() => handleAnalyzeEmail('existing')}>
                      {analyzerLoading ? '⏳ Analyzing…' : '📎 Analyze & Log'}
                    </button>
                    <button className="btn btn-sm" disabled={analyzerLoading || !analyzerText.trim()}
                      style={{ background: '#2563eb', color: '#fff', border: 'none', fontSize: '0.72rem' }}
                      onClick={() => handleAnalyzeEmail('new')}>
                      {analyzerLoading ? '⏳…' : '✨ Create New Lead'}
                    </button>
                  </div>
                  {analyzerResult && (
                    <div style={{ marginTop: 8, fontSize: '0.75rem', background: '#fff', borderRadius: 4, padding: '0.5rem', border: '1px solid #e9d5ff' }}>
                      <div style={{ fontWeight: 600, marginBottom: 4, color: '#7c3aed' }}>AI Extraction</div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                        {analyzerResult.name && <div><span style={{ color: '#9ca3af' }}>Name:</span> <strong>{analyzerResult.name}</strong></div>}
                        {analyzerResult.email && <div><span style={{ color: '#9ca3af' }}>Email:</span> {analyzerResult.email}</div>}
                        {analyzerResult.phone && <div><span style={{ color: '#9ca3af' }}>Phone:</span> {analyzerResult.phone}</div>}
                        {analyzerResult.enquiry_type && <div><span style={{ color: '#9ca3af' }}>Type:</span> <span style={{ textTransform: 'capitalize' }}>{analyzerResult.enquiry_type}</span></div>}
                        {analyzerResult.urgency && <div><span style={{ color: '#9ca3af' }}>Urgency:</span> <span style={{ fontWeight: 600, color: analyzerResult.urgency === 'high' ? '#dc2626' : analyzerResult.urgency === 'medium' ? '#d97706' : '#16a34a' }}>{analyzerResult.urgency}</span></div>}
                        {analyzerResult.estimated_value && <div><span style={{ color: '#9ca3af' }}>Est. Value:</span> <strong>{typeof analyzerResult.estimated_value === 'number' ? `£${analyzerResult.estimated_value}` : analyzerResult.estimated_value}</strong></div>}
                      </div>
                      {analyzerResult.summary && <div style={{ marginTop: 4 }}><span style={{ color: '#9ca3af' }}>Summary:</span> {analyzerResult.summary}</div>}
                      {analyzerResult.suggested_reply_points?.length > 0 && (
                        <div style={{ marginTop: 4 }}>
                          <span style={{ color: '#9ca3af' }}>Reply points:</span>
                          <ul style={{ margin: '2px 0 0 16px', padding: 0, fontSize: '0.72rem' }}>
                            {analyzerResult.suggested_reply_points.map((p: string, i: number) => <li key={i}>{p}</li>)}
                          </ul>
                        </div>
                      )}
                      {analyzerResult.tags?.length > 0 && (
                        <div style={{ marginTop: 4, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                          {analyzerResult.tags.map((tag: string, i: number) => (
                            <span key={i} style={{ padding: '1px 6px', background: '#ede9fe', color: '#6d28d9', borderRadius: 3, fontSize: '0.65rem' }}>{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Activity feed */}
              {messages.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '1rem 0' }}>No activity yet — log an email, call, or note above</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  {[...messages].reverse().map((m: any) => {
                    const icons: Record<string, string> = { email_in: '📨', email_out: '📤', call: '📞', sms: '💬', note: '📝' }
                    const colors: Record<string, string> = { email_in: '#dbeafe', email_out: '#dcfce7', call: '#fef9c3', sms: '#fce7f3', note: '#f3f4f6' }
                    return (
                      <div key={m.id} style={{ padding: '0.4rem 0.5rem', background: colors[m.message_type] || '#f3f4f6', borderRadius: 6, fontSize: '0.8rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.72rem' }}>{icons[m.message_type] || '📌'} {m.message_type.replace('_', ' ')}</span>
                          <span style={{ fontSize: '0.62rem', color: 'var(--color-text-muted)' }}>{new Date(m.created_at).toLocaleString('en-GB')}</span>
                        </div>
                        {m.subject && <div style={{ fontWeight: 600, fontSize: '0.75rem', marginBottom: 2 }}>{m.subject}</div>}
                        <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.75rem' }}>{m.body.length > 300 ? m.body.slice(0, 300) + '…' : m.body}</div>
                        {m.ai_parsed && (
                          <div style={{ marginTop: 4, padding: '3px 6px', background: 'rgba(124,58,237,0.08)', borderRadius: 4, fontSize: '0.65rem', color: '#7c3aed' }}>
                            🤖 AI: {m.ai_parsed.enquiry_type} · {m.ai_parsed.urgency} urgency{m.ai_parsed.estimated_value ? ` · ~£${m.ai_parsed.estimated_value}` : ''}
                          </div>
                        )}
                      </div>
                    )
                  })}
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

          {/* Revenue tab */}
          {panelTab === 'revenue' && (
            <div>
              {!leadRev || !leadRev.linked ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '1rem 0' }}>
                  {selected.status === 'CONVERTED' ? 'No client record linked yet' : 'Convert this lead to see revenue data'}
                </div>
              ) : (
                <div>
                  {/* Client revenue KPIs */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.35rem', fontSize: '0.78rem', marginBottom: '0.6rem', padding: '0.5rem', background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 6 }}>
                    <div><span style={{ color: 'var(--color-text-muted)' }}>Lifetime value:</span><div style={{ fontWeight: 700, fontSize: '1rem', color: '#15803d' }}>{fmtPrice(leadRev.lifetime_value_pence)}</div></div>
                    <div><span style={{ color: 'var(--color-text-muted)' }}>Bookings:</span><div style={{ fontWeight: 700, fontSize: '1rem' }}>{leadRev.total_bookings}</div></div>
                    <div><span style={{ color: 'var(--color-text-muted)' }}>Completed:</span> {leadRev.completed_bookings}</div>
                    <div><span style={{ color: 'var(--color-text-muted)' }}>Cancelled:</span> {leadRev.cancelled_bookings}</div>
                    <div><span style={{ color: 'var(--color-text-muted)' }}>No-shows:</span> {leadRev.no_show_count}</div>
                    <div><span style={{ color: 'var(--color-text-muted)' }}>Reliability:</span> <span style={{ fontWeight: 600, color: leadRev.reliability_score >= 80 ? '#15803d' : leadRev.reliability_score >= 50 ? '#854d0e' : '#991b1b' }}>{leadRev.reliability_score}%</span></div>
                    {leadRev.avg_days_between_bookings && <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--color-text-muted)' }}>Avg. days between visits:</span> <strong>{Math.round(leadRev.avg_days_between_bookings)}</strong></div>}
                  </div>

                  {/* Booking history */}
                  {leadRev.bookings && leadRev.bookings.length > 0 && (
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.8rem', marginBottom: '0.3rem' }}>Recent Bookings</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                        {leadRev.bookings.map((b: any) => (
                          <div key={b.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.3rem 0.4rem', background: 'var(--color-bg-alt, #f9fafb)', borderRadius: 4, fontSize: '0.75rem' }}>
                            <div>
                              <div style={{ fontWeight: 500 }}>{b.service}</div>
                              <div style={{ color: 'var(--color-text-muted)', fontSize: '0.65rem' }}>{fmtDate(b.date)} {b.time}</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ fontWeight: 600 }}>{fmtPrice(b.amount_pence)}</div>
                              <span className={`badge ${b.status === 'completed' ? 'badge-success' : b.status === 'cancelled' ? 'badge-danger' : b.status === 'no_show' ? 'badge-danger' : 'badge-warning'}`} style={{ fontSize: '0.6rem' }}>{b.status}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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
