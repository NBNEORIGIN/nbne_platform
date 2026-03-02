// Server component layout — forces dynamic rendering for all staff portal pages
// This prevents Next.js from attempting to prerender staff pages at build time
export const dynamic = 'force-dynamic'

import StaffLayoutClient from './StaffLayoutClient'

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  return <StaffLayoutClient>{children}</StaffLayoutClient>
}
