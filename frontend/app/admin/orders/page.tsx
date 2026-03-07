'use client'

import { useState, useEffect } from 'react'
import { useTenant } from '@/lib/tenant'
import {
  getMenuCategories, getMenuItems, createMenuCategory, updateMenuCategory,
  createMenuItem, updateMenuItem, deleteMenuItem, toggleMenuItemSoldOut,
  getOrderHistory, getOrdersToday, getOrderQueueSettings, updateOrderQueueSettings,
  getOrderDailySummary, getOrderDemandPrediction, getOrderWeekPrediction,
  getOrderProcurement, getOrderSalesTrends, getOrderPopularItems,
  getOrderHolidayCalendar,
} from '@/lib/api'

type Tab = 'dashboard' | 'menu' | 'orders' | 'analytics' | 'procurement' | 'settings'

export default function OrdersAdminPage() {
  const tenant = useTenant()
  const accent = tenant.colour_primary || '#dc2626'
  const [tab, setTab] = useState<Tab>('dashboard')

  const tabs: { key: Tab; label: string }[] = [
    { key: 'dashboard', label: '📊 Dashboard' },
    { key: 'menu', label: '🍕 Menu' },
    { key: 'orders', label: '📋 Orders' },
    { key: 'analytics', label: '📈 Analytics' },
    { key: 'procurement', label: '🛒 Procurement' },
    { key: 'settings', label: '⚙️ Settings' },
  ]

  return (
    <div style={{ padding: 20 }}>
      <h1 style={{ fontSize: '1.5rem', marginBottom: 16 }}>Orders & Menu</h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '8px 16px', borderRadius: 8, border: 'none',
              background: tab === t.key ? accent : '#f3f4f6',
              color: tab === t.key ? '#fff' : '#333',
              fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'dashboard' && <DashboardTab accent={accent} />}
      {tab === 'menu' && <MenuTab accent={accent} />}
      {tab === 'orders' && <OrdersTab accent={accent} />}
      {tab === 'analytics' && <AnalyticsTab accent={accent} />}
      {tab === 'procurement' && <ProcurementTab accent={accent} />}
      {tab === 'settings' && <SettingsTab accent={accent} />}
    </div>
  )
}

// ── Dashboard ──
function DashboardTab({ accent }: { accent: string }) {
  const [data, setData] = useState<any>(null)
  const [trends, setTrends] = useState<any>(null)
  const [popular, setPopular] = useState<any>(null)

  useEffect(() => {
    getOrdersToday().then(r => setData(r.data))
    getOrderSalesTrends(7).then(r => setTrends(r.data))
    getOrderPopularItems({ days: 7, limit: 5 }).then(r => setPopular(r.data))
  }, [])

  if (!data) return <p>Loading...</p>

  const statCards = [
    { label: 'Orders Today', value: data.total_orders, icon: '📋' },
    { label: 'Active Now', value: data.active_orders, icon: '🔥', color: data.active_orders > 5 ? '#f59e0b' : undefined },
    { label: 'Ready', value: data.ready_orders, icon: '✅' },
    { label: 'Completed', value: data.completed_orders, icon: '📦' },
    { label: 'Revenue', value: data.total_revenue_display, icon: '💰' },
    { label: 'Wait Time', value: `~${data.current_wait_minutes}min`, icon: '⏱' },
  ]

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 12, marginBottom: 24 }}>
        {statCards.map(s => (
          <div key={s.label} style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 4 }}>{s.icon}</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: s.color || '#333' }}>{s.value}</div>
            <div style={{ fontSize: '0.8rem', color: '#888' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {trends && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>📈 7-Day Trend</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <TrendStat label="Orders" current={trends.current?.total_orders} change={trends.change?.orders_pct} />
            <TrendStat label="Revenue" current={`£${((trends.current?.total_revenue_pence || 0) / 100).toFixed(0)}`} change={trends.change?.revenue_pct} />
            <TrendStat label="Items Sold" current={trends.current?.total_items} change={trends.change?.items_pct} />
          </div>
        </div>
      )}

      {popular?.items?.length > 0 && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>🏆 Top Sellers (7 days)</h3>
          {popular.items.map((item: any, i: number) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f3f4f6' }}>
              <span>{i + 1}. {item.menu_item__name}</span>
              <span style={{ fontWeight: 600 }}>{item.total_qty} sold</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function TrendStat({ label, current, change }: { label: string; current: any; change: number }) {
  const isUp = change > 0
  return (
    <div>
      <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{current}</div>
      <div style={{ fontSize: '0.8rem', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: isUp ? '#16a34a' : change < 0 ? '#dc2626' : '#888' }}>
        {isUp ? '↑' : change < 0 ? '↓' : '→'} {Math.abs(change || 0)}%
      </div>
    </div>
  )
}

// ── Menu Management ──
function MenuTab({ accent }: { accent: string }) {
  const [categories, setCategories] = useState<any[]>([])
  const [items, setItems] = useState<any[]>([])
  const [selectedCat, setSelectedCat] = useState<number | null>(null)
  const [showAddItem, setShowAddItem] = useState(false)
  const [editingItem, setEditingItem] = useState<any>(null)
  const [newCatName, setNewCatName] = useState('')

  const loadCategories = () => getMenuCategories(true).then(r => setCategories(r.data || []))
  const loadItems = (catId?: number) => {
    const params: any = { all: true }
    if (catId) params.category = catId
    getMenuItems(params).then(r => setItems(r.data || []))
  }

  useEffect(() => { loadCategories(); loadItems() }, [])

  const handleAddCategory = async () => {
    if (!newCatName.trim()) return
    await createMenuCategory({ name: newCatName.trim(), sort_order: categories.length })
    setNewCatName('')
    loadCategories()
  }

  const handleSaveItem = async (data: any) => {
    if (editingItem?.id) {
      await updateMenuItem(editingItem.id, data)
    } else {
      await createMenuItem(data)
    }
    setShowAddItem(false)
    setEditingItem(null)
    loadItems(selectedCat || undefined)
  }

  const handleToggleSoldOut = async (id: number) => {
    await toggleMenuItemSoldOut(id)
    loadItems(selectedCat || undefined)
  }

  const filteredItems = selectedCat ? items.filter(i => i.category === selectedCat) : items

  return (
    <div>
      {/* Categories */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <button onClick={() => { setSelectedCat(null); loadItems() }} style={{
          padding: '6px 14px', borderRadius: 20, border: 'none',
          background: selectedCat === null ? accent : '#f3f4f6',
          color: selectedCat === null ? '#fff' : '#333',
          fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
        }}>All</button>
        {categories.map(cat => (
          <button key={cat.id} onClick={() => { setSelectedCat(cat.id); loadItems(cat.id) }} style={{
            padding: '6px 14px', borderRadius: 20, border: 'none',
            background: selectedCat === cat.id ? accent : '#f3f4f6',
            color: selectedCat === cat.id ? '#fff' : '#333',
            fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
          }}>{cat.name} ({cat.item_count})</button>
        ))}
        <div style={{ display: 'flex', gap: 4 }}>
          <input value={newCatName} onChange={e => setNewCatName(e.target.value)} placeholder="New category" style={{ padding: '6px 10px', border: '1px solid #ddd', borderRadius: 8, fontSize: '0.85rem' }} />
          <button onClick={handleAddCategory} style={{ padding: '6px 10px', background: accent, color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem' }}>+</button>
        </div>
      </div>

      {/* Add item button */}
      <button onClick={() => { setEditingItem(null); setShowAddItem(true) }} style={{
        padding: '8px 16px', background: accent, color: '#fff', border: 'none', borderRadius: 8,
        fontWeight: 600, cursor: 'pointer', marginBottom: 16,
      }}>+ Add Menu Item</button>

      {/* Item form */}
      {(showAddItem || editingItem) && (
        <ItemForm
          item={editingItem}
          categories={categories}
          accent={accent}
          onSave={handleSaveItem}
          onCancel={() => { setShowAddItem(false); setEditingItem(null) }}
        />
      )}

      {/* Items list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filteredItems.map(item => (
          <div key={item.id} style={{
            background: '#fff', borderRadius: 10, padding: 14,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            opacity: item.active ? 1 : 0.5,
          }}>
            <div>
              <div style={{ fontWeight: 600 }}>
                {item.name}
                {item.sold_out && <span style={{ color: '#dc2626', fontSize: '0.75rem', marginLeft: 8 }}>SOLD OUT</span>}
                {!item.active && <span style={{ color: '#888', fontSize: '0.75rem', marginLeft: 8 }}>INACTIVE</span>}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#888' }}>
                {item.category_name} • £{(item.price_pence / 100).toFixed(2)} • {item.prep_time_minutes}min prep
                {item.vegetarian && ' • 🌿'}{item.vegan && ' • 🌱'}{item.gluten_free && ' • 🌾'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#aaa' }}>
                {item.total_ordered} ordered • £{(item.total_revenue_pence / 100).toFixed(2)} revenue
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => handleToggleSoldOut(item.id)} style={{
                padding: '4px 10px', border: '1px solid #ddd', borderRadius: 6, background: item.sold_out ? '#fef2f2' : '#fff',
                cursor: 'pointer', fontSize: '0.8rem',
              }}>{item.sold_out ? '✅ Restock' : '🚫 Sold Out'}</button>
              <button onClick={() => setEditingItem(item)} style={{
                padding: '4px 10px', border: '1px solid #ddd', borderRadius: 6, background: '#fff',
                cursor: 'pointer', fontSize: '0.8rem',
              }}>✏️ Edit</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ItemForm({ item, categories, accent, onSave, onCancel }: {
  item: any; categories: any[]; accent: string; onSave: (data: any) => void; onCancel: () => void
}) {
  const [name, setName] = useState(item?.name || '')
  const [desc, setDesc] = useState(item?.description || '')
  const [pricePence, setPricePence] = useState(item?.price_pence?.toString() || '')
  const [category, setCategory] = useState(item?.category?.toString() || categories[0]?.id?.toString() || '')
  const [prepTime, setPrepTime] = useState(item?.prep_time_minutes?.toString() || '10')
  const [vegetarian, setVegetarian] = useState(item?.vegetarian || false)
  const [vegan, setVegan] = useState(item?.vegan || false)
  const [glutenFree, setGlutenFree] = useState(item?.gluten_free || false)
  const [active, setActive] = useState(item?.active ?? true)

  const handleSubmit = () => {
    onSave({
      name, description: desc, price_pence: parseInt(pricePence) || 0,
      category: parseInt(category), prep_time_minutes: parseInt(prepTime) || 10,
      vegetarian, vegan, gluten_free: glutenFree, active,
    })
  }

  const fs: React.CSSProperties = { width: '100%', padding: '8px 12px', border: '1px solid #ddd', borderRadius: 8, fontSize: '0.9rem', marginBottom: 8, boxSizing: 'border-box' }

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', maxWidth: 500 }}>
      <h3 style={{ marginBottom: 12 }}>{item?.id ? 'Edit Item' : 'Add Item'}</h3>
      <input value={name} onChange={e => setName(e.target.value)} placeholder="Item name" style={fs} />
      <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" style={fs} />
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input value={pricePence} onChange={e => setPricePence(e.target.value)} placeholder="Price (pence)" type="number" style={{ ...fs, flex: 1, marginBottom: 0 }} />
        <input value={prepTime} onChange={e => setPrepTime(e.target.value)} placeholder="Prep (min)" type="number" style={{ ...fs, flex: 1, marginBottom: 0 }} />
      </div>
      <select value={category} onChange={e => setCategory(e.target.value)} style={{ ...fs }}>
        {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
      <div style={{ display: 'flex', gap: 16, marginBottom: 12, fontSize: '0.9rem' }}>
        <label><input type="checkbox" checked={vegetarian} onChange={e => setVegetarian(e.target.checked)} /> 🌿 Vegetarian</label>
        <label><input type="checkbox" checked={vegan} onChange={e => setVegan(e.target.checked)} /> 🌱 Vegan</label>
        <label><input type="checkbox" checked={glutenFree} onChange={e => setGlutenFree(e.target.checked)} /> 🌾 GF</label>
        <label><input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} /> Active</label>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={handleSubmit} style={{ padding: '8px 16px', background: accent, color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>Save</button>
        <button onClick={onCancel} style={{ padding: '8px 16px', background: '#f3f4f6', border: 'none', borderRadius: 8, cursor: 'pointer' }}>Cancel</button>
      </div>
    </div>
  )
}

// ── Orders History ──
function OrdersTab({ accent }: { accent: string }) {
  const [orders, setOrders] = useState<any>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  const load = (params?: any) => getOrderHistory({ ...params, limit: 50 }).then(r => setOrders(r.data))

  useEffect(() => { load() }, [])

  const handleFilter = () => load({ status: statusFilter || undefined, search: search || undefined })

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: 8 }}>
          <option value="">All statuses</option>
          <option value="received">Received</option>
          <option value="preparing">Preparing</option>
          <option value="ready">Ready</option>
          <option value="collected">Collected</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name / ref" style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: 8 }} />
        <button onClick={handleFilter} style={{ padding: '8px 16px', background: accent, color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer' }}>Filter</button>
      </div>

      {!orders ? <p>Loading...</p> : (
        <div>
          <p style={{ fontSize: '0.85rem', color: '#888', marginBottom: 8 }}>{orders.total} orders</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {orders.results?.map((o: any) => (
              <div key={o.id} style={{ background: '#fff', borderRadius: 8, padding: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
                <div>
                  <span style={{ fontWeight: 700, marginRight: 8 }}>#{o.order_ref}</span>
                  <span>{o.customer_name}</span>
                  <span style={{ color: '#888', marginLeft: 8, fontSize: '0.8rem' }}>{o.source_display}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: '0.85rem' }}>
                  <span>{o.total_display}</span>
                  <span style={{ fontWeight: 600 }}>{o.status_display}</span>
                  <span style={{ color: '#888' }}>{new Date(o.placed_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Analytics ──
function AnalyticsTab({ accent }: { accent: string }) {
  const [dailyData, setDailyData] = useState<any[]>([])
  const [days, setDays] = useState(30)
  const [holidays, setHolidays] = useState<any>(null)

  useEffect(() => {
    getOrderDailySummary(days).then(r => setDailyData(r.data || []))
    getOrderHolidayCalendar().then(r => setHolidays(r.data))
  }, [days])

  const totalOrders = dailyData.reduce((s, d) => s + d.total_orders, 0)
  const totalRevenue = dailyData.reduce((s, d) => s + d.total_revenue_pence, 0)
  const avgDaily = dailyData.length > 0 ? Math.round(totalOrders / dailyData.length) : 0
  const schoolHolDays = dailyData.filter(d => d.is_school_holiday)
  const normalDays = dailyData.filter(d => !d.is_school_holiday && !d.is_bank_holiday)
  const avgSchoolHol = schoolHolDays.length > 0 ? Math.round(schoolHolDays.reduce((s, d) => s + d.total_orders, 0) / schoolHolDays.length) : 0
  const avgNormal = normalDays.length > 0 ? Math.round(normalDays.reduce((s, d) => s + d.total_orders, 0) / normalDays.length) : 0

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[7, 30, 90, 365].map(d => (
          <button key={d} onClick={() => setDays(d)} style={{
            padding: '6px 14px', borderRadius: 8, border: 'none',
            background: days === d ? accent : '#f3f4f6',
            color: days === d ? '#fff' : '#333', cursor: 'pointer', fontWeight: 600,
          }}>{d}d</button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 20 }}>
        <StatBox label="Total Orders" value={totalOrders} />
        <StatBox label="Total Revenue" value={`£${(totalRevenue / 100).toFixed(0)}`} />
        <StatBox label="Avg Daily Orders" value={avgDaily} />
        <StatBox label="Avg (School Hols)" value={avgSchoolHol} color="#f59e0b" />
        <StatBox label="Avg (Normal)" value={avgNormal} />
        <StatBox label="Holiday Uplift" value={avgNormal > 0 ? `${Math.round(((avgSchoolHol - avgNormal) / avgNormal) * 100)}%` : 'N/A'} color="#16a34a" />
      </div>

      {holidays && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>🗓 UK Holidays ({holidays.year})</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.85rem' }}>
            <div>
              <h4 style={{ color: '#888', marginBottom: 4 }}>Bank Holidays</h4>
              {holidays.bank_holidays?.map((h: any, i: number) => (
                <div key={i} style={{ padding: '3px 0' }}>{h.date} — {h.name}</div>
              ))}
            </div>
            <div>
              <h4 style={{ color: '#888', marginBottom: 4 }}>School Holidays</h4>
              {holidays.school_holidays?.map((h: any, i: number) => (
                <div key={i} style={{ padding: '3px 0' }}>{h.start} → {h.end} — {h.name}</div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Procurement Prediction ──
function ProcurementTab({ accent }: { accent: string }) {
  const [procurement, setProcurement] = useState<any>(null)
  const [weekPred, setWeekPred] = useState<any[]>([])
  const [predDays, setPredDays] = useState(7)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getOrderProcurement({ days: predDays }),
      getOrderWeekPrediction(),
    ]).then(([procRes, weekRes]) => {
      setProcurement(procRes.data)
      setWeekPred(weekRes.data || [])
      setLoading(false)
    })
  }, [predDays])

  if (loading) return <p>Loading predictions...</p>

  return (
    <div>
      <h3 style={{ fontSize: '1.1rem', marginBottom: 4 }}>🛒 Procurement Forecast</h3>
      <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: 16 }}>
        Smart predictions based on historical sales, adjusted for school holidays, bank holidays, weekends, and seasonal patterns.
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[3, 7, 14].map(d => (
          <button key={d} onClick={() => setPredDays(d)} style={{
            padding: '6px 14px', borderRadius: 8, border: 'none',
            background: predDays === d ? accent : '#f3f4f6',
            color: predDays === d ? '#fff' : '#333', cursor: 'pointer', fontWeight: 600,
          }}>Next {d} days</button>
        ))}
      </div>

      {/* Daily overview */}
      {weekPred.length > 0 && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
          <h4 style={{ marginBottom: 8 }}>Daily Demand Forecast</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 8 }}>
            {weekPred.map((day: any, i: number) => (
              <div key={i} style={{
                padding: 10, borderRadius: 8, textAlign: 'center',
                background: day.target_context?.is_school_holiday ? '#fef3c7' : day.target_context?.is_bank_holiday ? '#ede9fe' : '#f9fafb',
                border: day.target_context?.is_school_holiday ? '1px solid #f59e0b' : '1px solid #e5e7eb',
              }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{day.target_context?.day_name}</div>
                <div style={{ fontSize: '0.75rem', color: '#888' }}>{day.target_date}</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, margin: '4px 0' }}>{Math.round(day.predicted_total_orders)}</div>
                <div style={{ fontSize: '0.7rem', color: '#888' }}>orders</div>
                {day.target_context?.is_school_holiday && <div style={{ fontSize: '0.65rem', color: '#f59e0b', fontWeight: 600 }}>🏖 School Holiday</div>}
                {day.target_context?.is_bank_holiday && <div style={{ fontSize: '0.65rem', color: '#7c3aed', fontWeight: 600 }}>🏦 Bank Holiday</div>}
                <div style={{ fontSize: '0.65rem', color: '#aaa' }}>Confidence: {day.confidence}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Shopping list */}
      {procurement?.items?.length > 0 && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
          <h4 style={{ marginBottom: 4 }}>🛍 Shopping List ({procurement.period_start} → {procurement.period_end})</h4>
          <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: 12 }}>Predicted quantities needed for the next {procurement.days} days</p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
                <th style={{ padding: '8px 4px' }}>Item</th>
                <th style={{ padding: '8px 4px', textAlign: 'right' }}>Total Qty</th>
                {procurement.items[0]?.daily_breakdown?.map((d: any, i: number) => (
                  <th key={i} style={{ padding: '8px 4px', textAlign: 'right', fontSize: '0.7rem', color: '#888' }}>{d.day?.substring(0, 3)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {procurement.items.map((item: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '6px 4px', fontWeight: 600 }}>{item.name}</td>
                  <td style={{ padding: '6px 4px', textAlign: 'right', fontWeight: 700, color: accent }}>{item.total_predicted}</td>
                  {item.daily_breakdown?.map((d: any, j: number) => (
                    <td key={j} style={{ padding: '6px 4px', textAlign: 'right', color: '#666' }}>{d.quantity}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Settings ──
function SettingsTab({ accent }: { accent: string }) {
  const [settings, setSettings] = useState<any>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => { getOrderQueueSettings().then(r => setSettings(r.data)) }, [])

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    await updateOrderQueueSettings(settings)
    setSaving(false)
  }

  if (!settings) return <p>Loading...</p>

  const fs: React.CSSProperties = { width: '100%', padding: '8px 12px', border: '1px solid #ddd', borderRadius: 8, fontSize: '0.9rem', marginBottom: 8, boxSizing: 'border-box' }

  return (
    <div style={{ maxWidth: 500 }}>
      <h3 style={{ marginBottom: 12 }}>Queue & Ordering Settings</h3>

      <label style={{ fontSize: '0.85rem', color: '#666' }}>Average prep time (minutes)</label>
      <input type="number" value={settings.avg_prep_time_minutes} onChange={e => setSettings({ ...settings, avg_prep_time_minutes: parseInt(e.target.value) || 0 })} style={fs} />

      <label style={{ fontSize: '0.85rem', color: '#666' }}>Max concurrent orders</label>
      <input type="number" value={settings.max_concurrent_orders} onChange={e => setSettings({ ...settings, max_concurrent_orders: parseInt(e.target.value) || 1 })} style={fs} />

      <label style={{ fontSize: '0.85rem', color: '#666' }}>Manual wait time override (minutes)</label>
      <input type="number" value={settings.current_wait_minutes} onChange={e => setSettings({ ...settings, current_wait_minutes: parseInt(e.target.value) || 0 })} style={fs} />

      <div style={{ marginBottom: 12 }}>
        <label><input type="checkbox" checked={settings.auto_calculate_wait} onChange={e => setSettings({ ...settings, auto_calculate_wait: e.target.checked })} /> Auto-calculate wait time from queue</label>
      </div>

      <label style={{ fontSize: '0.85rem', color: '#666' }}>Opening time</label>
      <input type="time" value={settings.opening_time || ''} onChange={e => setSettings({ ...settings, opening_time: e.target.value })} style={fs} />

      <label style={{ fontSize: '0.85rem', color: '#666' }}>Closing time</label>
      <input type="time" value={settings.closing_time || ''} onChange={e => setSettings({ ...settings, closing_time: e.target.value })} style={fs} />

      <h4 style={{ marginTop: 16, marginBottom: 8 }}>Payment Methods</h4>
      <div style={{ marginBottom: 8 }}>
        <label><input type="checkbox" checked={settings.accept_card} onChange={e => setSettings({ ...settings, accept_card: e.target.checked })} /> 💳 Card (Stripe)</label>
      </div>
      <div style={{ marginBottom: 8 }}>
        <label><input type="checkbox" checked={settings.accept_cash} onChange={e => setSettings({ ...settings, accept_cash: e.target.checked })} /> 💵 Cash</label>
      </div>
      <div style={{ marginBottom: 8 }}>
        <label><input type="checkbox" checked={settings.accept_bank_transfer} onChange={e => setSettings({ ...settings, accept_bank_transfer: e.target.checked })} /> 🏦 Bank Transfer</label>
      </div>

      <label style={{ fontSize: '0.85rem', color: '#666' }}>Bank transfer details</label>
      <textarea value={settings.bank_transfer_details || ''} onChange={e => setSettings({ ...settings, bank_transfer_details: e.target.value })} rows={3} style={{ ...fs, resize: 'vertical' }} />

      <h4 style={{ marginTop: 16, marginBottom: 8 }}>Seasonal</h4>
      <div style={{ marginBottom: 8 }}>
        <label><input type="checkbox" checked={settings.seasonal_closed} onChange={e => setSettings({ ...settings, seasonal_closed: e.target.checked })} /> 🏖 Closed for the season</label>
      </div>
      <input value={settings.seasonal_message || ''} onChange={e => setSettings({ ...settings, seasonal_message: e.target.value })} placeholder="Seasonal closed message" style={fs} />

      <button onClick={handleSave} disabled={saving} style={{
        padding: '10px 24px', background: accent, color: '#fff', border: 'none', borderRadius: 8,
        fontWeight: 600, cursor: saving ? 'wait' : 'pointer', marginTop: 8,
      }}>{saving ? 'Saving...' : 'Save Settings'}</button>
    </div>
  )
}

function StatBox({ label, value, color }: { label: string; value: any; color?: string }) {
  return (
    <div style={{ background: '#fff', borderRadius: 10, padding: 14, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
      <div style={{ fontSize: '1.3rem', fontWeight: 800, color: color || '#333' }}>{value}</div>
      <div style={{ fontSize: '0.8rem', color: '#888' }}>{label}</div>
    </div>
  )
}
