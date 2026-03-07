'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTenant } from '@/lib/tenant'
import {
  getKitchenQueue, updateOrderStatus, updateOrderNotes,
  getOrderQueueSettings, updateOrderQueueSettings, getOrdersToday,
} from '@/lib/api'

const STATUS_CONFIG: Record<string, { bg: string; color: string; label: string; next?: string; nextLabel?: string }> = {
  received: { bg: '#eff6ff', color: '#2563eb', label: '📋 New', next: 'preparing', nextLabel: '🔥 Start Preparing' },
  preparing: { bg: '#fef3c7', color: '#d97706', label: '🔥 Preparing', next: 'ready', nextLabel: '✅ Mark Ready' },
  ready: { bg: '#dcfce7', color: '#16a34a', label: '✅ Ready', next: 'collected', nextLabel: '📦 Collected' },
  collected: { bg: '#f3f4f6', color: '#6b7280', label: '📦 Done' },
  cancelled: { bg: '#fef2f2', color: '#dc2626', label: '❌ Cancelled' },
}

export default function KitchenPage() {
  const tenant = useTenant()
  const accent = tenant.colour_primary || '#dc2626'

  const [orders, setOrders] = useState<any[]>([])
  const [todayStats, setTodayStats] = useState<any>(null)
  const [queueSettings, setQueueSettings] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<'active' | 'ready' | 'completed'>('active')
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [updatingId, setUpdatingId] = useState<number | null>(null)

  // Audio notification for new orders
  const playNotification = useCallback(() => {
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = 800
      osc.type = 'sine'
      gain.gain.value = 0.3
      osc.start()
      osc.stop(ctx.currentTime + 0.15)
      setTimeout(() => {
        const osc2 = ctx.createOscillator()
        const gain2 = ctx.createGain()
        osc2.connect(gain2)
        gain2.connect(ctx.destination)
        osc2.frequency.value = 1000
        osc2.type = 'sine'
        gain2.gain.value = 0.3
        osc2.start()
        osc2.stop(ctx.currentTime + 0.15)
      }, 200)
    } catch (e) { /* silence */ }
  }, [])

  const fetchAll = useCallback(async () => {
    const statusFilter = view === 'active' ? 'received,preparing' : view === 'ready' ? 'ready' : 'collected,cancelled'
    const [ordersRes, todayRes, settingsRes] = await Promise.all([
      getKitchenQueue(statusFilter),
      getOrdersToday(),
      getOrderQueueSettings(),
    ])
    const prevCount = orders.filter(o => o.status === 'received').length
    const newOrders = (ordersRes.data || []) as any[]
    const newCount = newOrders.filter((o: any) => o.status === 'received').length
    if (newCount > prevCount && prevCount > 0) playNotification()

    setOrders(newOrders)
    setTodayStats(todayRes.data || null)
    setQueueSettings(settingsRes.data || null)
    setLoading(false)
  }, [view, orders, playNotification])

  useEffect(() => { fetchAll() }, [view])

  // Auto-refresh every 10s
  useEffect(() => {
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [fetchAll])

  const handleStatusChange = async (orderId: number, newStatus: string) => {
    setUpdatingId(orderId)
    await updateOrderStatus(orderId, newStatus)
    await fetchAll()
    setUpdatingId(null)
    if (selectedOrder?.id === orderId) {
      setSelectedOrder(null)
    }
  }

  const handleToggleAccepting = async () => {
    if (!queueSettings) return
    await updateOrderQueueSettings({ accepting_orders: !queueSettings.accepting_orders })
    await fetchAll()
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>Loading kitchen...</p>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#111', color: '#fff' }}>
      {/* Top bar */}
      <div style={{
        background: '#1a1a1a', padding: '12px 16px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        borderBottom: '1px solid #333', position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h1 style={{ fontSize: '1.2rem', margin: 0, fontWeight: 800 }}>🍕 Kitchen</h1>
          {todayStats && (
            <div style={{ display: 'flex', gap: 16, fontSize: '0.85rem', color: '#aaa' }}>
              <span>📊 {todayStats.total_orders} orders</span>
              <span>💰 {todayStats.total_revenue_display}</span>
              <span style={{ color: todayStats.active_orders > 5 ? '#f59e0b' : '#4ade80' }}>
                🔥 {todayStats.active_orders} active
              </span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {queueSettings && (
            <span style={{
              padding: '4px 10px', borderRadius: 20, fontSize: '0.8rem', fontWeight: 700,
              background: queueSettings.accepting_orders ? '#052e16' : '#450a0a',
              color: queueSettings.accepting_orders ? '#4ade80' : '#f87171',
            }}>
              ⏱ ~{queueSettings.calculated_wait_minutes} min wait
            </span>
          )}
          <button
            onClick={handleToggleAccepting}
            style={{
              padding: '6px 14px', borderRadius: 8, border: 'none',
              background: queueSettings?.accepting_orders ? '#dc2626' : '#16a34a',
              color: '#fff', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
            }}
          >
            {queueSettings?.accepting_orders ? '⏸ Pause Orders' : '▶ Resume Orders'}
          </button>
        </div>
      </div>

      {/* View tabs */}
      <div style={{ display: 'flex', gap: 4, padding: '8px 16px', background: '#1a1a1a' }}>
        {(['active', 'ready', 'completed'] as const).map(v => (
          <button
            key={v}
            onClick={() => setView(v)}
            style={{
              padding: '8px 16px', borderRadius: 8, border: 'none',
              background: view === v ? accent : '#333',
              color: '#fff', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {v === 'active' ? `🔥 Active (${todayStats?.active_orders || 0})` :
             v === 'ready' ? `✅ Ready (${todayStats?.ready_orders || 0})` :
             `📦 Completed (${todayStats?.completed_orders || 0})`}
          </button>
        ))}
      </div>

      {/* Order cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: 12, padding: 16,
      }}>
        {orders.length === 0 && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 40, color: '#666' }}>
            <p style={{ fontSize: '1.2rem' }}>{view === 'active' ? '🎉 No active orders' : view === 'ready' ? 'No orders ready' : 'No completed orders yet'}</p>
          </div>
        )}
        {orders.map(order => {
          const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.received
          const isUpdating = updatingId === order.id
          return (
            <div
              key={order.id}
              onClick={() => setSelectedOrder(selectedOrder?.id === order.id ? null : order)}
              style={{
                background: '#1e1e1e', borderRadius: 12, padding: 16,
                border: `2px solid ${selectedOrder?.id === order.id ? accent : '#333'}`,
                cursor: 'pointer', transition: 'border 0.15s',
                opacity: isUpdating ? 0.6 : 1,
              }}
            >
              {/* Order header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontSize: '1.3rem', fontWeight: 800, letterSpacing: 2,
                    color: accent,
                  }}>
                    #{order.order_ref}
                  </span>
                  <span style={{
                    background: cfg.bg, color: cfg.color,
                    padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem', fontWeight: 700,
                  }}>
                    {cfg.label}
                  </span>
                </div>
                <span style={{ color: '#888', fontSize: '0.8rem' }}>
                  {order.minutes_ago}m ago
                </span>
              </div>

              {/* Customer */}
              <div style={{ fontSize: '0.9rem', color: '#ccc', marginBottom: 8 }}>
                {order.customer_name}
                {order.source !== 'online' && (
                  <span style={{ color: '#888', marginLeft: 8, fontSize: '0.75rem' }}>
                    ({order.source_display})
                  </span>
                )}
              </div>

              {/* Items */}
              <div style={{ marginBottom: 10 }}>
                {order.items?.map((item: any, i: number) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '3px 0', fontSize: '0.9rem',
                    borderBottom: i < order.items.length - 1 ? '1px solid #2a2a2a' : 'none',
                  }}>
                    <span style={{ color: '#ddd' }}>
                      <strong>{item.quantity}×</strong> {item.name}
                    </span>
                  </div>
                ))}
              </div>

              {/* Notes */}
              {order.notes && (
                <div style={{
                  background: '#2a2a0a', borderRadius: 6, padding: '6px 10px',
                  fontSize: '0.8rem', color: '#fbbf24', marginBottom: 8,
                }}>
                  💬 {order.notes}
                </div>
              )}

              {/* Footer: total + action */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <div style={{ fontSize: '0.85rem', color: '#888' }}>
                  {order.total_display}
                  {' • '}
                  <span style={{ color: order.payment_confirmed ? '#4ade80' : '#f59e0b' }}>
                    {order.payment_confirmed ? '✓ Paid' : order.payment_method_display}
                  </span>
                </div>
                {cfg.next && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleStatusChange(order.id, cfg.next!) }}
                    disabled={isUpdating}
                    style={{
                      padding: '8px 14px', borderRadius: 8, border: 'none',
                      background: accent, color: '#fff', fontWeight: 700,
                      fontSize: '0.85rem', cursor: isUpdating ? 'wait' : 'pointer',
                    }}
                  >
                    {cfg.nextLabel}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
