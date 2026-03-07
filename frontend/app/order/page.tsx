'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import {
  getOrderMenu, getOrderQueueStatus, placeOrder, getOrderStatus, setDemoTenant,
} from '@/lib/api'


// ── Cart item type ──
interface CartItem {
  menu_item_id: number
  name: string
  price_pence: number
  quantity: number
  notes: string
}

// ── Compact calendar-style minute display ──
function WaitBadge({ minutes }: { minutes: number }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: minutes > 30 ? '#fef2f2' : minutes > 15 ? '#fffbeb' : '#f0fdf4',
      color: minutes > 30 ? '#dc2626' : minutes > 15 ? '#d97706' : '#16a34a',
      padding: '4px 10px', borderRadius: 20, fontWeight: 700, fontSize: '0.85rem',
    }}>
      ⏱ ~{minutes} min
    </span>
  )
}

// ── Search params wrapper to avoid Suspense issues ──
function OrderSearchParams() {
  const searchParams = useSearchParams()
  const demoSlug = searchParams.get('demo') || ''
  const paymentStatus = searchParams.get('payment') || ''
  const paymentOrderRef = searchParams.get('order_ref') || ''
  return <OrderPageInner demoSlug={demoSlug} paymentStatus={paymentStatus} paymentOrderRef={paymentOrderRef} />
}

function OrderPageInner({ demoSlug, paymentStatus, paymentOrderRef }: { demoSlug: string; paymentStatus: string; paymentOrderRef: string }) {
  const tenant = useTenant()
  const accent = tenant.colour_primary || '#dc2626'
  const bizName = tenant.business_name || 'Order'

  // Menu & queue state
  const [menu, setMenu] = useState<any[]>([])
  const [queueStatus, setQueueStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeCategory, setActiveCategory] = useState<number | null>(null)

  // Cart state
  const [cart, setCart] = useState<CartItem[]>([])
  const [showCart, setShowCart] = useState(false)

  // Checkout state
  const [step, setStep] = useState<'menu' | 'checkout' | 'confirmation' | 'tracking'>('menu')
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [notes, setNotes] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('cash')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [confirmedOrder, setConfirmedOrder] = useState<any>(null)

  // Tracking state
  const [trackingRef, setTrackingRef] = useState('')
  const [trackedOrder, setTrackedOrder] = useState<any>(null)
  const [trackingError, setTrackingError] = useState('')

  // Set demo tenant
  useEffect(() => {
    if (demoSlug) setDemoTenant(demoSlug)
    return () => { setDemoTenant(null) }
  }, [demoSlug])

  // Handle Stripe payment return
  useEffect(() => {
    if (paymentStatus === 'success' && paymentOrderRef) {
      getOrderStatus(paymentOrderRef).then(r => {
        if (r.data) {
          setConfirmedOrder(r.data)
          setStep('confirmation')
        }
      })
    }
  }, [paymentStatus, paymentOrderRef])

  // Load menu + queue status
  useEffect(() => {
    if (demoSlug) setDemoTenant(demoSlug)
    Promise.all([getOrderMenu(), getOrderQueueStatus()])
      .then(([menuRes, queueRes]) => {
        setMenu(menuRes.data || [])
        setQueueStatus(queueRes.data || null)
        if (menuRes.data?.length) setActiveCategory(menuRes.data[0].id)
        setLoading(false)
      })
  }, [demoSlug])

  // Auto-refresh queue status every 30s
  useEffect(() => {
    const interval = setInterval(() => {
      getOrderQueueStatus().then(r => { if (r.data) setQueueStatus(r.data) })
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  // Cart helpers
  const cartTotal = cart.reduce((sum, i) => sum + i.price_pence * i.quantity, 0)
  const cartCount = cart.reduce((sum, i) => sum + i.quantity, 0)

  const addToCart = useCallback((item: any) => {
    setCart(prev => {
      const existing = prev.find(c => c.menu_item_id === item.id)
      if (existing) {
        return prev.map(c =>
          c.menu_item_id === item.id ? { ...c, quantity: c.quantity + 1 } : c
        )
      }
      return [...prev, {
        menu_item_id: item.id,
        name: item.name,
        price_pence: item.price_pence,
        quantity: 1,
        notes: '',
      }]
    })
  }, [])

  const updateCartQty = useCallback((menuItemId: number, delta: number) => {
    setCart(prev => prev
      .map(c => c.menu_item_id === menuItemId ? { ...c, quantity: c.quantity + delta } : c)
      .filter(c => c.quantity > 0)
    )
  }, [])

  const removeFromCart = useCallback((menuItemId: number) => {
    setCart(prev => prev.filter(c => c.menu_item_id !== menuItemId))
  }, [])

  // Submit order
  const handleSubmit = async () => {
    if (!name.trim()) { setError('Please enter your name'); return }
    if (cart.length === 0) { setError('Your cart is empty'); return }
    setSubmitting(true)
    setError('')

    const result = await placeOrder({
      customer_name: name.trim(),
      customer_phone: phone.trim(),
      customer_email: email.trim(),
      notes: notes.trim(),
      payment_method: paymentMethod,
      source: 'online',
      items: cart.map(c => ({
        menu_item_id: c.menu_item_id,
        quantity: c.quantity,
        notes: c.notes,
      })),
    })

    setSubmitting(false)
    if (result.error) {
      setError(result.error)
    } else if (result.data?.checkout_url) {
      // Stripe checkout — redirect to payment page
      window.location.href = result.data.checkout_url
    } else {
      setConfirmedOrder(result.data)
      setStep('confirmation')
      setCart([])
    }
  }

  // Track order
  const handleTrack = async () => {
    if (!trackingRef.trim()) return
    setTrackingError('')
    const result = await getOrderStatus(trackingRef.trim())
    if (result.error) {
      setTrackingError('Order not found. Check your reference and try again.')
    } else {
      setTrackedOrder(result.data)
    }
  }

  // Closed state
  if (!loading && queueStatus && (queueStatus.seasonal_closed || !queueStatus.accepting_orders)) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', padding: 20, textAlign: 'center' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: 8 }}>{bizName}</h1>
        <p style={{ fontSize: '1.2rem', color: '#666', maxWidth: 400 }}>
          {queueStatus.seasonal_message || queueStatus.not_accepting_reason || 'We are not currently accepting orders. Please check back later.'}
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>Loading menu...</p>
      </div>
    )
  }

  // ── ORDER TRACKING ──
  if (step === 'tracking') {
    return (
      <div style={{ minHeight: '100vh', background: '#fafafa', padding: '20px 16px' }}>
        <div style={{ maxWidth: 480, margin: '0 auto' }}>
          <button onClick={() => { setStep('menu'); setTrackedOrder(null) }} style={{ background: 'none', border: 'none', color: accent, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16 }}>← Back to menu</button>
          <h2 style={{ fontSize: '1.5rem', marginBottom: 16 }}>Track Your Order</h2>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <input
              value={trackingRef}
              onChange={e => setTrackingRef(e.target.value.toUpperCase())}
              placeholder="Enter order reference (e.g. A7K3)"
              maxLength={6}
              style={{ flex: 1, padding: '12px 16px', border: '1px solid #ddd', borderRadius: 8, fontSize: '1.1rem', letterSpacing: 2, textTransform: 'uppercase' }}
            />
            <button onClick={handleTrack} style={{ padding: '12px 20px', background: accent, color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>Track</button>
          </div>
          {trackingError && <p style={{ color: '#dc2626', marginBottom: 12 }}>{trackingError}</p>}
          {trackedOrder && (
            <div style={{ background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 style={{ margin: 0 }}>Order #{trackedOrder.order_ref}</h3>
                <StatusBadge status={trackedOrder.status} />
              </div>
              <p style={{ color: '#666', margin: '4px 0' }}>{trackedOrder.customer_name}</p>
              {trackedOrder.estimated_ready_minutes > 0 && trackedOrder.status !== 'collected' && trackedOrder.status !== 'cancelled' && (
                <div style={{ marginTop: 8 }}>
                  <WaitBadge minutes={trackedOrder.estimated_ready_minutes} />
                </div>
              )}
              <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #eee' }} />
              {trackedOrder.items?.map((item: any, i: number) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                  <span>{item.quantity}× {item.name}</span>
                  <span style={{ color: '#666' }}>£{(item.line_total_pence / 100).toFixed(2)}</span>
                </div>
              ))}
              <hr style={{ margin: '12px 0', border: 'none', borderTop: '1px solid #eee' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
                <span>Total</span>
                <span>£{(trackedOrder.total_pence / 100).toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ── ORDER CONFIRMATION ──
  if (step === 'confirmation' && confirmedOrder) {
    return (
      <div style={{ minHeight: '100vh', background: '#fafafa', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
        <div style={{ maxWidth: 480, width: '100%', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: 12 }}>✅</div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: 4 }}>Order Placed!</h2>
          <p style={{ color: '#666', marginBottom: 20 }}>Your order reference is:</p>
          <div style={{
            fontSize: '2.5rem', fontWeight: 800, letterSpacing: 6,
            background: '#fff', padding: '16px 24px', borderRadius: 12,
            display: 'inline-block', border: `2px solid ${accent}`, color: accent,
            marginBottom: 20,
          }}>
            {confirmedOrder.order_ref}
          </div>
          <p style={{ color: '#666', marginBottom: 4 }}>
            Estimated ready in <strong>~{confirmedOrder.estimated_ready_minutes} minutes</strong>
          </p>
          <p style={{ color: '#999', fontSize: '0.85rem', marginBottom: 24 }}>
            Total: <strong>£{(confirmedOrder.total_pence / 100).toFixed(2)}</strong>
            {' • '}{confirmedOrder.payment_method === 'cash' ? 'Pay on collection' : confirmedOrder.payment_method === 'bank_transfer' ? 'Bank transfer' : 'Card payment'}
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => { setStep('menu'); setConfirmedOrder(null) }}
              style={{ padding: '12px 24px', background: '#f3f4f6', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}
            >
              Order Again
            </button>
            <button
              onClick={() => { setTrackingRef(confirmedOrder.order_ref); setStep('tracking'); setTrackedOrder(confirmedOrder) }}
              style={{ padding: '12px 24px', background: accent, color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}
            >
              Track Order
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── CHECKOUT ──
  if (step === 'checkout') {
    return (
      <div style={{ minHeight: '100vh', background: '#fafafa', padding: '20px 16px' }}>
        <div style={{ maxWidth: 480, margin: '0 auto' }}>
          <button onClick={() => setStep('menu')} style={{ background: 'none', border: 'none', color: accent, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16 }}>← Back to menu</button>
          <h2 style={{ fontSize: '1.5rem', marginBottom: 16 }}>Checkout</h2>

          {/* Cart summary */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: 12, color: '#666' }}>Your Order</h3>
            {cart.map(item => (
              <div key={item.menu_item_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <button onClick={() => updateCartQty(item.menu_item_id, -1)} style={{ width: 28, height: 28, border: '1px solid #ddd', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: '1rem' }}>−</button>
                    <span style={{ width: 24, textAlign: 'center', fontWeight: 600 }}>{item.quantity}</span>
                    <button onClick={() => updateCartQty(item.menu_item_id, 1)} style={{ width: 28, height: 28, border: '1px solid #ddd', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: '1rem' }}>+</button>
                  </div>
                  <span>{item.name}</span>
                </div>
                <span style={{ fontWeight: 600 }}>£{((item.price_pence * item.quantity) / 100).toFixed(2)}</span>
              </div>
            ))}
            <hr style={{ margin: '12px 0', border: 'none', borderTop: '1px solid #eee' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '1.1rem' }}>
              <span>Total</span>
              <span>£{(cartTotal / 100).toFixed(2)}</span>
            </div>
          </div>

          {/* Customer details */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: 12, color: '#666' }}>Your Details</h3>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Name *" style={inputStyle} />
            <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="Phone (optional)" style={inputStyle} />
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email (optional)" type="email" style={inputStyle} />
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Special instructions (optional)" rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
          </div>

          {/* Payment method */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: 12, color: '#666' }}>Payment</h3>
            {queueStatus?.accept_cash && (
              <label style={radioStyle}>
                <input type="radio" name="payment" value="cash" checked={paymentMethod === 'cash'} onChange={() => setPaymentMethod('cash')} />
                <span>💵 Pay on collection (cash)</span>
              </label>
            )}
            {queueStatus?.accept_bank_transfer && (
              <label style={radioStyle}>
                <input type="radio" name="payment" value="bank_transfer" checked={paymentMethod === 'bank_transfer'} onChange={() => setPaymentMethod('bank_transfer')} />
                <span>🏦 Bank transfer</span>
              </label>
            )}
            {queueStatus?.accept_card && (
              <label style={radioStyle}>
                <input type="radio" name="payment" value="card" checked={paymentMethod === 'card'} onChange={() => setPaymentMethod('card')} />
                <span>💳 Card payment</span>
              </label>
            )}
            {paymentMethod === 'bank_transfer' && queueStatus?.bank_transfer_details && (
              <div style={{ marginTop: 8, padding: 12, background: '#f9fafb', borderRadius: 8, fontSize: '0.85rem', whiteSpace: 'pre-line' }}>
                {queueStatus.bank_transfer_details}
              </div>
            )}
          </div>

          {/* Wait time */}
          {queueStatus && (
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <WaitBadge minutes={queueStatus.calculated_wait_minutes || 15} />
              <p style={{ color: '#999', fontSize: '0.8rem', marginTop: 4 }}>
                {queueStatus.active_order_count || 0} order{(queueStatus.active_order_count || 0) !== 1 ? 's' : ''} ahead of you
              </p>
            </div>
          )}

          {error && <p style={{ color: '#dc2626', textAlign: 'center', marginBottom: 12 }}>{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={submitting || cart.length === 0}
            style={{
              width: '100%', padding: '16px 24px', background: accent, color: '#fff',
              border: 'none', borderRadius: 12, fontSize: '1.1rem', fontWeight: 700,
              cursor: submitting ? 'wait' : 'pointer', opacity: submitting ? 0.6 : 1,
            }}
          >
            {submitting ? 'Placing Order...' : `Place Order • £${(cartTotal / 100).toFixed(2)}`}
          </button>
        </div>
      </div>
    )
  }

  // ── MENU (main view) ──
  return (
    <div style={{ minHeight: '100vh', background: '#fafafa' }}>
      {/* Header */}
      <div style={{
        background: accent, color: '#fff', padding: '20px 16px 16px',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ fontSize: '1.3rem', margin: 0, fontWeight: 800 }}>{bizName}</h1>
              <p style={{ margin: '2px 0 0', fontSize: '0.8rem', opacity: 0.85 }}>Order online for collection</p>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {queueStatus && <WaitBadge minutes={queueStatus.calculated_wait_minutes || 15} />}
              <button
                onClick={() => setStep('tracking')}
                style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem' }}
              >
                Track
              </button>
            </div>
          </div>

          {/* Category tabs */}
          <div style={{ display: 'flex', gap: 8, marginTop: 12, overflowX: 'auto', paddingBottom: 4 }}>
            {menu.map(cat => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                style={{
                  padding: '6px 14px', borderRadius: 20, border: 'none',
                  background: activeCategory === cat.id ? '#fff' : 'rgba(255,255,255,0.2)',
                  color: activeCategory === cat.id ? accent : '#fff',
                  fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
                  whiteSpace: 'nowrap', transition: 'all 0.15s',
                }}
              >
                {cat.icon} {cat.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Menu items */}
      <div style={{ maxWidth: 600, margin: '0 auto', padding: '16px 16px 100px' }}>
        {menu.filter(cat => activeCategory === null || cat.id === activeCategory).map(cat => (
          <div key={cat.id} style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: 12, color: '#333' }}>
              {cat.icon} {cat.name}
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {cat.items.map((item: any) => {
                const inCart = cart.find(c => c.menu_item_id === item.id)
                return (
                  <div
                    key={item.id}
                    style={{
                      background: '#fff', borderRadius: 12, padding: 14,
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                      opacity: item.sold_out ? 0.5 : 1,
                      border: inCart ? `2px solid ${accent}` : '2px solid transparent',
                      transition: 'border 0.15s',
                    }}
                  >
                    <div style={{ flex: 1, marginRight: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 600 }}>{item.name}</span>
                        {item.vegetarian && <span title="Vegetarian" style={{ fontSize: '0.75rem' }}>🌿</span>}
                        {item.vegan && <span title="Vegan" style={{ fontSize: '0.75rem' }}>🌱</span>}
                        {item.gluten_free && <span title="Gluten Free" style={{ fontSize: '0.75rem' }}>🌾</span>}
                        {item.sold_out && <span style={{ fontSize: '0.7rem', color: '#dc2626', fontWeight: 700 }}>SOLD OUT</span>}
                      </div>
                      {item.description && <p style={{ margin: '2px 0 0', fontSize: '0.8rem', color: '#888' }}>{item.description}</p>}
                      <span style={{ fontWeight: 700, color: accent, fontSize: '0.95rem' }}>£{(item.price_pence / 100).toFixed(2)}</span>
                    </div>
                    {!item.sold_out && (
                      inCart ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <button onClick={() => updateCartQty(item.id, -1)} style={qtyBtnStyle}>−</button>
                          <span style={{ width: 24, textAlign: 'center', fontWeight: 700 }}>{inCart.quantity}</span>
                          <button onClick={() => updateCartQty(item.id, 1)} style={qtyBtnStyle}>+</button>
                        </div>
                      ) : (
                        <button
                          onClick={() => addToCart(item)}
                          style={{
                            padding: '8px 16px', background: accent, color: '#fff',
                            border: 'none', borderRadius: 8, fontWeight: 600,
                            cursor: 'pointer', fontSize: '0.85rem',
                          }}
                        >
                          Add
                        </button>
                      )
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Floating cart bar */}
      {cartCount > 0 && (
        <div style={{
          position: 'fixed', bottom: 0, left: 0, right: 0,
          background: '#fff', borderTop: '1px solid #eee',
          padding: '12px 16px', zIndex: 200,
          boxShadow: '0 -2px 10px rgba(0,0,0,0.08)',
        }}>
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <button
              onClick={() => setStep('checkout')}
              style={{
                width: '100%', padding: '14px 24px', background: accent, color: '#fff',
                border: 'none', borderRadius: 12, fontSize: '1rem', fontWeight: 700,
                cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}
            >
              <span>View Order ({cartCount} item{cartCount !== 1 ? 's' : ''})</span>
              <span>£{(cartTotal / 100).toFixed(2)}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; color: string; label: string }> = {
    received: { bg: '#eff6ff', color: '#2563eb', label: '📋 Received' },
    preparing: { bg: '#fef3c7', color: '#d97706', label: '🔥 Preparing' },
    ready: { bg: '#dcfce7', color: '#16a34a', label: '✅ Ready!' },
    collected: { bg: '#f3f4f6', color: '#6b7280', label: '📦 Collected' },
    cancelled: { bg: '#fef2f2', color: '#dc2626', label: '❌ Cancelled' },
  }
  const c = config[status] || config.received
  return (
    <span style={{ background: c.bg, color: c.color, padding: '4px 10px', borderRadius: 20, fontWeight: 700, fontSize: '0.85rem' }}>
      {c.label}
    </span>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '12px 16px', border: '1px solid #ddd',
  borderRadius: 8, fontSize: '0.95rem', marginBottom: 8,
  boxSizing: 'border-box',
}

const radioStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
  cursor: 'pointer', fontSize: '0.95rem', borderRadius: 8,
  margin: '0 0 4px', transition: 'background 0.15s',
}

const qtyBtnStyle: React.CSSProperties = {
  width: 32, height: 32, border: '1px solid #ddd', borderRadius: 8,
  background: '#fff', cursor: 'pointer', fontSize: '1.1rem',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
}

export default function OrderPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>}>
      <OrderSearchParams />
    </Suspense>
  )
}
