'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import { requestPasswordReset } from '@/lib/api'

export default function LoginPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading…</div>}>
      <LoginForm />
    </Suspense>
  )
}

function LoginForm() {
  const tenant = useTenant()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showReset, setShowReset] = useState(false)
  const [resetEmail, setResetEmail] = useState('')
  const [resetSent, setResetSent] = useState(false)
  const [resetLoading, setResetLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get('redirect') || '/app'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password }),
      })
      const data = await res.json()
      if (data.ok) {
        // Store JWT tokens in localStorage for API client
        if (data.access && data.refresh) {
          localStorage.setItem('nbne_access', data.access)
          localStorage.setItem('nbne_refresh', data.refresh)
        }
        // Force password change on first login
        if (data.must_change_password) {
          router.push('/set-password')
          return
        }
        // Route based on role
        const role = data.user?.role
        if (role === 'owner' || role === 'manager') {
          router.push(redirect.startsWith('/admin') ? redirect : '/admin')
        } else if (role === 'staff') {
          router.push(redirect.startsWith('/app') ? redirect : '/app')
        } else {
          router.push('/')
        }
      } else {
        setError(data.error || 'Invalid credentials')
      }
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleResetSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!resetEmail.trim()) return
    setResetLoading(true)
    await requestPasswordReset(resetEmail.trim())
    setResetLoading(false)
    setResetSent(true)
  }

  // Forgot password view
  if (showReset) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
        <div style={{ maxWidth: 420, width: '90%' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary-dark)', fontSize: '2rem' }}>{tenant.business_name}</h1>
            <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>Reset your password</p>
          </div>

          <div className="card" style={{ padding: '2rem' }}>
            {resetSent ? (
              <div>
                <div style={{ background: '#dcfce7', color: '#166534', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
                  If an account exists with that email, a password reset link has been sent. Check your inbox.
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  onClick={() => { setShowReset(false); setResetSent(false); setResetEmail('') }}
                >
                  Back to Sign In
                </button>
              </div>
            ) : (
              <form onSubmit={handleResetSubmit}>
                <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '1.25rem' }}>
                  Enter your email address and we&rsquo;ll send you a link to reset your password.
                </p>
                <div style={{ marginBottom: '1.25rem' }}>
                  <label htmlFor="reset-email">Email</label>
                  <input
                    id="reset-email" type="email" value={resetEmail}
                    onChange={e => setResetEmail(e.target.value)}
                    placeholder="your.email@company.com" required autoFocus
                  />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={resetLoading}>
                  {resetLoading ? 'Sending…' : 'Send Reset Link'}
                </button>
                <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.85rem' }}>
                  <a href="#" onClick={(e) => { e.preventDefault(); setShowReset(false) }} style={{ color: 'var(--color-text-muted)' }}>
                    ← Back to Sign In
                  </a>
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
      <div style={{ maxWidth: 420, width: '90%' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary-dark)', fontSize: '2rem' }}>{tenant.business_name}</h1>
          <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ padding: '2rem' }}>
          {error && (
            <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your.email@company.com" required autoFocus />
          </div>

          <div style={{ marginBottom: '0.5rem' }}>
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter password" required />
          </div>

          <div style={{ textAlign: 'right', marginBottom: '1.25rem' }}>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); setShowReset(true) }}
              style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textDecoration: 'underline', textUnderlineOffset: '2px' }}
            >
              Forgot password?
            </a>
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>

          {tenant.slug && tenant.slug !== 'nbne' && (
            <div style={{ marginTop: '1.5rem' }}>
              <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.8rem', marginBottom: '0.75rem' }}>or</div>
              <button
                type="button"
                onClick={() => { setEmail(`owner@${tenant.slug}.demo`); setPassword('admin123'); setTimeout(() => { const form = document.querySelector('form'); if (form) form.requestSubmit() }, 100) }}
                style={{
                  width: '100%', padding: '0.65rem', borderRadius: 'var(--radius)',
                  border: '2px solid #2563eb', background: '#eff6ff', color: '#1d4ed8',
                  fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer',
                }}
              >
                Demo Login (Owner)
              </button>
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'var(--color-primary-light)', borderRadius: 'var(--radius)', fontSize: '0.78rem' }}>
                <div style={{ display: 'grid', gap: '0.2rem' }}>
                  <div><strong>owner@{tenant.slug}.demo</strong> / admin123 — <span className="badge badge-info">Full access</span></div>
                  <div><strong>manager@{tenant.slug}.demo</strong> / admin123 — <span className="badge badge-success">Manager</span></div>
                  <div><strong>staff1@{tenant.slug}.demo</strong> / admin123 — <span className="badge badge-neutral">Staff portal</span></div>
                </div>
                <div style={{ marginTop: '0.5rem', color: 'var(--color-text-muted)', fontSize: '0.72rem' }}>
                  Demo data resets nightly. Have a play!
                </div>
              </div>
            </div>
          )}

          <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
            <a href="/">← Back to public site</a>
          </p>
        </form>
      </div>
    </div>
  )
}
