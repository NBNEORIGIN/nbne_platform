# Tenant Isolation Fix — Feb 2026

## Problem

The NBNE app at `app.nbnesigns.co.uk/admin` was showing Mind Department staff data (Aly Harwood) instead of NBNE's own staff. The issue was Chrome-specific — Edge and incognito worked correctly.

## Root Cause Chain

Three independent issues combined to cause the problem:

### 1. Vercel Injects `x-tenant-slug: preview-demo` Header

Vercel's infrastructure injects an `x-tenant-slug: preview-demo` header into ALL incoming requests to the NBNE Vercel project. This header does not appear in curl from external machines but IS received by Vercel serverless functions when requests come through Chrome.

**Fix:** The proxy route handler (`/api/django/[...path]/route.ts`) now **ignores** the `x-tenant-slug` header from incoming requests and always uses `process.env.NEXT_PUBLIC_TENANT_SLUG` as the tenant slug.

### 2. Chrome CORS Strips Custom Headers with Wildcard + Credentials

The Railway backend returns `Access-Control-Allow-Headers: *` with `Access-Control-Allow-Credentials: true`. Per the CORS spec, **browsers ignore the `*` wildcard when credentials are enabled**. This means Chrome silently strips the `X-Tenant-Slug` header from cross-origin requests to Railway.

When `apiFetch` was changed to call Railway directly (bypassing the Vercel proxy), Chrome dropped the tenant header. Without it, the backend's `TenantMiddleware` fell back to `request.user.tenant`, which was NULL for the superuser, then to the first tenant in the DB (Mind Department).

**Fix:** All API calls go through the Vercel proxy (`/api/django/*`), which sends `X-Tenant-Slug` server-side — not subject to CORS. Direct Railway calls from the browser are avoided.

### 3. Chrome HTTP Cache Served Stale API Responses

Chrome cached API responses from before `Cache-Control: no-store` headers were added. The old JS bundle's `fetch()` calls (without `cache: 'no-store'`) served stale cached data.

**Fix:** An inline `<script>` in `layout.tsx` monkey-patches `window.fetch` before React hydrates, adding `?_cb=<timestamp>` and `cache: 'no-store'` to ALL `/api/` requests. This ensures Chrome never serves stale API data regardless of which JS bundle version is loaded.

## Architecture: Tenant Resolution

### Frontend → Proxy → Backend Flow

```
Browser (apiFetch)
  → /api/django/staff-module/     (same-origin, no CORS)
  → Vercel Proxy (route.ts)
    - Reads process.env.NEXT_PUBLIC_TENANT_SLUG ("nbne")
    - IGNORES x-tenant-slug header from request
    - Sends X-Tenant-Slug: nbne + ?tenant=nbne to Railway
  → Railway Backend
    - TenantMiddleware reads X-Tenant-Slug header → resolves tenant
    - View filters data by request.tenant
  → Response back through proxy to browser
```

### Backend TenantMiddleware Priority

1. `X-Tenant-Slug` header (from proxy)
2. `?tenant=` query parameter
3. `request.user.tenant` (authenticated user's tenant FK)
4. First tenant in database (fallback)

## Key Files Modified

| File | Change |
|------|--------|
| `frontend/app/api/django/[...path]/route.ts` | Ignore injected `x-tenant-slug` header, always use env var. Added `dynamic = 'force-dynamic'` and `fetchCache = 'force-no-store'`. |
| `frontend/lib/api.ts` | `API_BASE = '/api/django'` (proxy, not direct Railway). Demo tenant override scoped to `/book` pages only. |
| `frontend/lib/tenant.tsx` | Branding fetch uses proxy, not direct Railway. |
| `frontend/app/layout.tsx` | Inline script monkey-patches `fetch()` for cache-busting. |
| `frontend/middleware.ts` | Cross-tenant JWT cookie rejection. No-cache headers on all responses. |

## Lessons Learned

1. **Never trust incoming request headers for tenant resolution in the proxy** — Vercel can inject unexpected headers.
2. **`Access-Control-Allow-Headers: *` does NOT work with `Access-Control-Allow-Credentials: true`** — browsers silently strip custom headers. Always list headers explicitly.
3. **Chrome's HTTP cache for `fetch()` calls persists across hard reloads** — only `cache: 'no-store'` in the fetch options or unique URLs bypass it.
4. **Inline `<script>` tags in Next.js layout run before React hydrates** — useful for monkey-patching globals before any React code executes.
5. **Build-time env vars (`NEXT_PUBLIC_*`) are the most reliable tenant identifier** — they're baked into the JS bundle and can't be overridden by infrastructure.

## Vercel Environment Variables (per project)

| Variable | Value | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_TENANT_SLUG` | `nbne` | Tenant identifier, baked into JS at build time |
| `NEXT_PUBLIC_API_BASE_URL` | `https://nbneplatform-production.up.railway.app` | Railway backend URL |
| `DJANGO_BACKEND_URL` | `https://nbneplatform-production.up.railway.app` | Server-side backend URL |
