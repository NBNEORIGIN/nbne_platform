// Server component layout — forces dynamic rendering for all admin pages
// This prevents Next.js from attempting to prerender admin pages at build time
export const dynamic = 'force-dynamic'

import AdminLayoutClient from './AdminLayoutClient'

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AdminLayoutClient>{children}</AdminLayoutClient>
}
