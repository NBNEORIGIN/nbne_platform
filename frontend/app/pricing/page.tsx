'use client'

import { useTenant } from '@/lib/tenant'

export default function PricingPage() {
  const tenant = useTenant()
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
          <a href="/" style={{ color: '#4b5563', textDecoration: 'none' }}>Home</a>
          <a href="/book" style={{
            background: '#111827', color: '#fff', padding: '0.5rem 1.25rem',
            borderRadius: 6, textDecoration: 'none', fontWeight: 600, fontSize: '0.85rem',
          }}>Book Now</a>
          <a href="/login" style={{ color: '#6b7280', textDecoration: 'none', fontSize: '0.85rem' }}>Login</a>
        </div>
      </nav>

      {/* ── Header ── */}
      <section style={{ padding: '4rem 2rem 2rem', textAlign: 'center', background: 'linear-gradient(180deg, #f8fafc 0%, #fff 100%)' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#111827', marginBottom: '0.5rem' }}>
          Simple pricing. No surprises.
        </h1>
        <p style={{ fontSize: '1.1rem', color: '#6b7280', maxWidth: 480, margin: '0 auto' }}>
          One plan. Everything included. Cancel anytime.
        </p>
      </section>

      {/* ── Pricing card ── */}
      <section style={{ padding: '2rem', maxWidth: 640, margin: '0 auto' }}>
        <div style={{
          borderRadius: 16, border: '2px solid #111827', padding: '3rem 2.5rem',
          background: '#fff', position: 'relative',
        }}>
          <div style={{
            position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)',
            background: '#111827', color: '#fff', padding: '0.3rem 1.25rem',
            borderRadius: 20, fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em',
          }}>EVERYTHING INCLUDED</div>

          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ fontSize: '3.5rem', fontWeight: 800, color: '#111827', lineHeight: 1 }}>
              £30
            </div>
            <div style={{ fontSize: '1rem', color: '#6b7280', marginTop: '0.25rem' }}>per month + VAT</div>
          </div>

          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {[
              { item: 'Your own booking website', detail: 'We build it, host it, maintain it. Your brand, your domain.' },
              { item: 'Online booking system', detail: 'Clients book 24/7. You control services, staff, availability, and deposit rules.' },
              { item: 'Stripe payments', detail: 'Take deposits or full payment online. No fees from us — just standard Stripe rates (1.4% + 20p).' },
              { item: 'Staff management', detail: 'Rota, shifts, leave requests, working hours, timesheets, payroll export.' },
              { item: 'CRM & lead tracking', detail: 'Track enquiries from website, social, referrals. Follow up, convert, see revenue per source.' },
              { item: 'Health & safety compliance', detail: 'Compliance register, incident log, training tracker, document storage. Stay legal.' },
              { item: 'Team chat', detail: 'Simple internal messaging. Keep work chat off WhatsApp.' },
              { item: 'Document storage', detail: 'Policies, contracts, certificates, insurance docs. All in one place.' },
              { item: 'Dashboard & command bar', detail: 'Open up, see what\'s happening, type a command, get it sorted.' },
              { item: 'Unlimited staff logins', detail: 'No per-seat charges. Add as many staff as you need.' },
              { item: 'No per-client fees', detail: 'Your client list can grow without your bill growing.' },
              { item: 'Booking reminders', detail: 'Automatic email reminders 24h and 1h before appointments.' },
            ].map(f => (
              <div key={f.item} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                <span style={{ color: '#22c55e', fontWeight: 700, fontSize: '1.1rem', flexShrink: 0, marginTop: '0.1rem' }}>✓</span>
                <div>
                  <div style={{ fontWeight: 600, color: '#111827', fontSize: '0.95rem' }}>{f.item}</div>
                  <div style={{ fontSize: '0.82rem', color: '#6b7280', lineHeight: 1.4 }}>{f.detail}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <a href="/login?redirect=/admin" style={{
              display: 'inline-block', background: '#111827', color: '#fff',
              padding: '0.75rem 2.5rem', borderRadius: 8, textDecoration: 'none',
              fontWeight: 700, fontSize: '1rem',
            }}>Try the Demo</a>
            <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.5rem' }}>
              No credit card required. Demo resets nightly.
            </p>
          </div>
        </div>
      </section>

      {/* ── What you won't find ── */}
      <section style={{ padding: '3rem 2rem', maxWidth: 640, margin: '0 auto' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827', marginBottom: '1.25rem', textAlign: 'center' }}>
          What you won&rsquo;t find here
        </h2>
        <div style={{ display: 'grid', gap: '0.6rem' }}>
          {[
            'No per-client fees that punish you for growing',
            'No per-seat charges that make you think twice about adding staff',
            'No "free tier" that suddenly costs money when you rely on it',
            'No 12-month contracts or lock-in periods',
            'No surprise price increases',
            'No commission on your bookings',
            'No upsell to "premium" features you actually need',
          ].map(item => (
            <div key={item} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.9rem', color: '#374151' }}>
              <span style={{ color: '#ef4444', fontWeight: 700, flexShrink: 0 }}>✕</span>
              <span>{item}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── FAQ ── */}
      <section style={{ padding: '3rem 2rem', maxWidth: 640, margin: '0 auto' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827', marginBottom: '1.5rem', textAlign: 'center' }}>
          Common questions
        </h2>
        <div style={{ display: 'grid', gap: '1.25rem' }}>
          {[
            { q: 'Is there a contract?', a: 'No. Pay monthly, cancel anytime. No notice period.' },
            { q: 'What about Stripe fees?', a: 'Stripe charges their standard rate (1.4% + 20p for UK cards). We don\'t add anything on top.' },
            { q: 'Do I need to be technical?', a: 'No. We set everything up for you. You just run your business.' },
            { q: 'Can I use my own domain?', a: 'Yes. We\'ll set up your website on your domain at no extra cost.' },
            { q: 'What if I have more than one location?', a: 'Each location is £30/month. Same deal, same features.' },
            { q: 'Where is my data stored?', a: 'UK-hosted servers. Your data stays in Britain.' },
            { q: 'What support do I get?', a: 'Real support from real people. Email or chat. We actually reply.' },
          ].map(faq => (
            <div key={faq.q}>
              <div style={{ fontWeight: 600, color: '#111827', fontSize: '0.95rem', marginBottom: '0.25rem' }}>{faq.q}</div>
              <div style={{ fontSize: '0.88rem', color: '#6b7280', lineHeight: 1.5 }}>{faq.a}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding: '3rem 2rem', background: '#111827', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff', marginBottom: '0.75rem' }}>
          Ready to get sorted?
        </h2>
        <p style={{ color: '#9ca3af', marginBottom: '1.5rem' }}>Try the demo. No sign-up. No credit card.</p>
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/login?redirect=/admin" style={{
            background: '#fff', color: '#111827', padding: '0.65rem 2rem',
            borderRadius: 8, textDecoration: 'none', fontWeight: 700,
          }}>Try the Demo</a>
          <a href="/book" style={{
            background: 'transparent', color: '#fff', padding: '0.65rem 2rem',
            borderRadius: 8, textDecoration: 'none', fontWeight: 600,
            border: '2px solid #4b5563',
          }}>Book an Appointment</a>
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
