'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'

function SuccessContent() {
  const params = useSearchParams()
  const orderId = params.get('order')

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, sans-serif", minHeight: '100vh',
      background: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '2rem',
    }}>
      <div style={{
        background: '#fff', borderRadius: 16, padding: '3rem 2.5rem', textAlign: 'center',
        maxWidth: 480, width: '100%', boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
        border: '1px solid #e5e7eb',
      }}>
        <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>✅</div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.5rem' }}>
          Order Confirmed!
        </h1>
        {orderId && (
          <p style={{ fontSize: '0.9rem', color: '#64748b', margin: '0 0 0.75rem' }}>
            Order <strong>#{orderId}</strong>
          </p>
        )}
        <p style={{ fontSize: '0.9rem', color: '#6b7280', lineHeight: 1.6, margin: '0 0 1.5rem' }}>
          Thank you for your order. You will receive a confirmation email shortly with your order details and tracking information.
        </p>
        <a href="/shop" style={{
          display: 'inline-block', background: '#2563eb', color: '#fff', padding: '0.65rem 1.5rem',
          borderRadius: 8, fontWeight: 700, textDecoration: 'none', fontSize: '0.9rem',
        }}>Continue Shopping</a>
      </div>
    </div>
  )
}

export default function ShopSuccessPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>Loading...</div>}>
      <SuccessContent />
    </Suspense>
  )
}
