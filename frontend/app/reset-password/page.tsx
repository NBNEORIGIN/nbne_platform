'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTenant } from '@/lib/tenant'
import { validateResetToken, setPasswordWithToken } from '@/lib/api'

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading…</div>}>
      <ResetPasswordForm />
    </Suspense>
  )
}

function ResetPasswordForm() {
  const tenant = useTenant()
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token') || ''

  const [validating, setValidating] = useState(true)
  const [valid, setValid] = useState(false)
  const [userName, setUserName] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!token) {
      setValidating(false)
      return
    }
    validateResetToken(token).then(res => {
      if (res.data?.valid) {
        setValid(true)
        setUserName(res.data.name || '')
      }
      setValidating(false)
    })
  }, [token])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSaving(true)
    const res = await setPasswordWithToken(token, newPassword)
    setSaving(false)

    if (res.error) {
      setError(res.error)
      return
    }
    setDone(true)
  }

  if (validating) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
        <p style={{ color: 'var(--color-text-muted)' }}>Validating link…</p>
      </div>
    )
  }

  if (!token || !valid) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
        <div style={{ maxWidth: 420, width: '90%', textAlign: 'center' }}>
          <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary-dark)', fontSize: '2rem', marginBottom: '1rem' }}>{tenant.business_name}</h1>
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              This password reset link is invalid or has expired.
            </div>
            <a href="/login" className="btn btn-primary" style={{ display: 'inline-block', width: '100%', textAlign: 'center', textDecoration: 'none' }}>
              Back to Sign In
            </a>
          </div>
        </div>
      </div>
    )
  }

  if (done) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
        <div style={{ maxWidth: 420, width: '90%', textAlign: 'center' }}>
          <h1 style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary-dark)', fontSize: '2rem', marginBottom: '1rem' }}>{tenant.business_name}</h1>
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ background: '#dcfce7', color: '#166534', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Your password has been reset successfully.
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => router.push('/login')}>
              Sign In
            </button>
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
          <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
            {userName ? `Hi ${userName}, choose a new password` : 'Choose a new password'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ padding: '2rem' }}>
          {error && (
            <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="new-password">New Password</label>
            <input id="new-password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Minimum 8 characters" required autoFocus />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="confirm-password">Confirm Password</label>
            <input id="confirm-password" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Re-enter your password" required />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={saving}>
            {saving ? 'Resetting…' : 'Reset Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
