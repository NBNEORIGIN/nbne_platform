'use client'

import { useState, useEffect, useRef } from 'react'
import { getCmsPages, createCmsPage, updateCmsPage, deleteCmsPage, uploadCmsHero, uploadCmsImage, deleteCmsImage } from '@/lib/api'

export default function AdminCmsPage() {
  const [pages, setPages] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingPage, setEditingPage] = useState<any>(null)
  const [form, setForm] = useState({ title: '', slug: '', content: '', hero_headline: '', hero_subheadline: '', meta_title: '', meta_description: '', is_published: false, show_in_nav: true, sort_order: 0 })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [heroFile, setHeroFile] = useState<File | null>(null)
  const [galleryFiles, setGalleryFiles] = useState<File[]>([])
  const heroRef = useRef<HTMLInputElement>(null)
  const galleryRef = useRef<HTMLInputElement>(null)

  const load = async () => {
    setLoading(true)
    const res = await getCmsPages()
    setPages(res.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  function showToastMsg(msg: string) { setToast(msg); setTimeout(() => setToast(''), 3000) }

  function openAdd() {
    setForm({ title: '', slug: '', content: '', hero_headline: '', hero_subheadline: '', meta_title: '', meta_description: '', is_published: false, show_in_nav: true, sort_order: 0 })
    setEditingPage(null)
    setHeroFile(null)
    setGalleryFiles([])
    setError('')
    setShowModal(true)
  }

  function openEdit(p: any) {
    setForm({
      title: p.title || '',
      slug: p.slug || '',
      content: p.content || '',
      hero_headline: p.hero_headline || '',
      hero_subheadline: p.hero_subheadline || '',
      meta_title: p.meta_title || '',
      meta_description: p.meta_description || '',
      is_published: p.is_published ?? false,
      show_in_nav: p.show_in_nav ?? true,
      sort_order: p.sort_order || 0,
    })
    setEditingPage(p)
    setHeroFile(null)
    setGalleryFiles([])
    setError('')
    setShowModal(true)
  }

  async function handleSave() {
    if (!form.title.trim()) { setError('Title is required'); return }
    setSaving(true)
    setError('')

    const payload = { ...form, slug: form.slug || form.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') }
    let res
    if (editingPage) {
      res = await updateCmsPage(editingPage.id, payload)
    } else {
      res = await createCmsPage(payload)
    }
    if (res.error) { setSaving(false); setError(res.error); return }

    const pageId = res.data?.id || editingPage?.id
    if (pageId) {
      if (heroFile) {
        const hRes = await uploadCmsHero(pageId, heroFile)
        if (hRes.error) { setSaving(false); setError(`Saved but hero upload failed: ${hRes.error}`); load(); return }
      }
      for (const f of galleryFiles) {
        await uploadCmsImage(pageId, f)
      }
    }

    setSaving(false)
    setShowModal(false)
    showToastMsg(editingPage ? 'Page updated' : 'Page created')
    load()
  }

  async function handleDelete(p: any) {
    if (!confirm(`Delete page "${p.title}"? This cannot be undone.`)) return
    await deleteCmsPage(p.id)
    showToastMsg('Page deleted')
    load()
  }

  async function handleDeleteImage(pageId: number, imageId: number) {
    await deleteCmsImage(pageId, imageId)
    showToastMsg('Image removed')
    load()
  }

  async function togglePublish(p: any) {
    await updateCmsPage(p.id, { is_published: !p.is_published })
    load()
  }

  if (loading) return <div className="empty-state">Loading pages…</div>

  return (
    <div>
      {toast && <div style={{ position: 'fixed', top: 20, right: 20, background: 'var(--color-primary)', color: '#fff', padding: '0.6rem 1.2rem', borderRadius: 10, fontSize: '0.85rem', fontWeight: 600, zIndex: 9999, boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}>{toast}</div>}

      <div className="page-header"><h1>CMS Pages</h1></div>
      <p className="staff-header-sub">Edit your website pages — hero images, about sections, galleries and more.</p>

      <div className="status-strip">
        <div className="status-strip-item"><span className="status-strip-num">{pages.length}</span><span className="status-strip-label">Total</span></div>
        <div className="status-strip-item"><span className="status-strip-num" style={{ color: 'var(--color-success)' }}>{pages.filter(p => p.is_published).length}</span><span className="status-strip-label">Published</span></div>
        <div className="status-strip-item"><span className="status-strip-num">{pages.filter(p => !p.is_published).length}</span><span className="status-strip-label">Draft</span></div>
      </div>

      <div className="tab-subheader">
        <div className="tab-subheader-left" />
        <div className="tab-subheader-right">
          <button className="btn btn-primary" onClick={openAdd}>+ Add Page</button>
        </div>
      </div>

      {pages.length === 0 ? (
        <div className="empty-cta">
          <div className="empty-cta-title">No pages yet</div>
          <div className="empty-cta-desc">Create your first page — a homepage, about section, or gallery.</div>
          <button className="btn btn-primary" onClick={openAdd}>+ Add Page</button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Title</th><th>Slug</th><th>Status</th><th>Nav</th><th>Images</th><th>Actions</th></tr></thead>
            <tbody>
              {pages.map(p => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{p.title}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>/{p.slug}</td>
                  <td><span className={`badge ${p.is_published ? 'badge-success' : 'badge-neutral'}`}>{p.is_published ? 'Published' : 'Draft'}</span></td>
                  <td>{p.show_in_nav ? 'Yes' : '—'}</td>
                  <td>{(p.images || []).length + (p.hero_image_url ? 1 : 0)}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="btn btn-sm" onClick={() => openEdit(p)} style={{ marginRight: 6 }}>Edit</button>
                    <button className="btn btn-sm" onClick={() => togglePublish(p)} style={{ marginRight: 6 }}>{p.is_published ? 'Unpublish' : 'Publish'}</button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(p)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600, maxHeight: '90vh', overflowY: 'auto' }}>
            <h2 style={{ marginBottom: 16 }}>{editingPage ? 'Edit Page' : 'Add Page'}</h2>
            {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{error}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Page Title *</label>
                  <input className="form-input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="e.g. About Us" />
                </div>
                <div>
                  <label className="form-label">Slug</label>
                  <input className="form-input" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value })} placeholder="auto-generated" />
                </div>
              </div>

              <div>
                <label className="form-label">Hero Image</label>
                {editingPage?.hero_image_url && !heroFile && (
                  <div style={{ marginBottom: 8 }}>
                    <img src={editingPage.hero_image_url} alt="Hero" style={{ maxWidth: '100%', maxHeight: 120, objectFit: 'cover', borderRadius: 8 }} />
                  </div>
                )}
                <input ref={heroRef} type="file" accept="image/*" className="form-input" style={{ padding: '0.4rem' }} onChange={e => setHeroFile(e.target.files?.[0] || null)} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Hero Headline</label>
                  <input className="form-input" value={form.hero_headline} onChange={e => setForm({ ...form, hero_headline: e.target.value })} placeholder="Main headline text" />
                </div>
                <div>
                  <label className="form-label">Hero Subheadline</label>
                  <input className="form-input" value={form.hero_subheadline} onChange={e => setForm({ ...form, hero_subheadline: e.target.value })} placeholder="Supporting text" />
                </div>
              </div>

              <div>
                <label className="form-label">Page Content <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>(HTML supported)</span></label>
                <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius, 8px)', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', gap: 2, padding: '4px 6px', background: 'var(--color-bg-muted, #f8fafc)', borderBottom: '1px solid var(--color-border)' }}>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      const ta = document.getElementById('cms-content-ta') as HTMLTextAreaElement
                      if (!ta) return
                      const start = ta.selectionStart, end = ta.selectionEnd
                      const sel = form.content.substring(start, end)
                      setForm({ ...form, content: form.content.substring(0, start) + `<strong>${sel || 'bold text'}</strong>` + form.content.substring(end) })
                    }}><b>B</b></button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      const ta = document.getElementById('cms-content-ta') as HTMLTextAreaElement
                      if (!ta) return
                      const start = ta.selectionStart, end = ta.selectionEnd
                      const sel = form.content.substring(start, end)
                      setForm({ ...form, content: form.content.substring(0, start) + `<em>${sel || 'italic text'}</em>` + form.content.substring(end) })
                    }}><i>I</i></button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      setForm({ ...form, content: form.content + '\n<h2>Section Heading</h2>' })
                    }}>H2</button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      setForm({ ...form, content: form.content + '\n<ul>\n  <li>Item</li>\n</ul>' })
                    }}>List</button>
                  </div>
                  <textarea id="cms-content-ta" className="form-input" rows={8} value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} placeholder="Page content — supports HTML for formatting" style={{ border: 'none', borderRadius: 0, resize: 'vertical' }} />
                </div>
              </div>

              {/* Gallery images */}
              <div>
                <label className="form-label">Gallery Images</label>
                {editingPage?.images?.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                    {editingPage.images.map((img: any) => (
                      <div key={img.id} style={{ position: 'relative', width: 80, height: 80, borderRadius: 6, overflow: 'hidden', border: '1px solid var(--color-border)' }}>
                        <img src={img.url} alt={img.alt_text || ''} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        <button onClick={() => handleDeleteImage(editingPage.id, img.id)} style={{ position: 'absolute', top: 2, right: 2, background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', borderRadius: '50%', width: 18, height: 18, fontSize: '0.65rem', cursor: 'pointer', lineHeight: '18px', textAlign: 'center' }}>x</button>
                      </div>
                    ))}
                  </div>
                )}
                <input ref={galleryRef} type="file" accept="image/*" multiple className="form-input" style={{ padding: '0.4rem' }} onChange={e => setGalleryFiles(Array.from(e.target.files || []))} />
              </div>

              {/* SEO */}
              <details style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius, 8px)', padding: '0.5rem 0.75rem' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.88rem' }}>SEO Settings</summary>
                <div style={{ display: 'grid', gap: 10, marginTop: 10 }}>
                  <div>
                    <label className="form-label">Meta Title</label>
                    <input className="form-input" value={form.meta_title} onChange={e => setForm({ ...form, meta_title: e.target.value })} placeholder="SEO page title (falls back to page title)" />
                  </div>
                  <div>
                    <label className="form-label">Meta Description</label>
                    <textarea className="form-input" rows={2} value={form.meta_description} onChange={e => setForm({ ...form, meta_description: e.target.value })} placeholder="Brief description for search engines (max 160 chars)" />
                  </div>
                </div>
              </details>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Sort Order</label>
                  <input className="form-input" type="number" value={form.sort_order} onChange={e => setForm({ ...form, sort_order: +e.target.value })} />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.88rem', cursor: 'pointer' }}>
                    <input type="checkbox" checked={form.is_published} onChange={e => setForm({ ...form, is_published: e.target.checked })} />
                    Published
                  </label>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 4 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.88rem', cursor: 'pointer' }}>
                    <input type="checkbox" checked={form.show_in_nav} onChange={e => setForm({ ...form, show_in_nav: e.target.checked })} />
                    Show in Nav
                  </label>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Saving…' : editingPage ? 'Save Changes' : 'Create Page'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
