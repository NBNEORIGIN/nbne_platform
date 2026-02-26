import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

/**
 * Proxy /api/media/<path> to the tenant's own Railway backend.
 * This avoids hardcoding a single backend URL in the frontend
 * and lets each Vercel project resolve media from its own backend.
 */
async function proxyMedia(req: NextRequest) {
  const BACKEND = process.env.DJANGO_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://nbneplatform-production.up.railway.app'
  const url = new URL(req.url)
  const path = url.pathname.replace(/^\/api\/media/, '')
  const target = BACKEND + '/media' + path

  try {
    const res = await fetch(target, { cache: 'no-store' })
    if (!res.ok) {
      return new NextResponse(null, { status: res.status })
    }
    const body = await res.arrayBuffer()
    return new NextResponse(Buffer.from(body), {
      status: 200,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/octet-stream',
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    })
  } catch (err: any) {
    console.error('[MEDIA PROXY ERROR]', target, err.message)
    return new NextResponse(null, { status: 502 })
  }
}

export const GET = proxyMedia
