'use client'

import { useTenant } from '@/lib/tenant'

export default function PizzaShackLanding() {
  const tenant = useTenant()
  const accent = tenant.colour_primary || '#dc2626'
  const dark = tenant.colour_secondary || '#991b1b'
  const bg = tenant.colour_background || '#fffbeb'
  const bizName = tenant.business_name || 'The Pizza Shack'
  const tagline = tenant.tagline || 'Wood-fired pizza on the Northumberland coast'

  return (
    <div style={{ minHeight: '100vh', background: bg, color: '#1c1917' }}>
      {/* Hero */}
      <div style={{
        background: `linear-gradient(135deg, ${dark} 0%, ${accent} 100%)`,
        color: '#fff', padding: '60px 20px 50px', textAlign: 'center',
      }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0, letterSpacing: -1 }}>
          🍕 {bizName}
        </h1>
        <p style={{ fontSize: '1.1rem', opacity: 0.9, marginTop: 8, maxWidth: 500, margin: '8px auto 0' }}>
          {tagline}
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24, flexWrap: 'wrap' }}>
          <a href="/order" style={{
            background: '#fff', color: accent, padding: '14px 32px',
            textDecoration: 'none', fontWeight: 700, fontSize: '1rem',
            borderRadius: 10, letterSpacing: '0.05em', textTransform: 'uppercase',
          }}>
            Order Now
          </a>
          <a href="/order" style={{
            background: 'rgba(255,255,255,0.15)', color: '#fff', padding: '14px 32px',
            textDecoration: 'none', fontWeight: 600, fontSize: '1rem',
            borderRadius: 10, border: '1px solid rgba(255,255,255,0.3)',
          }}>
            View Menu
          </a>
        </div>
      </div>

      {/* How it works */}
      <div style={{ maxWidth: 700, margin: '0 auto', padding: '40px 20px' }}>
        <h2 style={{ textAlign: 'center', fontSize: '1.5rem', marginBottom: 30 }}>How It Works</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 20 }}>
          {[
            { icon: '📱', title: 'Browse Menu', desc: 'Pick from our hand-crafted pizzas, sides, and desserts' },
            { icon: '🛒', title: 'Place Order', desc: 'Add items to your cart and checkout in seconds' },
            { icon: '⏱', title: 'Live Wait Time', desc: 'See exactly how long your order will take' },
            { icon: '🍕', title: 'Collect & Enjoy', desc: 'Grab your freshly made order when it\'s ready' },
          ].map(step => (
            <div key={step.title} style={{ textAlign: 'center', padding: 16 }}>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>{step.icon}</div>
              <h3 style={{ fontSize: '1rem', marginBottom: 4 }}>{step.title}</h3>
              <p style={{ fontSize: '0.85rem', color: '#666', margin: 0 }}>{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Features for owner */}
      <div style={{ background: '#fff', padding: '40px 20px' }}>
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: '1.5rem', marginBottom: 8 }}>Behind the Counter</h2>
          <p style={{ textAlign: 'center', color: '#888', marginBottom: 30 }}>
            Powerful tools for the business owner — try the admin panel
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {[
              { icon: '🔥', title: 'Kitchen Display', desc: 'Real-time order queue with one-tap status updates' },
              { icon: '📊', title: 'Smart Analytics', desc: 'Sales trends, popular items, and seasonal patterns' },
              { icon: '🛒', title: 'Procurement AI', desc: 'Predicts what to buy based on holidays and demand' },
              { icon: '🍕', title: 'Menu Management', desc: 'Add items, set prices, mark sold out in real-time' },
              { icon: '💳', title: 'Flexible Payments', desc: 'Card, cash, or bank transfer — your choice' },
              { icon: '🏖', title: 'Seasonal Controls', desc: 'Close for winter with one toggle' },
            ].map(feature => (
              <div key={feature.title} style={{
                background: '#f9fafb', borderRadius: 10, padding: 16,
                border: '1px solid #f3f4f6',
              }}>
                <div style={{ fontSize: '1.5rem', marginBottom: 6 }}>{feature.icon}</div>
                <h4 style={{ fontSize: '0.9rem', marginBottom: 4 }}>{feature.title}</h4>
                <p style={{ fontSize: '0.8rem', color: '#888', margin: 0 }}>{feature.desc}</p>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <a href="/login" style={{
              display: 'inline-block', background: accent, color: '#fff',
              padding: '12px 28px', textDecoration: 'none', fontWeight: 600,
              borderRadius: 8,
            }}>
              Try the Admin Panel →
            </a>
            <p style={{ fontSize: '0.8rem', color: '#aaa', marginTop: 8 }}>
              Login: <strong>pizza-shack-x-owner</strong> / <strong>admin123</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Contact / Footer */}
      <div style={{ padding: '30px 20px', textAlign: 'center', fontSize: '0.85rem', color: '#888' }}>
        <p>{bizName} • Seahouses, Northumberland</p>
        <p>{tenant.phone} • {tenant.email}</p>
        <p style={{ marginTop: 8, fontSize: '0.75rem', color: '#bbb' }}>
          Powered by <a href="https://floe.nbne.uk" style={{ color: '#aaa' }}>Floe</a> by NBNE
        </p>
      </div>
    </div>
  )
}
