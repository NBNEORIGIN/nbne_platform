'use client'

import { useTenant } from '@/lib/tenant'

export default function HomePage() {
  const tenant = useTenant()
  const isSalon = tenant.business_name?.toLowerCase().includes('salon')
  const bizName = tenant.business_name || 'Salon-X'

  return (
    <div style={{ minHeight: '100vh', background: '#fff' }}>

      {/* ── Nav ── */}
      <nav style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '1rem 2rem', borderBottom: '1px solid #f1f5f9',
        position: 'sticky', top: 0, background: '#fff', zIndex: 50,
      }}>
        <a href="/" style={{ fontWeight: 800, fontSize: '1.3rem', color: '#111827', textDecoration: 'none', letterSpacing: '-0.02em' }}>
          {bizName}
        </a>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', fontSize: '0.9rem' }}>
          <a href="#features" style={{ color: '#4b5563', textDecoration: 'none' }}>Features</a>
          <a href="/pricing" style={{ color: '#4b5563', textDecoration: 'none' }}>Pricing</a>
          <a href="/book" style={{
            background: '#111827', color: '#fff', padding: '0.5rem 1.25rem',
            borderRadius: 6, textDecoration: 'none', fontWeight: 600, fontSize: '0.85rem',
          }}>Book Now</a>
          <a href="/login" style={{ color: '#6b7280', textDecoration: 'none', fontSize: '0.85rem' }}>Login</a>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{
        padding: '5rem 2rem 4rem', textAlign: 'center',
        background: 'linear-gradient(180deg, #f8fafc 0%, #fff 100%)',
      }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#2563eb', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
            Built in the UK for UK small businesses
          </div>
          <h1 style={{ fontSize: '2.75rem', fontWeight: 800, color: '#111827', lineHeight: 1.15, marginBottom: '1.25rem', letterSpacing: '-0.03em' }}>
            Bookings, staff cover, and compliance — <span style={{ color: '#2563eb' }}>sorted</span>.
          </h1>
          <p style={{ fontSize: '1.15rem', color: '#6b7280', lineHeight: 1.6, marginBottom: '2rem', maxWidth: 520, margin: '0 auto 2rem' }}>
            Everything a UK {isSalon ? 'salon' : 'business'} owner needs to run the day without the stress.
            No per-client fees. No per-seat limits. Just straightforward software that works.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/book" style={{
              background: '#111827', color: '#fff', padding: '0.75rem 2rem',
              borderRadius: 8, textDecoration: 'none', fontWeight: 700, fontSize: '1rem',
            }}>Book an Appointment</a>
            <a href="/login?redirect=/admin" style={{
              background: '#fff', color: '#111827', padding: '0.75rem 2rem',
              borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: '1rem',
              border: '2px solid #e5e7eb',
            }}>Try the Demo</a>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.75rem' }}>
            Demo login: <strong>owner</strong> / <strong>admin123</strong> — data resets nightly
          </p>
        </div>
      </section>

      {/* ── How it works (owner brain) ── */}
      <section style={{ padding: '4rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '2.5rem' }}>
            How your morning goes
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '2rem' }}>
            {[
              { num: '1', title: 'What happened?', desc: 'Sick calls, no-shows, gaps in the diary, deposits not paid. It\'s all there when you open up.' },
              { num: '2', title: 'What do I do?', desc: 'One-click actions. Sensible options. The system tells you what needs doing and lets you do it.' },
              { num: '3', title: 'Sorted.', desc: 'Then crack on with the day. Run your business, not your software.' },
            ].map(item => (
              <div key={item.num} style={{ textAlign: 'center' }}>
                <div style={{
                  width: 48, height: 48, borderRadius: '50%', background: '#f0f9ff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 1rem', fontSize: '1.25rem', fontWeight: 800, color: '#2563eb',
                }}>{item.num}</div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#111827', marginBottom: '0.5rem' }}>{item.title}</h3>
                <p style={{ fontSize: '0.9rem', color: '#6b7280', lineHeight: 1.5 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" style={{ padding: '4rem 2rem', background: '#f8fafc' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '0.5rem' }}>
            Everything you need. Nothing you don&rsquo;t.
          </h2>
          <p style={{ textAlign: 'center', color: '#6b7280', marginBottom: '2.5rem', fontSize: '1rem' }}>
            All included. No add-ons. No upgrades. No surprises.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
            {[
              { icon: '📅', title: 'Online Booking', desc: 'Clients book 24/7. You set the rules — services, staff, availability, deposits.' },
              { icon: '💳', title: 'Stripe Payments', desc: 'Take deposits or full payment. No fees from us, ever. Just standard Stripe rates.' },
              { icon: '👥', title: 'Staff Management', desc: 'Rota, leave, hours, timesheets, training records. All in one place.' },
              { icon: '📋', title: 'CRM & Leads', desc: 'Track enquiries, follow up, convert to clients. See which sources bring real revenue.' },
              { icon: '🛡️', title: 'Health & Safety', desc: 'Compliance register, incident log, training tracker. Stay legal without the stress.' },
              { icon: '📊', title: 'Dashboard', desc: 'Open up, see what\'s happening, deal with it. One command bar to run everything.' },
              { icon: '🌐', title: 'Your Website', desc: 'We build and host your booking website. It\'s included. No extra charge.' },
              { icon: '💬', title: 'Team Chat', desc: 'Simple internal messaging. No WhatsApp groups needed.' },
              { icon: '📁', title: 'Documents', desc: 'Store policies, contracts, certificates. Everything in one secure place.' },
            ].map(f => (
              <div key={f.title} style={{
                background: '#fff', borderRadius: 10, padding: '1.5rem',
                border: '1px solid #e5e7eb',
              }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{f.icon}</div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#111827', marginBottom: '0.35rem' }}>{f.title}</h3>
                <p style={{ fontSize: '0.85rem', color: '#6b7280', lineHeight: 1.5, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing preview ── */}
      <section style={{ padding: '4rem 2rem', background: '#fff' }}>
        <div style={{ maxWidth: 560, margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginBottom: '0.5rem' }}>
            Simple pricing. Proper value.
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '2rem' }}>One plan. Everything included. No hidden costs.</p>
          <div style={{
            background: '#f8fafc', borderRadius: 12, padding: '2.5rem 2rem',
            border: '2px solid #e5e7eb',
          }}>
            <div style={{ fontSize: '3rem', fontWeight: 800, color: '#111827', lineHeight: 1 }}>
              £30<span style={{ fontSize: '1rem', fontWeight: 500, color: '#6b7280' }}>/month + VAT</span>
            </div>
            <div style={{ marginTop: '1.5rem', textAlign: 'left', maxWidth: 320, margin: '1.5rem auto 0' }}>
              {[
                'Your own booking website',
                'Online payments via Stripe',
                'Staff rota, leave & timesheets',
                'CRM & lead tracking',
                'Health & safety compliance',
                'Team chat',
                'Document storage',
                'Unlimited staff logins',
                'No per-client charges, ever',
              ].map(item => (
                <div key={item} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#374151' }}>
                  <span style={{ color: '#22c55e', fontWeight: 700, flexShrink: 0 }}>✓</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <a href="/pricing" style={{
              display: 'inline-block', marginTop: '1.5rem',
              background: '#111827', color: '#fff', padding: '0.65rem 2rem',
              borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem',
            }}>See full details</a>
          </div>
        </div>
      </section>

      {/* ── Trust / fish & chips ── */}
      <section style={{ padding: '4rem 2rem', background: '#f0f9ff' }}>
        <div style={{ maxWidth: 640, margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', marginBottom: '1rem' }}>
            Built in the UK by a small business, for UK small businesses.
          </h2>
          <p style={{ fontSize: '1rem', color: '#4b5563', lineHeight: 1.7, marginBottom: '1rem' }}>
            We&rsquo;re not a Silicon Valley startup trying to lock you in.
            We&rsquo;re a small British company that builds straightforward software for people who run real businesses.
          </p>
          <p style={{ fontSize: '1rem', color: '#4b5563', lineHeight: 1.7, marginBottom: '1.5rem' }}>
            No per-client fees. No per-seat fees. No surprise price hikes.
            No &ldquo;free tier&rdquo; that suddenly isn&rsquo;t free.
            Just honest software at a fair price.
          </p>
          <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap', fontSize: '0.85rem', color: '#6b7280' }}>
            <span>No contracts</span>
            <span>Cancel anytime</span>
            <span>UK data hosting</span>
            <span>Real support</span>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding: '4rem 2rem', background: '#111827', textAlign: 'center' }}>
        <div style={{ maxWidth: 560, margin: '0 auto' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#fff', marginBottom: '0.75rem' }}>
            See it in action
          </h2>
          <p style={{ color: '#9ca3af', marginBottom: '2rem', fontSize: '1rem' }}>
            Log into the demo and have a play. No sign-up required.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/login?redirect=/admin" style={{
              background: '#fff', color: '#111827', padding: '0.75rem 2rem',
              borderRadius: 8, textDecoration: 'none', fontWeight: 700, fontSize: '1rem',
            }}>Try the Demo</a>
            <a href="/book" style={{
              background: 'transparent', color: '#fff', padding: '0.75rem 2rem',
              borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: '1rem',
              border: '2px solid #4b5563',
            }}>Book an Appointment</a>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ padding: '2rem', textAlign: 'center', fontSize: '0.8rem', color: '#9ca3af', borderTop: '1px solid #f1f5f9' }}>
        <p>{bizName} — powered by NBNE Business Platform</p>
        <p style={{ marginTop: '0.25rem' }}>Built in Britain. Straightforward pricing. Proper support.</p>
      </footer>
    </div>
  )
}
