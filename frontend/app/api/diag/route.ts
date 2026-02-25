import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const API_BASE = process.env.DJANGO_BACKEND_URL || 'https://nbneplatform-production.up.railway.app'
  // ALWAYS use env var — Vercel injects stale x-tenant-slug header we must ignore
  const tenantSlug = process.env.NEXT_PUBLIC_TENANT_SLUG || 'nbne'
  const injectedHeader = req.headers.get('x-tenant-slug')
  const auth = req.headers.get('authorization')
  const cookie = req.headers.get('cookie')
  
  // Make the exact same call as the proxy would
  const target = `${API_BASE}/api/staff/?tenant=${tenantSlug}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (auth) headers['Authorization'] = auth
  if (tenantSlug) headers['X-Tenant-Slug'] = tenantSlug

  const res = await fetch(target, { method: 'GET', headers, cache: 'no-store' })
  const data = await res.json()
  
  return NextResponse.json({
    diag: {
      tenant_slug_used: tenantSlug,
      env_tenant: process.env.NEXT_PUBLIC_TENANT_SLUG,
      vercel_injected_header: injectedHeader,
      header_ignored: injectedHeader !== tenantSlug,
      auth_header_present: !!auth,
      cookie_present: !!cookie,
    },
    backend_target: target,
    backend_status: res.status,
    staff_count: Array.isArray(data) ? data.length : 'not array',
    first_staff: Array.isArray(data) ? (data[0]?.display_name || data[0]?.name || 'none') : 'N/A',
  }, {
    headers: { 'Cache-Control': 'no-store' },
  })
}
