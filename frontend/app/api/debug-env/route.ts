import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    DJANGO_BACKEND_URL: process.env.DJANGO_BACKEND_URL || '(not set)',
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || '(not set)',
    NEXT_PUBLIC_TENANT_SLUG: process.env.NEXT_PUBLIC_TENANT_SLUG || '(not set)',
    resolved_api_base: process.env.DJANGO_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://nbneplatform-production.up.railway.app',
    timestamp: new Date().toISOString(),
  })
}
