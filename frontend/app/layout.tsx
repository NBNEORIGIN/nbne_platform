import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'

export const viewport: Viewport = {
  themeColor: '#0f172a',
}

export const metadata: Metadata = {
  title: 'NBNE Platform',
  description: 'Three-tier business management platform',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'NBNE',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body>
        <script dangerouslySetInnerHTML={{ __html: `
          // Nuke all service workers and caches on every load
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(function(regs) {
              regs.forEach(function(r) { r.unregister(); });
            });
          }
          if ('caches' in window) {
            caches.keys().then(function(names) {
              names.forEach(function(n) { caches.delete(n); });
            });
          }
          // Force bundle refresh — bump this version to force Chrome to reload JS
          var BUNDLE_V = "b4";
          try {
            if (sessionStorage.getItem('_bv') !== BUNDLE_V) {
              sessionStorage.setItem('_bv', BUNDLE_V);
              localStorage.removeItem('nbne_access');
              localStorage.removeItem('nbne_refresh');
              document.cookie = 'nbne_session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT';
              // Navigate with cache-bust param to force new JS bundle download
              var u = new URL(window.location.href);
              u.searchParams.set('_bv', BUNDLE_V);
              window.location.replace(u.toString());
            }
          } catch(e) {}
        `}} />
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
