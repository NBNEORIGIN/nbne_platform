'use client'

import { useState, useEffect, useRef } from 'react'
import { getBlogPosts, createBlogPost, updateBlogPost, deleteBlogPost, uploadBlogImage } from '@/lib/api'

export default function AdminBlogPage() {
  const [posts, setPosts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingPost, setEditingPost] = useState<any>(null)
  const [form, setForm] = useState({ title: '', slug: '', excerpt: '', content: '', author_name: '', category: '', tags: '', status: 'draft' as 'draft' | 'published', meta_title: '', meta_description: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [filter, setFilter] = useState<'all' | 'published' | 'draft'>('all')
  const imgRef = useRef<HTMLInputElement>(null)

  const load = async () => {
    setLoading(true)
    const res = await getBlogPosts()
    setPosts(res.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  function showToastMsg(msg: string) { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const blogCategories = Array.from(new Set(posts.map(p => p.category).filter(Boolean)))
  const published = posts.filter(p => p.status === 'published')
  const drafts = posts.filter(p => p.status === 'draft')
  const filtered = filter === 'published' ? published : filter === 'draft' ? drafts : posts

  function openAdd() {
    setForm({ title: '', slug: '', excerpt: '', content: '', author_name: '', category: '', tags: '', status: 'draft', meta_title: '', meta_description: '' })
    setEditingPost(null)
    setImageFile(null)
    setError('')
    setShowModal(true)
  }

  function openEdit(p: any) {
    setForm({
      title: p.title || '',
      slug: p.slug || '',
      excerpt: p.excerpt || '',
      content: p.content || '',
      author_name: p.author_name || '',
      category: p.category || '',
      tags: p.tags || '',
      status: p.status || 'draft',
      meta_title: p.meta_title || '',
      meta_description: p.meta_description || '',
    })
    setEditingPost(p)
    setImageFile(null)
    setError('')
    setShowModal(true)
  }

  async function handleSave() {
    if (!form.title.trim()) { setError('Title is required'); return }
    setSaving(true)
    setError('')

    const payload = { ...form, slug: form.slug || form.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') }
    let res
    if (editingPost) {
      res = await updateBlogPost(editingPost.id, payload)
    } else {
      res = await createBlogPost(payload)
    }
    if (res.error) { setSaving(false); setError(res.error); return }

    const postId = res.data?.id || editingPost?.id
    if (postId && imageFile) {
      const iRes = await uploadBlogImage(postId, imageFile)
      if (iRes.error) { setSaving(false); setError(`Saved but image upload failed: ${iRes.error}`); load(); return }
    }

    setSaving(false)
    setShowModal(false)
    showToastMsg(editingPost ? 'Post updated' : 'Post created')
    load()
  }

  async function handleDelete(p: any) {
    if (!confirm(`Delete "${p.title}"? This cannot be undone.`)) return
    await deleteBlogPost(p.id)
    showToastMsg('Post deleted')
    load()
  }

  async function toggleStatus(p: any) {
    const newStatus = p.status === 'published' ? 'draft' : 'published'
    await updateBlogPost(p.id, { status: newStatus })
    load()
  }

  function fmtDate(d: string | null) {
    if (!d) return '—'
    return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  if (loading) return <div className="empty-state">Loading blog posts…</div>

  return (
    <div>
      {toast && <div style={{ position: 'fixed', top: 20, right: 20, background: 'var(--color-primary)', color: '#fff', padding: '0.6rem 1.2rem', borderRadius: 10, fontSize: '0.85rem', fontWeight: 600, zIndex: 9999, boxShadow: '0 4px 20px rgba(0,0,0,0.15)' }}>{toast}</div>}

      <div className="page-header"><h1>Blog</h1></div>
      <p className="staff-header-sub">Write blog posts to boost your SEO and keep customers informed.</p>

      <div className="status-strip">
        <div className="status-strip-item"><span className="status-strip-num">{posts.length}</span><span className="status-strip-label">Total</span></div>
        <div className="status-strip-item"><span className="status-strip-num" style={{ color: 'var(--color-success)' }}>{published.length}</span><span className="status-strip-label">Published</span></div>
        <div className="status-strip-item"><span className="status-strip-num">{drafts.length}</span><span className="status-strip-label">Drafts</span></div>
      </div>

      <div className="tab-subheader">
        <div className="tab-subheader-left">
          <div className="filter-pills">
            <button className={`filter-pill ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All ({posts.length})</button>
            <button className={`filter-pill ${filter === 'published' ? 'active' : ''}`} onClick={() => setFilter('published')}>Published ({published.length})</button>
            <button className={`filter-pill ${filter === 'draft' ? 'active' : ''}`} onClick={() => setFilter('draft')}>Drafts ({drafts.length})</button>
          </div>
        </div>
        <div className="tab-subheader-right">
          <button className="btn btn-primary" onClick={openAdd}>+ New Post</button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-cta">
          <div className="empty-cta-title">{filter === 'all' ? 'No blog posts yet' : `No ${filter} posts`}</div>
          <div className="empty-cta-desc">Blog posts help your Google ranking. Write about your services, tips, and industry news.</div>
          <button className="btn btn-primary" onClick={openAdd}>+ New Post</button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Title</th><th>Category</th><th>Status</th><th>Published</th><th>Actions</th></tr></thead>
            <tbody>
              {filtered.map(p => (
                <tr key={p.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {p.featured_image_url && <img src={p.featured_image_url} alt="" style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 6, flexShrink: 0 }} />}
                      <div>
                        <div style={{ fontWeight: 600 }}>{p.title}</div>
                        {p.excerpt && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.excerpt}</div>}
                      </div>
                    </div>
                  </td>
                  <td>{p.category || '—'}</td>
                  <td><span className={`badge ${p.status === 'published' ? 'badge-success' : 'badge-neutral'}`}>{p.status === 'published' ? 'Published' : 'Draft'}</span></td>
                  <td style={{ fontSize: '0.85rem' }}>{fmtDate(p.published_at)}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="btn btn-sm" onClick={() => openEdit(p)} style={{ marginRight: 6 }}>Edit</button>
                    <button className="btn btn-sm" onClick={() => toggleStatus(p)} style={{ marginRight: 6 }}>{p.status === 'published' ? 'Unpublish' : 'Publish'}</button>
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
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 640, maxHeight: '90vh', overflowY: 'auto' }}>
            <h2 style={{ marginBottom: 16 }}>{editingPost ? 'Edit Post' : 'New Blog Post'}</h2>
            {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}>{error}</div>}
            <div style={{ display: 'grid', gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Title *</label>
                  <input className="form-input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Blog post title" />
                </div>
                <div>
                  <label className="form-label">Slug</label>
                  <input className="form-input" value={form.slug} onChange={e => setForm({ ...form, slug: e.target.value })} placeholder="auto-generated" />
                </div>
              </div>

              <div>
                <label className="form-label">Excerpt</label>
                <textarea className="form-input" rows={2} value={form.excerpt} onChange={e => setForm({ ...form, excerpt: e.target.value })} placeholder="Short summary shown in blog listings and search results" />
              </div>

              <div>
                <label className="form-label">Content <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>(HTML supported)</span></label>
                <div style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius, 8px)', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', gap: 2, padding: '4px 6px', background: 'var(--color-bg-muted, #f8fafc)', borderBottom: '1px solid var(--color-border)' }}>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      const ta = document.getElementById('blog-content-ta') as HTMLTextAreaElement
                      if (!ta) return
                      const start = ta.selectionStart, end = ta.selectionEnd
                      const sel = form.content.substring(start, end)
                      setForm({ ...form, content: form.content.substring(0, start) + `<strong>${sel || 'bold text'}</strong>` + form.content.substring(end) })
                    }}><b>B</b></button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      const ta = document.getElementById('blog-content-ta') as HTMLTextAreaElement
                      if (!ta) return
                      const start = ta.selectionStart, end = ta.selectionEnd
                      const sel = form.content.substring(start, end)
                      setForm({ ...form, content: form.content.substring(0, start) + `<em>${sel || 'italic text'}</em>` + form.content.substring(end) })
                    }}><i>I</i></button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      setForm({ ...form, content: form.content + '\n<h2>Section Heading</h2>' })
                    }}>H2</button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      setForm({ ...form, content: form.content + '\n<h3>Sub Heading</h3>' })
                    }}>H3</button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      setForm({ ...form, content: form.content + '\n<ul>\n  <li>Item</li>\n</ul>' })
                    }}>List</button>
                    <button type="button" className="btn btn-sm" style={{ padding: '2px 8px', fontSize: '0.78rem' }} onClick={() => {
                      setForm({ ...form, content: form.content + '\n<blockquote>Quote text</blockquote>' })
                    }}>Quote</button>
                  </div>
                  <textarea id="blog-content-ta" className="form-input" rows={10} value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} placeholder="Write your blog post content here…&#10;Supports HTML: <h2>, <h3>, <strong>, <em>, <ul>, <blockquote>, <p>, <a>" style={{ border: 'none', borderRadius: 0, resize: 'vertical' }} />
                </div>
              </div>

              <div>
                <label className="form-label">Featured Image</label>
                {editingPost?.featured_image_url && !imageFile && (
                  <div style={{ marginBottom: 8 }}>
                    <img src={editingPost.featured_image_url} alt="" style={{ maxWidth: '100%', maxHeight: 120, objectFit: 'cover', borderRadius: 8 }} />
                  </div>
                )}
                <input ref={imgRef} type="file" accept="image/*" className="form-input" style={{ padding: '0.4rem' }} onChange={e => setImageFile(e.target.files?.[0] || null)} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div>
                  <label className="form-label">Author</label>
                  <input className="form-input" value={form.author_name} onChange={e => setForm({ ...form, author_name: e.target.value })} placeholder="Author name" />
                </div>
                <div>
                  <label className="form-label">Category</label>
                  <input className="form-input" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} placeholder="e.g. Tips, News" list="blog-cat-list" />
                  <datalist id="blog-cat-list">{blogCategories.map(c => <option key={c} value={c} />)}</datalist>
                </div>
                <div>
                  <label className="form-label">Tags</label>
                  <input className="form-input" value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} placeholder="safety, training" />
                </div>
              </div>

              <div>
                <label className="form-label">Status</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className={`filter-pill ${form.status === 'draft' ? 'active' : ''}`} onClick={() => setForm({ ...form, status: 'draft' })}>Draft</button>
                  <button type="button" className={`filter-pill ${form.status === 'published' ? 'active' : ''}`} onClick={() => setForm({ ...form, status: 'published' })}>Published</button>
                </div>
              </div>

              {/* SEO */}
              <details style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius, 8px)', padding: '0.5rem 0.75rem' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.88rem' }}>SEO Settings</summary>
                <div style={{ display: 'grid', gap: 10, marginTop: 10 }}>
                  <div>
                    <label className="form-label">Meta Title</label>
                    <input className="form-input" value={form.meta_title} onChange={e => setForm({ ...form, meta_title: e.target.value })} placeholder="SEO title (falls back to post title)" />
                  </div>
                  <div>
                    <label className="form-label">Meta Description</label>
                    <textarea className="form-input" rows={2} value={form.meta_description} onChange={e => setForm({ ...form, meta_description: e.target.value })} placeholder="Brief description for search engines (max 160 chars)" />
                  </div>
                </div>
              </details>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button className="btn" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Saving…' : editingPost ? 'Save Changes' : 'Create Post'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
