'use client'

import dynamic from 'next/dynamic'
import SalonPage from './salon/page'
import TavolaPage from './restaurant/client-page'
import FitHubPage from './gym/client-page'
import PizzaShackPage from './pizza-shack/page'

const NBNELandingPage = dynamic(() => import('./home-page'), { ssr: false })

const TENANT_SLUG = process.env.NEXT_PUBLIC_TENANT_SLUG || ''

export default function HomePage() {
  if (TENANT_SLUG === 'salon-x') return <SalonPage />
  if (TENANT_SLUG === 'restaurant-x') return <TavolaPage />
  if (TENANT_SLUG === 'health-club-x') return <FitHubPage />
  if (TENANT_SLUG === 'pizza-shack-x') return <PizzaShackPage />

  if (TENANT_SLUG === 'nbne') {
    if (typeof window !== 'undefined') window.location.href = '/admin'
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Redirecting...</div>
  }

  return <NBNELandingPage />
}
