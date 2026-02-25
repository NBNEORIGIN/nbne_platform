import { NextRequest, NextResponse } from 'next/server'

// Fresh proxy route — no cached data in Vercel's Data Cache
export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

async function proxyRequest(req: NextRequest) {
  const API_BASE = process.env.DJANGO_BACKEND_URL || 'https://nbneplatform-production.up.railway.app'
  const url = new URL(req.url)
  const path = url.pathname.replace(/^\/api\/v2/, '')
  // ALWAYS use env var — Vercel injects stale x-tenant-slug header
  const tenantSlug = process.env.NEXT_PUBLIC_TENANT_SLUG || url.searchParams.get('tenant') || 'nbne'

  let target = `${API_BASE}/api${path}${url.search}`
  if (tenantSlug) {
    const sep = target.includes('?') ? '&' : '?'
    target = `${target}${sep}tenant=${tenantSlug}`
  }

  try {
    const headers: Record<string, string> = {}
    const contentType = req.headers.get('content-type')
    if (contentType) headers['Content-Type'] = contentType
    const auth = req.headers.get('authorization')
    if (auth) headers['Authorization'] = auth
    if (tenantSlug) headers['X-Tenant-Slug'] = tenantSlug

    const init: RequestInit = {
      method: req.method,
      headers,
      cache: 'no-store',
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      try {
        const buf = await req.arrayBuffer()
        if (buf.byteLength > 0) init.body = Buffer.from(buf)
      } catch { /* no body */ }
    }

    const res = await fetch(target, init)
    const body = await res.arrayBuffer()

    return new NextResponse(Buffer.from(body), {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    })
  } catch (err: any) {
    return NextResponse.json({ error: 'Proxy error', detail: err.message }, { status: 502 })
  }
}

export const GET = proxyRequest
export const POST = proxyRequest
export const PUT = proxyRequest
export const PATCH = proxyRequest
export const DELETE = proxyRequest
export const OPTIONS = proxyRequest
