'use client'

import { useState, useEffect } from 'react'
import { getProducts, createProduct, updateProduct, deleteProduct, getOrders, updateOrder } from '@/lib/api'

type Product = {
  id: number; name: string; description: string; category: string;
  price: string; image_url: string; stock_quantity: number;
  track_stock: boolean; in_stock: boolean; sort_order: number; active: boolean;
}
type Order = {
  id: number; customer_name: string; customer_email: string; customer_phone: string;
  status: string; total_pence: number; items: { id: number; product_name: string; quantity: number; unit_price_pence: number }[];
  created_at: string;
}

const STATUS_COLOURS: Record<string, string> = {
  pending: '#f59e0b', paid: '#10b981', processing: '#3b82f6',
  shipped: '#6366f1', completed: '#059669', cancelled: '#ef4444', refunded: '#6b7280',
}

const EMPTY_PRODUCT = { name: '', description: '', category: '', price: '0.00', image_url: '', stock_quantity: 0, track_stock: false, sort_order: 0, active: true }

export default function ShopPage() {
  const [tab, setTab] = useState<'products' | 'orders'>('products')
  const [products, setProducts] = useState<Product[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<Partial<Product> | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    const [p, o] = await Promise.all([getProducts({ all: true }), getOrders()])
    if (Array.isArray(p)) setProducts(p)
    if (Array.isArray(o)) setOrders(o)
    setLoading(false)
  }

  async function handleSave() {
    if (!editing?.name?.trim()) return
    setSaving(true)
    try {
      if (editing.id) {
        await updateProduct(editing.id, editing)
      } else {
        await createProduct(editing)
      }
      setEditing(null)
      await loadData()
    } catch { /* ignore */ }
    setSaving(false)
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this product?')) return
    await deleteProduct(id)
    await loadData()
  }

  async function handleOrderStatus(id: number, status: string) {
    await updateOrder(id, { status })
    await loadData()
  }

  const categories = Array.from(new Set(products.map(p => p.category).filter(Boolean)))

  return (
    <div>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.25rem' }}>Shop</h1>
      <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>Manage products and orders.</p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {(['products', 'orders'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '0.5rem 1.25rem', borderRadius: 8, border: 'none', fontWeight: 700,
            background: tab === t ? '#0f172a' : '#f1f5f9', color: tab === t ? '#fff' : '#64748b',
            cursor: 'pointer', fontSize: '0.85rem', textTransform: 'capitalize',
          }}>{t} {t === 'products' ? `(${products.length})` : `(${orders.length})`}</button>
        ))}
        {tab === 'products' && (
          <button onClick={() => setEditing({ ...EMPTY_PRODUCT })} style={{
            marginLeft: 'auto', padding: '0.5rem 1.25rem', borderRadius: 8, border: 'none',
            background: '#2563eb', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem',
          }}>+ Add Product</button>
        )}
      </div>

      {loading && <p style={{ color: '#94a3b8' }}>Loading...</p>}

      {/* Product Form Modal */}
      {editing && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem',
        }}>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '1.5rem', width: '100%', maxWidth: 500,
            boxShadow: '0 8px 40px rgba(0,0,0,0.15)',
          }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
              {editing.id ? 'Edit Product' : 'Add Product'}
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <input placeholder="Product name" value={editing.name || ''} onChange={e => setEditing({ ...editing, name: e.target.value })}
                style={{ padding: '0.6rem 0.75rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.9rem' }} />
              <textarea placeholder="Description" value={editing.description || ''} onChange={e => setEditing({ ...editing, description: e.target.value })}
                rows={3} style={{ padding: '0.6rem 0.75rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.9rem', resize: 'vertical' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <input placeholder="Category" value={editing.category || ''} onChange={e => setEditing({ ...editing, category: e.target.value })}
                  list="categories" style={{ padding: '0.6rem 0.75rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.9rem' }} />
                <datalist id="categories">{categories.map(c => <option key={c} value={c} />)}</datalist>
                <input type="number" step="0.01" min="0" placeholder="Price (£)" value={editing.price || ''} onChange={e => setEditing({ ...editing, price: e.target.value })}
                  style={{ padding: '0.6rem 0.75rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.9rem' }} />
              </div>
              <input placeholder="Image URL" value={editing.image_url || ''} onChange={e => setEditing({ ...editing, image_url: e.target.value })}
                style={{ padding: '0.6rem 0.75rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.9rem' }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
                  <input type="checkbox" checked={editing.track_stock || false} onChange={e => setEditing({ ...editing, track_stock: e.target.checked })} />
                  Track stock
                </label>
                {editing.track_stock && (
                  <input type="number" min="0" placeholder="Qty" value={editing.stock_quantity || 0} onChange={e => setEditing({ ...editing, stock_quantity: parseInt(e.target.value) || 0 })}
                    style={{ width: 80, padding: '0.4rem 0.5rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem' }} />
                )}
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', marginLeft: 'auto' }}>
                  <input type="checkbox" checked={editing.active !== false} onChange={e => setEditing({ ...editing, active: e.target.checked })} />
                  Active
                </label>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
              <button onClick={() => setEditing(null)} style={{ padding: '0.5rem 1rem', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: '0.85rem' }}>Cancel</button>
              <button onClick={handleSave} disabled={saving} style={{
                padding: '0.5rem 1.25rem', borderRadius: 6, border: 'none',
                background: saving ? '#93c5fd' : '#2563eb', color: '#fff', fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', fontSize: '0.85rem',
              }}>{saving ? 'Saving...' : 'Save'}</button>
            </div>
          </div>
        </div>
      )}

      {/* Products Tab */}
      {tab === 'products' && !loading && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Product</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Category</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Price</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Stock</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map(p => (
                <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {p.image_url && <img src={p.image_url} alt="" style={{ width: 40, height: 40, borderRadius: 6, objectFit: 'cover' }} />}
                      <div>
                        <div style={{ fontWeight: 600 }}>{p.name}</div>
                        {p.description && <div style={{ fontSize: '0.78rem', color: '#94a3b8', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.description}</div>}
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '0.75rem', color: '#64748b' }}>{p.category || '—'}</td>
                  <td style={{ padding: '0.75rem', fontWeight: 600 }}>£{Number(p.price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>
                    {p.track_stock ? (
                      <span style={{ color: p.stock_quantity > 0 ? '#059669' : '#ef4444', fontWeight: 600 }}>{p.stock_quantity}</span>
                    ) : <span style={{ color: '#94a3b8' }}>∞</span>}
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{
                      padding: '0.2rem 0.6rem', borderRadius: 12, fontSize: '0.75rem', fontWeight: 700,
                      background: p.active ? '#dcfce7' : '#fee2e2', color: p.active ? '#166534' : '#991b1b',
                    }}>{p.active ? 'Active' : 'Inactive'}</span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button onClick={() => setEditing(p)} style={{ padding: '0.3rem 0.75rem', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600 }}>Edit</button>
                      <button onClick={() => handleDelete(p.id)} style={{ padding: '0.3rem 0.75rem', borderRadius: 6, border: 'none', background: '#ef4444', color: '#fff', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600 }}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr><td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No products yet. Click "+ Add Product" to get started.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Orders Tab */}
      {tab === 'orders' && !loading && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Order</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Customer</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Items</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Total</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '0.6rem 0.75rem', color: '#64748b', fontWeight: 600, fontSize: '0.78rem', textTransform: 'uppercase' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: 600 }}>#{o.id}</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{new Date(o.created_at).toLocaleDateString()}</div>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: 600 }}>{o.customer_name}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{o.customer_email}</div>
                  </td>
                  <td style={{ padding: '0.75rem', fontSize: '0.8rem', color: '#64748b' }}>
                    {o.items?.map(i => `${i.quantity}x ${i.product_name}`).join(', ') || '—'}
                  </td>
                  <td style={{ padding: '0.75rem', fontWeight: 600 }}>£{(o.total_pence / 100).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{
                      padding: '0.2rem 0.6rem', borderRadius: 12, fontSize: '0.75rem', fontWeight: 700,
                      background: `${STATUS_COLOURS[o.status] || '#94a3b8'}20`, color: STATUS_COLOURS[o.status] || '#94a3b8',
                    }}>{o.status}</span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <select value={o.status} onChange={e => handleOrderStatus(o.id, e.target.value)}
                      style={{ padding: '0.3rem 0.5rem', borderRadius: 6, border: '1px solid #d1d5db', fontSize: '0.78rem', cursor: 'pointer' }}>
                      {['pending', 'paid', 'processing', 'shipped', 'completed', 'cancelled', 'refunded'].map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr><td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No orders yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
