'use client'

import React, { useEffect, useState } from 'react'
import {
  getTrainingRecords, createTrainingRecord, deleteTrainingRecord,
  getTrainingCourses, createTrainingCourse, updateTrainingCourse, deleteTrainingCourse,
  getTrainingReminders, getTrainingCompliance,
} from '@/lib/api'

interface TrainingTabProps {
  staff: any[]
  currentUserRole: string
  onRefresh?: () => void
}

const STATUS_COLOURS: Record<string, { bg: string; text: string; label: string }> = {
  valid: { bg: '#dcfce7', text: '#15803d', label: 'Valid' },
  expiring_soon: { bg: '#fef9c3', text: '#a16207', label: 'Expiring Soon' },
  expired: { bg: '#fee2e2', text: '#dc2626', label: 'Expired' },
  missing: { bg: '#f3f4f6', text: '#6b7280', label: 'Not Completed' },
}

export default function TrainingTab({ staff, currentUserRole, onRefresh }: TrainingTabProps) {
  const [subTab, setSubTab] = useState<'records' | 'courses' | 'compliance' | 'reminders'>('records')
  const [records, setRecords] = useState<any[]>([])
  const [courses, setCourses] = useState<any[]>([])
  const [reminders, setReminders] = useState<any[]>([])
  const [compliance, setCompliance] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Add record modal
  const [showAddRecord, setShowAddRecord] = useState(false)
  const [recForm, setRecForm] = useState({ staff: '', course: '', title: '', provider: '', completed_date: '', expiry_date: '', certificate_reference: '', notes: '' })
  const [recSaving, setRecSaving] = useState(false)
  const [recError, setRecError] = useState('')

  // Add course modal
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [courseForm, setCourseForm] = useState({ name: '', provider: '', is_mandatory: false, renewal_months: 12, reminder_days_before: 30, description: '' })
  const [courseSaving, setCourseSaving] = useState(false)
  const [courseError, setCourseError] = useState('')

  const isManager = currentUserRole === 'owner' || currentUserRole === 'manager'

  const loadData = async () => {
    setLoading(true)
    const [recRes, courseRes, remRes, compRes] = await Promise.all([
      getTrainingRecords(),
      getTrainingCourses(),
      getTrainingReminders(),
      isManager ? getTrainingCompliance() : Promise.resolve({ data: [] }),
    ])
    setRecords(recRes.data || [])
    setCourses(courseRes.data || [])
    setReminders(remRes.data || [])
    setCompliance(compRes.data || [])
    setLoading(false)
  }

  useEffect(() => { loadData() }, [])

  // Submit new training record
  const submitRecord = async () => {
    setRecSaving(true)
    setRecError('')
    const payload: any = { ...recForm }
    if (payload.course) payload.course = Number(payload.course)
    if (payload.staff) payload.staff = Number(payload.staff)
    if (!payload.staff) { setRecError('Please select a staff member.'); setRecSaving(false); return }
    if (!payload.title && !payload.course) { setRecError('Please select a course or enter a title.'); setRecSaving(false); return }
    if (!payload.completed_date) { setRecError('Please enter a completion date.'); setRecSaving(false); return }
    // Remove empty strings
    Object.keys(payload).forEach(k => { if (payload[k] === '') delete payload[k] })
    const res = await createTrainingRecord(payload)
    if (res.error) { setRecError(res.error); setRecSaving(false); return }
    setRecSaving(false)
    setShowAddRecord(false)
    setRecForm({ staff: '', course: '', title: '', provider: '', completed_date: '', expiry_date: '', certificate_reference: '', notes: '' })
    loadData()
    if (onRefresh) onRefresh()
  }

  // Submit new course
  const submitCourse = async () => {
    setCourseSaving(true)
    setCourseError('')
    if (!courseForm.name.trim()) { setCourseError('Course name is required.'); setCourseSaving(false); return }
    const res = await createTrainingCourse({
      ...courseForm,
      renewal_months: Number(courseForm.renewal_months),
      reminder_days_before: Number(courseForm.reminder_days_before),
    })
    if (res.error) { setCourseError(res.error); setCourseSaving(false); return }
    setCourseSaving(false)
    setShowAddCourse(false)
    setCourseForm({ name: '', provider: '', is_mandatory: false, renewal_months: 12, reminder_days_before: 30, description: '' })
    loadData()
  }

  const handleDeleteRecord = async (id: number) => {
    if (!confirm('Delete this training record?')) return
    await deleteTrainingRecord(id)
    loadData()
    if (onRefresh) onRefresh()
  }

  const handleDeleteCourse = async (id: number) => {
    if (!confirm('Remove this course? Existing records will be kept.')) return
    await deleteTrainingCourse(id)
    loadData()
  }

  const handleToggleMandatory = async (course: any) => {
    await updateTrainingCourse(course.id, { is_mandatory: !course.is_mandatory })
    loadData()
  }

  // When course is selected in add-record form, auto-populate fields
  const handleCourseSelect = (courseId: string) => {
    setRecForm(prev => {
      const updated = { ...prev, course: courseId }
      if (courseId) {
        const c = courses.find((x: any) => String(x.id) === courseId)
        if (c) {
          updated.title = c.name
          updated.provider = c.provider || ''
        }
      }
      return updated
    })
  }

  if (loading) return <div className="empty-state">Loading training data...</div>

  return (
    <div>
      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
        {[
          { key: 'records', label: 'Records' },
          { key: 'courses', label: 'Courses' },
          ...(isManager ? [{ key: 'compliance', label: 'Compliance' }] : []),
          { key: 'reminders', label: `Reminders${reminders.length > 0 ? ` (${reminders.length})` : ''}` },
        ].map(t => (
          <button
            key={t.key}
            className={`btn btn-sm ${subTab === t.key ? 'btn-primary' : ''}`}
            onClick={() => setSubTab(t.key as any)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Reminders banner (always visible if there are alerts) ── */}
      {reminders.length > 0 && subTab !== 'reminders' && (
        <div style={{
          padding: '10px 14px', marginBottom: 16, borderRadius: 'var(--radius)',
          backgroundColor: '#fef3c7', border: '1px solid #f59e0b',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ fontSize: '0.88rem', color: '#92400e' }}>
            <strong>{reminders.filter(r => r.alert_type === 'expired').length} expired</strong> and{' '}
            <strong>{reminders.filter(r => r.alert_type === 'expiring_soon').length} expiring soon</strong> training records need attention.
          </div>
          <button className="btn btn-sm" onClick={() => setSubTab('reminders')}>View</button>
        </div>
      )}

      {/* ── Records sub-tab ── */}
      {subTab === 'records' && (
        <>
          {isManager && (
            <div style={{ marginBottom: 12 }}>
              <button className="btn btn-primary" onClick={() => setShowAddRecord(true)}>+ Add Training Record</button>
            </div>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Staff</th><th>Course</th><th>Provider</th><th>Completed</th><th>Expiry</th><th>Status</th>
                  {isManager && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {records.map((r: any) => {
                  let statusLabel = 'Valid'
                  let statusClass = 'badge-success'
                  if (r.is_expired) { statusLabel = 'Expired'; statusClass = 'badge-danger' }
                  else if (r.is_expiring_soon) { statusLabel = `Expiring (${r.days_until_expiry}d)`; statusClass = 'badge-warning' }
                  else if (!r.expiry_date) { statusLabel = 'No Expiry'; statusClass = '' }
                  return (
                    <tr key={r.id}>
                      <td style={{ fontWeight: 600 }}>{r.staff_name}</td>
                      <td>
                        {r.title}
                        {r.is_mandatory && <span style={{ marginLeft: 6, fontSize: '0.7rem', color: '#dc2626', fontWeight: 600 }}>MANDATORY</span>}
                      </td>
                      <td>{r.provider || '—'}</td>
                      <td>{r.completed_date || '—'}</td>
                      <td>{r.expiry_date || 'N/A'}</td>
                      <td><span className={`badge ${statusClass}`}>{statusLabel}</span></td>
                      {isManager && (
                        <td>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDeleteRecord(r.id)}>Delete</button>
                        </td>
                      )}
                    </tr>
                  )
                })}
                {records.length === 0 && <tr><td colSpan={isManager ? 7 : 6} className="empty-state">No training records yet</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* ── Courses sub-tab ── */}
      {subTab === 'courses' && (
        <>
          {isManager && (
            <div style={{ marginBottom: 12 }}>
              <button className="btn btn-primary" onClick={() => setShowAddCourse(true)}>+ Add Course</button>
            </div>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Course Name</th><th>Provider</th><th>Type</th><th>Renewal</th><th>Reminder</th>{isManager && <th>Actions</th>}</tr>
              </thead>
              <tbody>
                {courses.map((c: any) => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 600 }}>{c.name}</td>
                    <td>{c.provider || '—'}</td>
                    <td>
                      <span className={`badge ${c.is_mandatory ? 'badge-danger' : 'badge-success'}`}>
                        {c.is_mandatory ? 'Mandatory' : 'Optional'}
                      </span>
                    </td>
                    <td>{c.renewal_months > 0 ? `Every ${c.renewal_months} months` : 'No renewal'}</td>
                    <td>{c.reminder_days_before} days before</td>
                    {isManager && (
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <button className="btn btn-sm" onClick={() => handleToggleMandatory(c)} style={{ marginRight: 6 }}>
                          {c.is_mandatory ? 'Make Optional' : 'Make Mandatory'}
                        </button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteCourse(c.id)}>Remove</button>
                      </td>
                    )}
                  </tr>
                ))}
                {courses.length === 0 && <tr><td colSpan={isManager ? 6 : 5} className="empty-state">No courses configured yet. Add courses to get started.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* ── Compliance sub-tab ── */}
      {subTab === 'compliance' && isManager && (
        <>
          {compliance.length === 0 ? (
            <div className="empty-state">No mandatory courses configured. Add mandatory courses in the Courses tab to see compliance status.</div>
          ) : (
            compliance.map((course: any) => (
              <div key={course.course_id} style={{ marginBottom: 20 }}>
                <h3 style={{ fontSize: '1rem', marginBottom: 8 }}>
                  {course.course_name}
                  <span style={{ marginLeft: 8, fontSize: '0.75rem', color: '#dc2626', fontWeight: 600 }}>MANDATORY</span>
                </h3>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Staff</th><th>Status</th><th>Completed</th><th>Expiry</th><th>Days Left</th></tr></thead>
                    <tbody>
                      {course.staff.map((s: any) => {
                        const sc = STATUS_COLOURS[s.status] || STATUS_COLOURS.missing
                        return (
                          <tr key={s.staff_id}>
                            <td style={{ fontWeight: 600 }}>{s.staff_name}</td>
                            <td><span style={{ padding: '2px 8px', borderRadius: 4, fontSize: '0.8rem', fontWeight: 600, backgroundColor: sc.bg, color: sc.text }}>{sc.label}</span></td>
                            <td>{s.completed_date || '—'}</td>
                            <td>{s.expiry_date || '—'}</td>
                            <td>{s.days_until_expiry !== null ? `${s.days_until_expiry} days` : '—'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}
        </>
      )}

      {/* ── Reminders sub-tab ── */}
      {subTab === 'reminders' && (
        <>
          {reminders.length === 0 ? (
            <div className="empty-state">No training reminders — all training is up to date.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Staff</th><th>Course</th><th>Status</th><th>Expiry</th><th>Days</th></tr></thead>
                <tbody>
                  {reminders.map((r: any) => {
                    const isExpired = r.alert_type === 'expired'
                    return (
                      <tr key={r.id}>
                        <td style={{ fontWeight: 600 }}>{r.staff_name}</td>
                        <td>{r.title}</td>
                        <td>
                          <span className={`badge ${isExpired ? 'badge-danger' : 'badge-warning'}`}>
                            {isExpired ? 'EXPIRED' : 'EXPIRING SOON'}
                          </span>
                        </td>
                        <td>{r.expiry_date}</td>
                        <td style={{ fontWeight: 600, color: isExpired ? '#dc2626' : '#a16207' }}>
                          {r.days_until_expiry !== null ? (r.days_until_expiry < 0 ? `${Math.abs(r.days_until_expiry)} days overdue` : `${r.days_until_expiry} days left`) : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* ── Add Record Modal ── */}
      {showAddRecord && (
        <div className="modal-overlay" onClick={() => setShowAddRecord(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <h2 style={{ marginBottom: 12 }}>Add Training Record</h2>
            {recError && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{recError}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div>
                <label className="form-label">Staff Member *</label>
                <select className="form-input" value={recForm.staff} onChange={e => setRecForm({ ...recForm, staff: e.target.value })}>
                  <option value="">Select staff...</option>
                  {staff.map((s: any) => <option key={s.id} value={s.id}>{s.display_name}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">Course</label>
                <select className="form-input" value={recForm.course} onChange={e => handleCourseSelect(e.target.value)}>
                  <option value="">Select course (or enter manually below)...</option>
                  {courses.map((c: any) => <option key={c.id} value={c.id}>{c.name} {c.is_mandatory ? '(Mandatory)' : ''}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">Title *</label>
                <input className="form-input" value={recForm.title} onChange={e => setRecForm({ ...recForm, title: e.target.value })} placeholder="e.g. Manual Handling" />
              </div>
              <div>
                <label className="form-label">Provider</label>
                <input className="form-input" value={recForm.provider} onChange={e => setRecForm({ ...recForm, provider: e.target.value })} placeholder="e.g. SafetyFirst Ltd" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Completed Date *</label>
                  <input className="form-input" type="date" value={recForm.completed_date} onChange={e => setRecForm({ ...recForm, completed_date: e.target.value })} />
                </div>
                <div>
                  <label className="form-label">Expiry Date</label>
                  <input className="form-input" type="date" value={recForm.expiry_date} onChange={e => setRecForm({ ...recForm, expiry_date: e.target.value })} />
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>Auto-calculated if course has renewal period</div>
                </div>
              </div>
              <div>
                <label className="form-label">Certificate Reference</label>
                <input className="form-input" value={recForm.certificate_reference} onChange={e => setRecForm({ ...recForm, certificate_reference: e.target.value })} />
              </div>
              <div>
                <label className="form-label">Notes</label>
                <input className="form-input" value={recForm.notes} onChange={e => setRecForm({ ...recForm, notes: e.target.value })} />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowAddRecord(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={submitRecord} disabled={recSaving}>{recSaving ? 'Saving...' : 'Add Record'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Add Course Modal ── */}
      {showAddCourse && (
        <div className="modal-overlay" onClick={() => setShowAddCourse(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h2 style={{ marginBottom: 12 }}>Add Training Course</h2>
            {courseError && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{courseError}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div>
                <label className="form-label">Course Name *</label>
                <input className="form-input" value={courseForm.name} onChange={e => setCourseForm({ ...courseForm, name: e.target.value })} placeholder="e.g. Manual Handling" />
              </div>
              <div>
                <label className="form-label">Default Provider</label>
                <input className="form-input" value={courseForm.provider} onChange={e => setCourseForm({ ...courseForm, provider: e.target.value })} placeholder="e.g. SafetyFirst Ltd" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input type="checkbox" id="is_mandatory" checked={courseForm.is_mandatory} onChange={e => setCourseForm({ ...courseForm, is_mandatory: e.target.checked })} />
                <label htmlFor="is_mandatory" style={{ fontSize: '0.9rem' }}>Mandatory for all staff</label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Renewal Period (months)</label>
                  <input className="form-input" type="number" min="0" value={courseForm.renewal_months} onChange={e => setCourseForm({ ...courseForm, renewal_months: Number(e.target.value) })} />
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>0 = no renewal needed</div>
                </div>
                <div>
                  <label className="form-label">Reminder (days before expiry)</label>
                  <input className="form-input" type="number" min="0" value={courseForm.reminder_days_before} onChange={e => setCourseForm({ ...courseForm, reminder_days_before: Number(e.target.value) })} />
                </div>
              </div>
              <div>
                <label className="form-label">Description</label>
                <input className="form-input" value={courseForm.description} onChange={e => setCourseForm({ ...courseForm, description: e.target.value })} placeholder="Optional description" />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowAddCourse(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={submitCourse} disabled={courseSaving}>{courseSaving ? 'Saving...' : 'Add Course'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
