'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import { useTenant, hasModule } from '@/lib/tenant'
import './staff.css'

const NAV_ITEMS = [
  { href: '/portal', label: 'Dashboard', icon: '📊', module: 'staff' },
  { href: '/portal/shifts', label: 'My Shifts', icon: '📅', module: 'staff' },
  { href: '/portal/leave', label: 'Leave', icon: '🏖️', module: 'staff' },
  { href: '/portal/training', label: 'Training', icon: '🎓', module: 'staff' },
  { href: '/portal/chat', label: 'Team Chat', icon: '💬', module: 'comms' },
  { href: '/portal/hse', label: 'Health & Safety', icon: '🛡️', module: 'compliance' },
  { href: '/portal/documents', label: 'Documents', icon: '📁', module: 'documents' },
]

export default function StaffLayoutClient({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const tenant = useTenant()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const visibleNav = NAV_ITEMS.filter(item => hasModule(tenant, item.module))

  async function handleLogout() {
    localStorage.removeItem('nbne_access')
    localStorage.removeItem('nbne_refresh')
    await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'logout' }),
    })
    router.push('/login')
  }

  return (
    <div className="shell">
      <header className="topbar">
        <button className="btn btn-ghost" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
        <span className="topbar-title">{tenant.business_name}</span>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span className="badge badge-success">Tier 2</span>
          <button className="btn btn-ghost" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Staff Portal</h2>
        </div>
        <nav className="sidebar-nav">
          {visibleNav.map(item => (
            <a
              key={item.href}
              href={item.href}
              className={`nav-item ${pathname === item.href ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <a href="/admin" className="nav-item" style={{ opacity: 0.6, fontSize: '0.8rem' }}>
            <span className="nav-icon">⚙️</span>
            <span>Admin Panel</span>
          </a>
        </div>
      </aside>

      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <main className="main-content">{children}</main>
    </div>
  )
}
