'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { getRamsDetail, updateRams, runRamsAiReview } from '@/lib/api'

// ── Section metadata ──
const ALL_SECTIONS = [
  { key: 'job_details', label: 'Job Details', icon: '📋' },
  { key: 'personnel', label: 'Personnel', icon: '👷' },
  { key: 'equipment', label: 'Equipment', icon: '🔧' },
  { key: 'hazards', label: 'Hazards & Controls', icon: '⚠️' },
  { key: 'method_statement', label: 'Method Statement', icon: '📝' },
  { key: 'emergency_procedures', label: 'Emergency Procedures', icon: '🚑' },
  { key: 'environmental', label: 'Environmental', icon: '🌿' },
  { key: 'permits', label: 'Permits', icon: '📄' },
  { key: 'monitoring', label: 'Monitoring & Review', icon: '🔍' },
]

const RISK_LABELS: Record<number, string> = { 1: 'Very Low', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Very High' }
const RISK_COLOURS: Record<string, string> = {
  low: '#22c55e', medium: '#f59e0b', high: '#ef4444', 'very high': '#991b1b',
}

function riskScore(l: number, s: number) { return l * s }
function riskLevel(score: number): string {
  if (score <= 4) return 'low'
  if (score <= 9) return 'medium'
  if (score <= 16) return 'high'
  return 'very high'
}
function riskColour(score: number): string {
  return RISK_COLOURS[riskLevel(score)] || '#94a3b8'
}

const emptyHazard = () => ({
  description: '', controls: '',
  initial_likelihood: 3, initial_severity: 3,
  residual_likelihood: 1, residual_severity: 2,
})

const emptyPerson = () => ({ name: '', role: '', qualifications: '', responsibilities: '' })
const emptyEquipment = () => ({ name: '', inspection_date: '', cert_ref: '', notes: '' })
const emptyStep = (n: number) => ({ step_number: n, description: '', responsible: '', hazard_refs: '' })
const emptyPermit = () => ({ type: '', reference: '', issued_by: '', expiry: '' })

export default function RamsEditorPage() {
  const params = useParams()
  const ramsId = Number(params.id)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [rams, setRams] = useState<any>(null)
  const [activeSection, setActiveSection] = useState('job_details')
  const [aiLoading, setAiLoading] = useState(false)

  // Form data
  const [applicableSections, setApplicableSections] = useState<string[]>([])
  const [jobDetails, setJobDetails] = useState<any>({})
  const [personnel, setPersonnel] = useState<any[]>([emptyPerson()])
  const [equipment, setEquipment] = useState<any[]>([emptyEquipment()])
  const [hazards, setHazards] = useState<any[]>([emptyHazard()])
  const [methodStatement, setMethodStatement] = useState<any[]>([emptyStep(1)])
  const [emergencyProcedures, setEmergencyProcedures] = useState<any>({})
  const [environmental, setEnvironmental] = useState<any>({})
  const [permits, setPermits] = useState<any[]>([emptyPermit()])
  const [monitoring, setMonitoring] = useState<any>({})
  const [aiReview, setAiReview] = useState<any>(null)
  const [title, setTitle] = useState('')
  const [refNumber, setRefNumber] = useState('')
  const [ramsStatus, setRamsStatus] = useState('DRAFT')

  const load = useCallback(async () => {
    setLoading(true)
    const res = await getRamsDetail(ramsId)
    if (res.data) {
      const d = res.data
      setRams(d)
      setTitle(d.title || '')
      setRefNumber(d.reference_number || '')
      setRamsStatus(d.status || 'DRAFT')
      setApplicableSections(d.applicable_sections?.length ? d.applicable_sections : ALL_SECTIONS.map(s => s.key))
      setJobDetails(d.job_details || {})
      setPersonnel(d.personnel?.length ? d.personnel : [emptyPerson()])
      setEquipment(d.equipment?.length ? d.equipment : [emptyEquipment()])
      setHazards(d.hazards?.length ? d.hazards : [emptyHazard()])
      setMethodStatement(d.method_statement?.length ? d.method_statement : [emptyStep(1)])
      setEmergencyProcedures(d.emergency_procedures || {})
      setEnvironmental(d.environmental || {})
      setPermits(d.permits?.length ? d.permits : [emptyPermit()])
      setMonitoring(d.monitoring || {})
      setAiReview(d.ai_review || null)
    }
    setLoading(false)
  }, [ramsId])

  useEffect(() => { load() }, [load])

  async function handleSave() {
    setSaving(true)
    setSaved(false)
    await updateRams(ramsId, {
      title, reference_number: refNumber, status: ramsStatus,
      applicable_sections: applicableSections,
      job_details: jobDetails,
      personnel, equipment, hazards,
      method_statement: methodStatement,
      emergency_procedures: emergencyProcedures,
      environmental, permits, monitoring,
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  async function handleAiReview() {
    await handleSave()
    setAiLoading(true)
    const res = await runRamsAiReview(ramsId)
    if (res.data) setAiReview(res.data)
    setAiLoading(false)
    setActiveSection('ai_review')
  }

  function toggleSection(key: string) {
    setApplicableSections(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }

  function isApplicable(key: string) { return applicableSections.includes(key) }

  // Hazard helpers
  function updateHazard(idx: number, field: string, value: any) {
    setHazards(prev => prev.map((h, i) => i === idx ? { ...h, [field]: value } : h))
  }
  function addHazard() { setHazards(prev => [...prev, emptyHazard()]) }
  function removeHazard(idx: number) { setHazards(prev => prev.filter((_, i) => i !== idx)) }

  // Personnel helpers
  function updatePerson(idx: number, field: string, value: string) {
    setPersonnel(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p))
  }
  function addPerson() { setPersonnel(prev => [...prev, emptyPerson()]) }
  function removePerson(idx: number) { setPersonnel(prev => prev.filter((_, i) => i !== idx)) }

  // Equipment helpers
  function updateEquip(idx: number, field: string, value: string) {
    setEquipment(prev => prev.map((e, i) => i === idx ? { ...e, [field]: value } : e))
  }
  function addEquip() { setEquipment(prev => [...prev, emptyEquipment()]) }
  function removeEquip(idx: number) { setEquipment(prev => prev.filter((_, i) => i !== idx)) }

  // Method statement helpers
  function updateStep(idx: number, field: string, value: string) {
    setMethodStatement(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s))
  }
  function addStep() { setMethodStatement(prev => [...prev, emptyStep(prev.length + 1)]) }
  function removeStep(idx: number) {
    setMethodStatement(prev => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_number: i + 1 })))
  }

  // Permit helpers
  function updatePermit(idx: number, field: string, value: string) {
    setPermits(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p))
  }
  function addPermit() { setPermits(prev => [...prev, emptyPermit()]) }
  function removePermit(idx: number) { setPermits(prev => prev.filter((_, i) => i !== idx)) }

  if (loading) return <div className="empty-state">Loading RAMS…</div>
  if (!rams) return <div className="empty-state">RAMS document not found</div>

  const navSections = ALL_SECTIONS.filter(s => isApplicable(s.key))

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <a href="/admin/health-safety/rams" style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', textDecoration: 'none' }}>← RAMS</a>
          <span style={{ color: 'var(--color-text-muted)' }}>/</span>
          <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{title || 'Untitled'}</h2>
          <span className={`badge ${ramsStatus === 'ACTIVE' ? 'badge-success' : ramsStatus === 'EXPIRED' ? 'badge-danger' : 'badge-warning'}`}>
            {ramsStatus}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          {saved && <span style={{ fontSize: '0.78rem', color: '#22c55e', fontWeight: 600 }}>✓ Saved</span>}
          <button className="btn btn-outline btn-sm" onClick={handleAiReview} disabled={aiLoading}>
            {aiLoading ? '🤖 Reviewing…' : '🤖 AI Review'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        {/* Sidebar nav */}
        <div style={{ width: 210, flexShrink: 0, position: 'sticky', top: 80 }}>
          {/* Title & ref */}
          <div style={{ marginBottom: '0.75rem' }}>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="RAMS title" style={inputSm} />
            <input value={refNumber} onChange={e => setRefNumber(e.target.value)} placeholder="Ref number" style={{ ...inputSm, marginTop: 4 }} />
            <select value={ramsStatus} onChange={e => setRamsStatus(e.target.value)} style={{ ...inputSm, marginTop: 4 }}>
              <option value="DRAFT">Draft</option>
              <option value="ACTIVE">Active</option>
              <option value="EXPIRED">Expired</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>

          {/* Section toggles */}
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
            Sections
          </div>
          {ALL_SECTIONS.map(s => (
            <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: 2 }}>
              <input
                type="checkbox"
                checked={isApplicable(s.key)}
                onChange={() => toggleSection(s.key)}
                style={{ margin: 0, cursor: 'pointer' }}
              />
              <button
                onClick={() => { if (isApplicable(s.key)) setActiveSection(s.key) }}
                disabled={!isApplicable(s.key)}
                style={{
                  background: activeSection === s.key ? 'var(--color-primary)' : 'transparent',
                  color: activeSection === s.key ? '#fff' : isApplicable(s.key) ? 'var(--color-text)' : 'var(--color-text-muted)',
                  border: 'none', borderRadius: 4, padding: '0.3rem 0.5rem', fontSize: '0.8rem',
                  fontWeight: activeSection === s.key ? 700 : 500,
                  cursor: isApplicable(s.key) ? 'pointer' : 'default',
                  textAlign: 'left', fontFamily: 'inherit', opacity: isApplicable(s.key) ? 1 : 0.5,
                  width: '100%', textDecoration: isApplicable(s.key) ? 'none' : 'line-through',
                }}
              >
                {s.icon} {s.label}
              </button>
            </div>
          ))}
          {/* AI Review nav */}
          {aiReview && (
            <button
              onClick={() => setActiveSection('ai_review')}
              style={{
                background: activeSection === 'ai_review' ? 'var(--color-primary)' : 'transparent',
                color: activeSection === 'ai_review' ? '#fff' : 'var(--color-text)',
                border: 'none', borderRadius: 4, padding: '0.3rem 0.5rem', fontSize: '0.8rem',
                fontWeight: activeSection === 'ai_review' ? 700 : 500,
                cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', width: '100%', marginTop: 4,
              }}
            >🤖 AI Review</button>
          )}

          {/* Completion */}
          <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: '#f8fafc', borderRadius: 6, fontSize: '0.78rem' }}>
            <div style={{ fontWeight: 700, marginBottom: 2 }}>Completion</div>
            {navSections.map(s => {
              const val = s.key === 'job_details' ? jobDetails :
                s.key === 'personnel' ? personnel :
                s.key === 'equipment' ? equipment :
                s.key === 'hazards' ? hazards :
                s.key === 'method_statement' ? methodStatement :
                s.key === 'emergency_procedures' ? emergencyProcedures :
                s.key === 'environmental' ? environmental :
                s.key === 'permits' ? permits :
                s.key === 'monitoring' ? monitoring : null
              const filled = val && (Array.isArray(val) ? val.length > 0 : Object.keys(val).length > 0)
              return (
                <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: 1 }}>
                  <span style={{ color: filled ? '#22c55e' : '#f59e0b' }}>{filled ? '✓' : '○'}</span>
                  <span style={{ color: filled ? 'var(--color-text)' : 'var(--color-text-muted)' }}>{s.label}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Main content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* ── Job Details ── */}
          {activeSection === 'job_details' && isApplicable('job_details') && (
            <SectionCard title="Job Details" icon="📋">
              <FormRow label="Client / Company Name">
                <input value={jobDetails.client_name || ''} onChange={e => setJobDetails((p: any) => ({ ...p, client_name: e.target.value }))} style={inputStyle} placeholder="e.g. Acme Construction Ltd" />
              </FormRow>
              <FormRow label="Site Address">
                <textarea value={jobDetails.site_address || ''} onChange={e => setJobDetails((p: any) => ({ ...p, site_address: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Full site address" />
              </FormRow>
              <FormRow label="Job Description">
                <textarea value={jobDetails.job_description || ''} onChange={e => setJobDetails((p: any) => ({ ...p, job_description: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={3} placeholder="Describe the scope of work" />
              </FormRow>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <FormRow label="Start Date">
                  <input type="date" value={jobDetails.start_date || ''} onChange={e => setJobDetails((p: any) => ({ ...p, start_date: e.target.value }))} style={inputStyle} />
                </FormRow>
                <FormRow label="End Date">
                  <input type="date" value={jobDetails.end_date || ''} onChange={e => setJobDetails((p: any) => ({ ...p, end_date: e.target.value }))} style={inputStyle} />
                </FormRow>
              </div>
              <FormRow label="Principal Contractor">
                <input value={jobDetails.principal_contractor || ''} onChange={e => setJobDetails((p: any) => ({ ...p, principal_contractor: e.target.value }))} style={inputStyle} placeholder="If applicable" />
              </FormRow>
              <FormRow label="Additional Notes">
                <textarea value={jobDetails.notes || ''} onChange={e => setJobDetails((p: any) => ({ ...p, notes: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} />
              </FormRow>
            </SectionCard>
          )}

          {/* ── Personnel ── */}
          {activeSection === 'personnel' && isApplicable('personnel') && (
            <SectionCard title="Personnel" icon="👷">
              {personnel.map((p, idx) => (
                <div key={idx} className="card" style={{ padding: '0.75rem', marginBottom: '0.5rem', background: '#f8fafc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Person {idx + 1}</span>
                    {personnel.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => removePerson(idx)}>Remove</button>}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <input placeholder="Name" value={p.name} onChange={e => updatePerson(idx, 'name', e.target.value)} style={inputStyle} />
                    <input placeholder="Role / Trade" value={p.role} onChange={e => updatePerson(idx, 'role', e.target.value)} style={inputStyle} />
                    <input placeholder="Qualifications / Cards" value={p.qualifications} onChange={e => updatePerson(idx, 'qualifications', e.target.value)} style={inputStyle} />
                    <input placeholder="Responsibilities" value={p.responsibilities} onChange={e => updatePerson(idx, 'responsibilities', e.target.value)} style={inputStyle} />
                  </div>
                </div>
              ))}
              <button className="btn btn-outline btn-sm" onClick={addPerson}>+ Add Person</button>
            </SectionCard>
          )}

          {/* ── Equipment ── */}
          {activeSection === 'equipment' && isApplicable('equipment') && (
            <SectionCard title="Equipment" icon="🔧">
              {equipment.map((eq, idx) => (
                <div key={idx} className="card" style={{ padding: '0.75rem', marginBottom: '0.5rem', background: '#f8fafc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Item {idx + 1}</span>
                    {equipment.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => removeEquip(idx)}>Remove</button>}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <input placeholder="Equipment name" value={eq.name} onChange={e => updateEquip(idx, 'name', e.target.value)} style={inputStyle} />
                    <input placeholder="Inspection date" type="date" value={eq.inspection_date} onChange={e => updateEquip(idx, 'inspection_date', e.target.value)} style={inputStyle} />
                    <input placeholder="Certificate ref" value={eq.cert_ref} onChange={e => updateEquip(idx, 'cert_ref', e.target.value)} style={inputStyle} />
                    <input placeholder="Notes" value={eq.notes} onChange={e => updateEquip(idx, 'notes', e.target.value)} style={inputStyle} />
                  </div>
                </div>
              ))}
              <button className="btn btn-outline btn-sm" onClick={addEquip}>+ Add Equipment</button>
            </SectionCard>
          )}

          {/* ── Hazards & Controls ── */}
          {activeSection === 'hazards' && isApplicable('hazards') && (
            <SectionCard title="Hazards & Controls" icon="⚠️">
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: '0 0 0.75rem' }}>
                Identify each hazard, describe controls, and rate the initial and residual risk using the 5×5 matrix (Likelihood × Severity).
              </p>
              {hazards.map((h, idx) => {
                const initScore = riskScore(h.initial_likelihood, h.initial_severity)
                const resScore = riskScore(h.residual_likelihood, h.residual_severity)
                return (
                  <div key={idx} className="card" style={{ padding: '0.85rem', marginBottom: '0.75rem', borderLeft: `4px solid ${riskColour(resScore)}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Hazard #{idx + 1}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: 4, background: riskColour(initScore), color: '#fff', fontWeight: 700 }}>
                          Initial: {initScore}
                        </span>
                        <span style={{ fontSize: '0.75rem' }}>→</span>
                        <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: 4, background: riskColour(resScore), color: '#fff', fontWeight: 700 }}>
                          Residual: {resScore}
                        </span>
                        {hazards.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => removeHazard(idx)}>✕</button>}
                      </div>
                    </div>
                    <textarea
                      placeholder="Describe the hazard…"
                      value={h.description}
                      onChange={e => updateHazard(idx, 'description', e.target.value)}
                      style={{ ...inputStyle, resize: 'vertical', marginBottom: '0.5rem' }}
                      rows={2}
                    />
                    <textarea
                      placeholder="Controls in place / additional controls required…"
                      value={h.controls}
                      onChange={e => updateHazard(idx, 'controls', e.target.value)}
                      style={{ ...inputStyle, resize: 'vertical', marginBottom: '0.5rem' }}
                      rows={2}
                    />
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>Initial Risk (Before Controls)</div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <RiskSelect label="Likelihood" value={h.initial_likelihood} onChange={v => updateHazard(idx, 'initial_likelihood', v)} />
                          <RiskSelect label="Severity" value={h.initial_severity} onChange={v => updateHazard(idx, 'initial_severity', v)} />
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>Residual Risk (After Controls)</div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <RiskSelect label="Likelihood" value={h.residual_likelihood} onChange={v => updateHazard(idx, 'residual_likelihood', v)} />
                          <RiskSelect label="Severity" value={h.residual_severity} onChange={v => updateHazard(idx, 'residual_severity', v)} />
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
              <button className="btn btn-outline btn-sm" onClick={addHazard}>+ Add Hazard</button>

              {/* 5×5 Risk Matrix legend */}
              <div style={{ marginTop: '1.25rem' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem' }}>5×5 Risk Matrix</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginBottom: '0.4rem' }}>
                  Risk Rating = Likelihood × Severity
                </div>
                <table style={{ borderCollapse: 'collapse', fontSize: '0.72rem', width: '100%', maxWidth: 360 }}>
                  <thead>
                    <tr>
                      <th style={matrixCell}></th>
                      {[1,2,3,4,5].map(s => <th key={s} style={matrixCell}>S{s}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {[5,4,3,2,1].map(l => (
                      <tr key={l}>
                        <td style={{ ...matrixCell, fontWeight: 700 }}>L{l}</td>
                        {[1,2,3,4,5].map(s => {
                          const sc = l * s
                          return <td key={s} style={{ ...matrixCell, background: riskColour(sc), color: '#fff', fontWeight: 700, textAlign: 'center' }}>{sc}</td>
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.4rem', fontSize: '0.72rem' }}>
                  <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#22c55e', marginRight: 4 }} />Low (1-4)</span>
                  <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#f59e0b', marginRight: 4 }} />Medium (5-9)</span>
                  <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#ef4444', marginRight: 4 }} />High (10-16)</span>
                  <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#991b1b', marginRight: 4 }} />Very High (17-25)</span>
                </div>
              </div>
            </SectionCard>
          )}

          {/* ── Method Statement ── */}
          {activeSection === 'method_statement' && isApplicable('method_statement') && (
            <SectionCard title="Method Statement" icon="📝">
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: '0 0 0.75rem' }}>
                Describe the step-by-step process. Edit as needed for your specific job.
              </p>
              {methodStatement.map((s, idx) => (
                <div key={idx} className="card" style={{ padding: '0.75rem', marginBottom: '0.5rem', background: '#f8fafc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Step {idx + 1}</span>
                    {methodStatement.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => removeStep(idx)}>✕</button>}
                  </div>
                  <textarea
                    placeholder="Describe this step…"
                    value={s.description}
                    onChange={e => updateStep(idx, 'description', e.target.value)}
                    style={{ ...inputStyle, resize: 'vertical', marginBottom: '0.4rem' }}
                    rows={2}
                  />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <input placeholder="Responsible person / role" value={s.responsible} onChange={e => updateStep(idx, 'responsible', e.target.value)} style={inputStyle} />
                    <input placeholder="Related hazard #s (e.g. 1, 3)" value={s.hazard_refs} onChange={e => updateStep(idx, 'hazard_refs', e.target.value)} style={inputStyle} />
                  </div>
                </div>
              ))}
              <button className="btn btn-outline btn-sm" onClick={addStep}>+ Add Step</button>
            </SectionCard>
          )}

          {/* ── Emergency Procedures ── */}
          {activeSection === 'emergency_procedures' && isApplicable('emergency_procedures') && (
            <SectionCard title="Emergency Procedures" icon="🚑">
              <FormRow label="Emergency Contact">
                <input value={emergencyProcedures.emergency_contact || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, emergency_contact: e.target.value }))} style={inputStyle} placeholder="Name and phone number" />
              </FormRow>
              <FormRow label="First Aider(s)">
                <input value={emergencyProcedures.first_aiders || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, first_aiders: e.target.value }))} style={inputStyle} placeholder="Names of qualified first aiders on site" />
              </FormRow>
              <FormRow label="Nearest Hospital / A&E">
                <input value={emergencyProcedures.nearest_hospital || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, nearest_hospital: e.target.value }))} style={inputStyle} placeholder="Name and address" />
              </FormRow>
              <FormRow label="Evacuation Procedure">
                <textarea value={emergencyProcedures.evacuation_procedure || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, evacuation_procedure: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={3} placeholder="Describe the evacuation procedure" />
              </FormRow>
              <FormRow label="Fire Assembly Point">
                <input value={emergencyProcedures.assembly_point || ''} onChange={e => setEmergencyProcedures((p: any) => ({ ...p, assembly_point: e.target.value }))} style={inputStyle} />
              </FormRow>
            </SectionCard>
          )}

          {/* ── Environmental ── */}
          {activeSection === 'environmental' && isApplicable('environmental') && (
            <SectionCard title="Environmental Considerations" icon="🌿">
              <FormRow label="Waste Disposal">
                <textarea value={environmental.waste_disposal || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, waste_disposal: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="How waste will be managed and disposed of" />
              </FormRow>
              <FormRow label="Noise / Vibration">
                <textarea value={environmental.noise || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, noise: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Noise or vibration considerations and mitigations" />
              </FormRow>
              <FormRow label="Protected Areas / Wildlife">
                <textarea value={environmental.protected_areas || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, protected_areas: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Nearby protected areas, watercourses, etc." />
              </FormRow>
              <FormRow label="Dust / Emissions">
                <textarea value={environmental.dust || ''} onChange={e => setEnvironmental((p: any) => ({ ...p, dust: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Dust suppression measures" />
              </FormRow>
            </SectionCard>
          )}

          {/* ── Permits ── */}
          {activeSection === 'permits' && isApplicable('permits') && (
            <SectionCard title="Permits to Work" icon="📄">
              {permits.map((p, idx) => (
                <div key={idx} className="card" style={{ padding: '0.75rem', marginBottom: '0.5rem', background: '#f8fafc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Permit {idx + 1}</span>
                    {permits.length > 1 && <button className="btn btn-ghost btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => removePermit(idx)}>Remove</button>}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <input placeholder="Permit type" value={p.type} onChange={e => updatePermit(idx, 'type', e.target.value)} style={inputStyle} />
                    <input placeholder="Reference" value={p.reference} onChange={e => updatePermit(idx, 'reference', e.target.value)} style={inputStyle} />
                    <input placeholder="Issued by" value={p.issued_by} onChange={e => updatePermit(idx, 'issued_by', e.target.value)} style={inputStyle} />
                    <input placeholder="Expiry" type="date" value={p.expiry} onChange={e => updatePermit(idx, 'expiry', e.target.value)} style={inputStyle} />
                  </div>
                </div>
              ))}
              <button className="btn btn-outline btn-sm" onClick={addPermit}>+ Add Permit</button>
            </SectionCard>
          )}

          {/* ── Monitoring ── */}
          {activeSection === 'monitoring' && isApplicable('monitoring') && (
            <SectionCard title="Monitoring & Review" icon="🔍">
              <FormRow label="Review Schedule">
                <textarea value={monitoring.review_schedule || ''} onChange={e => setMonitoring((p: any) => ({ ...p, review_schedule: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="How often will this RAMS be reviewed?" />
              </FormRow>
              <FormRow label="Sign-off Requirements">
                <textarea value={monitoring.signoff || ''} onChange={e => setMonitoring((p: any) => ({ ...p, signoff: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Who needs to sign off before work starts?" />
              </FormRow>
              <FormRow label="Toolbox Talk Records">
                <textarea value={monitoring.toolbox_talks || ''} onChange={e => setMonitoring((p: any) => ({ ...p, toolbox_talks: e.target.value }))} style={{ ...inputStyle, resize: 'vertical' }} rows={2} placeholder="Record of toolbox talks delivered" />
              </FormRow>
            </SectionCard>
          )}

          {/* ── AI Review ── */}
          {activeSection === 'ai_review' && aiReview && (
            <SectionCard title="AI Safety Review" icon="🤖">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{
                  width: 56, height: 56, borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.4rem', fontWeight: 800,
                  background: (aiReview.score || 0) >= 7 ? '#dcfce7' : (aiReview.score || 0) >= 4 ? '#fef3c7' : '#fef2f2',
                  color: (aiReview.score || 0) >= 7 ? '#15803d' : (aiReview.score || 0) >= 4 ? '#92400e' : '#991b1b',
                }}>
                  {aiReview.score || '?'}/10
                </div>
                <div>
                  <div style={{ fontWeight: 700 }}>{aiReview.summary}</div>
                  {aiReview.reviewed_at && <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>Reviewed: {new Date(aiReview.reviewed_at).toLocaleString()}</div>}
                  {aiReview.ai_powered === false && <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>Rule-based (AI unavailable)</span>}
                </div>
              </div>

              {aiReview.findings?.length > 0 && (
                <>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.4rem' }}>Findings</div>
                  {aiReview.findings.map((f: any, i: number) => (
                    <div key={i} style={{
                      padding: '0.6rem 0.75rem', borderRadius: 6, marginBottom: '0.4rem',
                      border: `1px solid ${f.severity === 'high' ? '#fecaca' : f.severity === 'medium' ? '#fed7aa' : '#e2e8f0'}`,
                      background: f.severity === 'high' ? '#fef2f2' : f.severity === 'medium' ? '#fffbeb' : '#f8fafc',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: 2 }}>
                        <span className={`badge ${f.severity === 'high' ? 'badge-danger' : f.severity === 'medium' ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.68rem' }}>
                          {f.severity.toUpperCase()}
                        </span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{f.section}</span>
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{f.issue}</div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: 2 }}>💡 {f.recommendation}</div>
                    </div>
                  ))}
                </>
              )}

              {aiReview.positive_points?.length > 0 && (
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.4rem' }}>Positive Points</div>
                  {aiReview.positive_points.map((p: string, i: number) => (
                    <div key={i} style={{ fontSize: '0.85rem', marginBottom: 2 }}>✅ {p}</div>
                  ))}
                </div>
              )}

              {aiReview.missing_controls?.length > 0 && (
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.4rem' }}>Missing Controls</div>
                  {aiReview.missing_controls.map((c: string, i: number) => (
                    <div key={i} style={{ fontSize: '0.85rem', marginBottom: 2 }}>⚠️ {c}</div>
                  ))}
                </div>
              )}

              <div style={{ marginTop: '1rem' }}>
                <button className="btn btn-outline btn-sm" onClick={handleAiReview} disabled={aiLoading}>
                  {aiLoading ? 'Re-running…' : '🔄 Re-run AI Review'}
                </button>
              </div>
            </SectionCard>
          )}

          {/* Disclaimer */}
          <div style={{
            marginTop: '1.5rem', padding: '0.85rem', borderRadius: 8,
            background: '#fffbeb', border: '1px solid #fcd34d', fontSize: '0.82rem', color: '#92400e',
          }}>
            <strong>⚠️ Important Notice</strong><br />
            This tool generates RAMS documents based on the information you provide. All documents must be reviewed and approved by a competent health &amp; safety professional before use. This tool does not replace professional health &amp; safety advice or legal compliance requirements.
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ──

function SectionCard({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ padding: '1.15rem', marginBottom: '1rem' }}>
      <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <span>{icon}</span> {title}
      </h3>
      {children}
    </div>
  )
}

function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '0.65rem' }}>
      <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>{label}</label>
      {children}
    </div>
  )
}

function RiskSelect({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: 2 }}>{label}</div>
      <select
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{ ...inputStyle, fontSize: '0.82rem' }}
      >
        {[1,2,3,4,5].map(n => (
          <option key={n} value={n}>{n} — {RISK_LABELS[n]}</option>
        ))}
      </select>
    </div>
  )
}

// ── Styles ──
const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.45rem 0.65rem', borderRadius: 6,
  border: '1px solid #e2e8f0', fontSize: '0.85rem', fontFamily: 'inherit',
  outline: 'none', boxSizing: 'border-box',
}

const inputSm: React.CSSProperties = {
  ...inputStyle, fontSize: '0.8rem', padding: '0.35rem 0.55rem',
}

const matrixCell: React.CSSProperties = {
  padding: '0.25rem 0.4rem', border: '1px solid #e2e8f0', fontSize: '0.72rem',
}
