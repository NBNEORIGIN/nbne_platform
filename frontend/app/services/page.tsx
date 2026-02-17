'use client'

import { useState, useEffect } from 'react'
import { getServices } from '@/lib/api'
import { useTenant } from '@/lib/tenant'

function formatPrice(pence: number) { return '£' + (pence / 100).toFixed(2) }

export default function PublicServicesPage() {
  const tenant = useTenant()
  const [services, setServices] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  useEffect(() => {
    getServices().then(r => { setServices(r.data || []); setLoading(false) })
  }, [])

  const activeServices = services.filter((s: any) => s.is_active !== false)
  const categories = Array.from(new Set(activeServices.map((s: any) => s.category).filter(Boolean))) as string[]
  const filtered = activeCategory
    ? activeServices.filter((s: any) => s.category === activeCategory)
    : activeServices

  const primaryColor = tenant.colour_primary || '#2563eb'
  const darkColor = tenant.colour_secondary || '#1e40af'

  return (
    <div style={{ minHeight: '100vh', background: '#fafafa' }}>
      {/* Header */}
      <header style={{ background: darkColor, color: '#fff', padding: '1.5rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <a href="/" style={{ color: '#fff', textDecoration: 'none' }}>
          <h1 style={{ color: '#fff', fontSize: '1.5rem', margin: 0 }}>{tenant.business_name}</h1>
        </a>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <a href="/" style={{ color: '#fff', opacity: 0.85, fontSize: '0.9rem', textDecoration: 'none' }}>Book Now</a>
          <a href="/login" style={{ color: '#fff', opacity: 0.7, fontSize: '0.85rem', textDecoration: 'none' }}>Staff Login</a>
        </div>
      </header>

      <main style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Our Services</h2>
          <p style={{ color: '#6b7280', fontSize: '0.95rem' }}>
            {tenant.tagline || 'Browse our services and book online.'}
          </p>
        </div>

        {/* Category filter pills */}
        {categories.length > 1 && (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <button
              onClick={() => setActiveCategory(null)}
              style={{
                padding: '0.4rem 1rem', borderRadius: 999, fontSize: '0.85rem', fontWeight: 600,
                border: `1.5px solid ${!activeCategory ? primaryColor : '#d1d5db'}`,
                background: !activeCategory ? primaryColor : '#fff',
                color: !activeCategory ? '#fff' : '#6b7280',
                cursor: 'pointer', transition: 'all 150ms ease',
              }}
            >
              All
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                style={{
                  padding: '0.4rem 1rem', borderRadius: 999, fontSize: '0.85rem', fontWeight: 600,
                  border: `1.5px solid ${activeCategory === cat ? primaryColor : '#d1d5db'}`,
                  background: activeCategory === cat ? primaryColor : '#fff',
                  color: activeCategory === cat ? '#fff' : '#6b7280',
                  cursor: 'pointer', transition: 'all 150ms ease',
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {/* Services grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>Loading services…</div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>No services available</p>
            <p style={{ fontSize: '0.9rem' }}>Check back soon — we&rsquo;re setting things up.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {filtered.map((svc: any) => (
              <div
                key={svc.id}
                style={{
                  background: '#fff', borderRadius: 12, border: '1px solid #e5e7eb',
                  padding: '1.25rem 1.5rem', display: 'flex', justifyContent: 'space-between',
                  alignItems: 'center', transition: 'box-shadow 150ms ease',
                }}
                onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.08)')}
                onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    {svc.colour && <span style={{ width: 10, height: 10, borderRadius: '50%', background: svc.colour, flexShrink: 0 }} />}
                    <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>{svc.name}</h3>
                  </div>
                  {svc.description && (
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.88rem', color: '#6b7280', lineHeight: 1.4 }}>{svc.description}</p>
                  )}
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.82rem', color: '#9ca3af' }}>
                    <span>{svc.duration_minutes} min</span>
                    {svc.category && <span>{svc.category}</span>}
                  </div>
                </div>
                <div style={{ textAlign: 'right', marginLeft: '1.5rem', flexShrink: 0 }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: darkColor, marginBottom: 6 }}>
                    {svc.price_pence > 0 ? formatPrice(svc.price_pence) : 'Free'}
                  </div>
                  {(svc.deposit_percentage > 0 || svc.deposit_pence > 0) && (
                    <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: 8 }}>
                      Deposit: {svc.deposit_percentage > 0 ? `${svc.deposit_percentage}%` : formatPrice(svc.deposit_pence)}
                    </div>
                  )}
                  <a
                    href="/"
                    style={{
                      display: 'inline-block', padding: '0.45rem 1.25rem', borderRadius: 8,
                      background: primaryColor, color: '#fff', fontSize: '0.85rem', fontWeight: 600,
                      textDecoration: 'none', transition: 'opacity 150ms ease',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.opacity = '0.9')}
                    onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                  >
                    Book Now
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Contact info */}
        {(tenant.phone || tenant.email) && (
          <div style={{ textAlign: 'center', marginTop: '2.5rem', padding: '1.5rem', background: '#fff', borderRadius: 12, border: '1px solid #e5e7eb' }}>
            <p style={{ fontSize: '0.9rem', color: '#6b7280', marginBottom: '0.5rem' }}>Questions? Get in touch.</p>
            <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', fontSize: '0.9rem' }}>
              {tenant.phone && <a href={`tel:${tenant.phone}`} style={{ color: primaryColor, textDecoration: 'none', fontWeight: 600 }}>{tenant.phone}</a>}
              {tenant.email && <a href={`mailto:${tenant.email}`} style={{ color: primaryColor, textDecoration: 'none', fontWeight: 600 }}>{tenant.email}</a>}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#9ca3af', fontSize: '0.8rem' }}>
        © {new Date().getFullYear()} {tenant.business_name}
      </footer>
    </div>
  )
}
