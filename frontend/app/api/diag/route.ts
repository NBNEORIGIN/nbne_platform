import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const API_BASE = process.env.DJANGO_BACKEND_URL || 'https://nbneplatform-production.up.railway.app'
  const tenantSlug = req.headers.get('x-tenant-slug') || process.env.NEXT_PUBLIC_TENANT_SLUG || ''
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
      tenant_slug_resolved: tenantSlug,
      env_tenant: process.env.NEXT_PUBLIC_TENANT_SLUG,
      auth_header_present: !!auth,
      auth_header_preview: auth ? auth.substring(0, 30) + '...' : null,
      cookie_present: !!cookie,
      cookie_preview: cookie ? cookie.substring(0, 50) + '...' : null,
      x_tenant_slug_header: req.headers.get('x-tenant-slug'),
    },
    backend_target: target,
    backend_status: res.status,
    staff_count: Array.isArray(data) ? data.length : 'not array',
    first_staff: Array.isArray(data) ? (data[0]?.display_name || data[0]?.name || 'none') : 'N/A',
  }, {
    headers: { 'Cache-Control': 'no-store' },
  })
}
