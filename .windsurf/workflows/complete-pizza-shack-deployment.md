---
description: Complete Pizza Shack X deployment — fix bugs, build beautiful site, update floe landing, test everything, deploy live
---

# Pizza Shack X — Full Deployment Completion (Wiggum Micro-Loop)

## Context
Pizza Shack X (pizza-shack-x.nbne.uk) is a new "Order & Collect" demo site for the Floe platform. The backend and frontend are deployed on Hetzner (Docker Compose) but have known bugs and need polish. This workflow runs autonomously — no user input required.

**Server:** root@178.104.1.152 (SSH key auth, ed25519)
**Instances dir:** /opt/nbne/instances/pizza-shack-x/
**Shared code:** /opt/nbne/shared (git repo, origin = NBNEORIGIN/nbne_platform)
**Git push:** `git push origin main` ONLY (no vercel remote)
**Floe landing:** Static HTML at /opt/nbne/floe-landing/ on server (index.html, platform.html)
**Demo credentials:** pizza-shack-x-owner / admin123, pizza-shack-x-staff1 / admin123

## Known Bugs to Fix

### Bug 1: Admin Login Broken
The login page at /login posts to /api/auth which is a Next.js API route at `frontend/app/api/auth/route.ts`. Line 4 has a hardcoded Railway fallback:
```
const DJANGO_API = process.env.DJANGO_BACKEND_URL || 'https://nbneplatform-production.up.railway.app'
```
On Hetzner, `DJANGO_BACKEND_URL` is set to `http://backend:8000` in docker-compose.client.yml (runtime env). But the auth route runs server-side in the Next.js container where this env var IS available. The bug is likely that the login POST to `/api/auth/login/` on the Django side returns an error because:
- The request from the Next.js container to `http://backend:8000` needs the `Host` header or `X-Tenant-Slug` header set correctly
- Check `frontend/app/api/auth/route.ts` line 30-37 — it does send `X-Tenant-Slug` from `NEXT_PUBLIC_TENANT_SLUG`
- `NEXT_PUBLIC_TENANT_SLUG` is a build-time var baked into the JS bundle, but this route runs server-side where the RUNTIME env `NEXT_PUBLIC_TENANT_SLUG` from docker-compose is used
- The Dockerfile.frontend line 42 resets `NEXT_PUBLIC_TENANT_SLUG=""` in the runner stage — THIS IS THE BUG for server-side routes

**Fix:** Remove the empty `ENV NEXT_PUBLIC_TENANT_SLUG=""` reset from the runner stage in `docker/Dockerfile.frontend`, since the runtime env from docker-compose.client.yml should provide it.

**Verification:** After fix, SSH to server, rebuild frontend, then test login:
```
ssh root@178.104.1.152 "docker exec pizza-shack-x-frontend-1 env | grep TENANT"
# Should show: NEXT_PUBLIC_TENANT_SLUG=pizza-shack-x
```
Then test the login API:
```
ssh root@178.104.1.152 "python3 -c \"
import urllib.request, json
data = json.dumps({'username':'pizza-shack-x-owner','password':'admin123'}).encode()
req = urllib.request.Request('http://127.0.0.1:3007/api/auth', data=data, headers={'Content-Type':'application/json','Host':'pizza-shack-x.nbne.uk'})
try:
    r = urllib.request.urlopen(req)
    print('STATUS:', r.status)
    print(json.loads(r.read().decode()).get('ok'))
except Exception as e:
    print('ERROR:', e)
\""
```

### Bug 2: Card Payments Not Integrated with Stripe
The order page offers "Card payment" as an option but the `place_order` view just creates the order with `payment_method='card'` and `payment_confirmed=False`. There's no Stripe checkout redirect. The existing Stripe integration in `bookings/views_stripe.py` shows the pattern.

**Fix approach:**
1. In `backend/orders/views.py` `place_order()`, after creating the order, if `payment_method == 'card'`:
   - Check if `STRIPE_SECRET_KEY` is configured
   - If yes: create a Stripe Checkout Session with the order total, redirect URL pointing to `/order?payment=success&order_ref=XXXX`
   - Return `{ checkout_url, order_ref }` instead of the full order — frontend redirects to Stripe
   - If no Stripe key: fall through to normal flow (order confirmed, pay on collection)
2. In `frontend/app/order/page.tsx`, handle the checkout_url response — if present, redirect to Stripe
3. Add a webhook or success handler: when user returns from Stripe with `?payment=success`, mark payment_confirmed=True
4. For the demo site, Stripe won't be configured (no key in .env), so card orders will just go through unpaid — this is fine for demo. Add a note on the confirmation screen.

**Simpler approach for demo:** Since this is a demo site without real Stripe keys, just make the card payment flow work gracefully:
- If Stripe is configured, do the full Stripe checkout flow
- If not (demo mode), accept the order with a note "Card payment will be collected on pickup" 
- The key thing is it shouldn't error — it should work smoothly

### Bug 3: Payment Radio Button Layout
From the screenshot, the payment radio buttons have poor layout — labels are misaligned. Fix the CSS in the order page.

## Phase 1: Fix Bugs (Backend + Frontend)

### Step 1.1: Fix Dockerfile.frontend runner stage
Edit `docker/Dockerfile.frontend` — remove the line `ENV NEXT_PUBLIC_TENANT_SLUG=""` from the runner stage (around line 42). The runtime env from docker-compose provides this value.

### Step 1.2: Fix card payment flow in place_order view
Edit `backend/orders/views.py`:
- After order creation, if payment_method == 'card', check for STRIPE_SECRET_KEY
- If Stripe configured: create checkout session, return checkout_url
- If not: mark order as accepted with payment_confirmed=False, include a message in response

### Step 1.3: Fix frontend order page to handle Stripe redirect
Edit `frontend/app/order/page.tsx`:
- If placeOrder response contains `checkout_url`, redirect browser to it
- Handle `?payment=success&order_ref=XXX` query params on page load to show confirmation
- Fix payment radio button layout CSS

### Step 1.4: Commit and push
// turbo
```
git add -A && git commit -m "fix: admin login (Dockerfile tenant slug), card payment flow, payment UI layout" && git push origin main
```

## Phase 2: Build Beautiful Pizza Shack Landing Page

### Step 2.1: Redesign pizza-shack/page.tsx
Replace the current basic landing page with a beautiful, modern design:
- Hero section with gradient background, animated pizza emoji, compelling CTA
- Social proof section (e.g. "500+ orders this month", "4.8★ rating")
- Menu preview section showing 3-4 featured items with prices
- "How it works" section with icons and steps
- Owner tools section showcasing admin features
- Testimonials (fictional for demo)
- Footer with contact info, opening hours, social links
- Mobile-first responsive design
- Use CSS animations (fade-in on scroll, hover effects)
- Use the tenant's colour scheme throughout
- Add a sticky "Order Now" button on mobile

### Step 2.2: Improve the /order page UI
Polish the customer-facing order page:
- Better typography and spacing
- Card-style menu items with hover effects
- Animated cart badge
- Smooth transitions between menu/cart/checkout/confirmation steps
- Better confirmation screen with order tracking animation
- Responsive grid for menu categories

### Step 2.3: Commit and push
// turbo
```
git add -A && git commit -m "feat: beautiful pizza shack landing page and polished order page UI" && git push origin main
```

## Phase 3: Update Floe Landing Page

### Step 3.1: Read current floe landing page
SSH to server and read `/opt/nbne/floe-landing/index.html` to understand the current structure and where the demo sites are listed.

### Step 3.2: Add Pizza Shack X to the demo sites section
The floe landing page (index.html) lists the demo sites (Salon X, Tavola, FitHub). Add Pizza Shack X as the 4th demo:
- Title: "The Pizza Shack"
- Description: "Order & collect for takeaways — smart menu, live kitchen display, procurement AI"
- Link: https://pizza-shack-x.nbne.uk
- Icon/emoji: 🍕
- Match the existing card style

### Step 3.3: Also update platform.html if it lists demos
Check if platform.html has a demo listing section and update it too.

### Step 3.4: Deploy floe landing page update
Write the updated HTML files directly to the server via SSH heredoc or scp. No Docker rebuild needed — it's static HTML served by Nginx.

## Phase 4: Deploy Everything on Hetzner

### Step 4.1: Pull latest code on server
```
ssh root@178.104.1.152 "cd /opt/nbne/shared && git pull origin main"
```

### Step 4.2: Rebuild pizza-shack-x (both backend and frontend)
Frontend needs rebuild because of Dockerfile change:
```
ssh root@178.104.1.152 "cd /opt/nbne/instances/pizza-shack-x && docker compose --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml -p pizza-shack-x up -d --build --remove-orphans"
```

### Step 4.3: Also rebuild other sites that might be affected by Dockerfile change
The Dockerfile.frontend change (removing empty NEXT_PUBLIC_TENANT_SLUG) should be tested on at least one other site to make sure it doesn't break anything:
```
ssh root@178.104.1.152 "cd /opt/nbne/instances/salon-x && docker compose --env-file .env -f /opt/nbne/shared/docker/docker-compose.client.yml -p salon-x up -d --build frontend"
```
Verify salon-x still works after rebuild.

### Step 4.4: Wait for containers to start
Check backend logs until gunicorn starts:
```
ssh root@178.104.1.152 "docker logs pizza-shack-x-backend-1 --tail 5"
```
Keep checking every 15 seconds until you see "Booting worker with pid".

## Phase 5: Test Everything

### Step 5.1: Test backend API health
```
ssh root@178.104.1.152 "python3 -c \"
import urllib.request, json

# Test 1: Menu endpoint
req = urllib.request.Request('http://127.0.0.1:8007/api/orders/menu/', headers={'Host':'pizza-shack-x.nbne.uk','X-Tenant-Slug':'pizza-shack-x'})
r = urllib.request.urlopen(req)
menu = json.loads(r.read().decode())
print(f'MENU: {len(menu)} categories, OK' if len(menu) > 0 else 'MENU: FAIL')

# Test 2: Queue status
req = urllib.request.Request('http://127.0.0.1:8007/api/orders/queue-status/', headers={'Host':'pizza-shack-x.nbne.uk','X-Tenant-Slug':'pizza-shack-x'})
r = urllib.request.urlopen(req)
qs = json.loads(r.read().decode())
print(f'QUEUE: accepting={qs.get(\"accepting_orders\")}, wait={qs.get(\"calculated_wait_minutes\")}min, OK')

# Test 3: Place order
data = json.dumps({'customer_name':'Automated Test','customer_phone':'','customer_email':'','notes':'','payment_method':'cash','source':'online','items':[{'menu_item_id':1,'quantity':1}]}).encode()
req = urllib.request.Request('http://127.0.0.1:8007/api/orders/place/', data=data, headers={'Host':'pizza-shack-x.nbne.uk','X-Tenant-Slug':'pizza-shack-x','Content-Type':'application/json'})
r = urllib.request.urlopen(req)
order = json.loads(r.read().decode())
print(f'ORDER: ref={order.get(\"order_ref\")}, total=£{order.get(\"total_pence\",0)/100:.2f}, OK')

# Test 4: Order status lookup
ref = order.get('order_ref')
req = urllib.request.Request(f'http://127.0.0.1:8007/api/orders/status/{ref}/', headers={'Host':'pizza-shack-x.nbne.uk','X-Tenant-Slug':'pizza-shack-x'})
r = urllib.request.urlopen(req)
status = json.loads(r.read().decode())
print(f'STATUS: ref={ref}, status={status.get(\"status\")}, OK')

# Test 5: Card payment order (no Stripe key = should still succeed gracefully)
data = json.dumps({'customer_name':'Card Test','customer_phone':'','customer_email':'test@test.com','notes':'','payment_method':'card','source':'online','items':[{'menu_item_id':1,'quantity':2}]}).encode()
req = urllib.request.Request('http://127.0.0.1:8007/api/orders/place/', data=data, headers={'Host':'pizza-shack-x.nbne.uk','X-Tenant-Slug':'pizza-shack-x','Content-Type':'application/json'})
r = urllib.request.urlopen(req)
card_order = json.loads(r.read().decode())
print(f'CARD ORDER: ref={card_order.get(\"order_ref\")}, payment={card_order.get(\"payment_method\")}, OK')

print()
print('=== ALL BACKEND TESTS PASSED ===')
\""
```

### Step 5.2: Test login flow
```
ssh root@178.104.1.152 "python3 -c \"
import urllib.request, json

# Test login via Next.js auth route (this is what the browser does)
data = json.dumps({'username':'pizza-shack-x-owner','password':'admin123'}).encode()
req = urllib.request.Request('http://127.0.0.1:3007/api/auth', data=data, headers={'Content-Type':'application/json','Host':'pizza-shack-x.nbne.uk'})
try:
    r = urllib.request.urlopen(req)
    result = json.loads(r.read().decode())
    if result.get('ok'):
        print(f'LOGIN: OK, role={result.get(\"user\",{}).get(\"role\")}, has_access_token={bool(result.get(\"access\"))}')
    else:
        print(f'LOGIN: FAILED — {result}')
except Exception as e:
    print(f'LOGIN: ERROR — {e}')
    # Also try reading the error body
    import traceback
    traceback.print_exc()
\""
```

### Step 5.3: Test frontend pages respond
```
ssh root@178.104.1.152 "
echo '=== Testing frontend pages ==='
for path in '/' '/order' '/login' '/admin/kitchen' '/admin/orders'; do
  code=\$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3007\$path)
  echo \"  \$path: HTTP \$code\"
done
echo '=== Testing via Nginx ==='
for path in '/' '/order' '/login' '/api/orders/menu/'; do
  code=\$(curl -s -o /dev/null -w '%{http_code}' -k -H 'Host: pizza-shack-x.nbne.uk' https://127.0.0.1\$path)
  echo \"  \$path: HTTP \$code\"
done
"
```

### Step 5.4: Test floe landing page
```
ssh root@178.104.1.152 "
echo '=== Testing floe.nbne.uk ==='
code=\$(curl -s -o /dev/null -w '%{http_code}' -k -H 'Host: floe.nbne.uk' https://127.0.0.1/)
echo \"  /: HTTP \$code\"
curl -s -k -H 'Host: floe.nbne.uk' https://127.0.0.1/ | grep -o 'pizza-shack-x' | head -1 && echo '  Pizza Shack reference: FOUND' || echo '  Pizza Shack reference: NOT FOUND'
"
```

### Step 5.5: Test salon-x still works (regression check)
```
ssh root@178.104.1.152 "
echo '=== Regression: salon-x ==='
code=\$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/)
echo \"  salon-x frontend: HTTP \$code\"
code=\$(curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8001/api/tenant/branding/?tenant=salon-x' -H 'Host: salon-x.nbne.uk')
echo \"  salon-x backend: HTTP \$code\"
"
```

## Phase 6: Final Verification & Exit

### Step 6.1: Run full test suite summary
Compile results from all tests above. If any test failed:
- Diagnose the root cause
- Fix the code
- Commit, push, rebuild
- Re-run the failing test
- Loop until all tests pass

### Step 6.2: Create summary
Once all tests pass, output a final summary:
```
## Pizza Shack X Deployment — COMPLETE ✅

### Live URLs
- Landing: https://pizza-shack-x.nbne.uk
- Order: https://pizza-shack-x.nbne.uk/order
- Kitchen: https://pizza-shack-x.nbne.uk/admin/kitchen
- Admin: https://pizza-shack-x.nbne.uk/admin/orders
- Login: https://pizza-shack-x.nbne.uk/login

### Credentials
- Owner: pizza-shack-x-owner / admin123
- Staff: pizza-shack-x-staff1 / admin123

### What was fixed
- [list of bugs fixed]

### What was built
- [list of new features/pages]

### Test results
- [summary of all tests]
```

### Step 6.3: Exit
Stop. The deployment is complete.

## Micro-Loop Rules
1. **One step at a time.** Complete each step fully before moving to the next.
2. **If a step fails:** Diagnose → fix → re-test. Do NOT move on until it passes.
3. **If stuck after 3 attempts on the same issue:** Log the issue and skip to the next step. Come back later.
4. **SSH commands:** Always use `ssh -o ConnectTimeout=10 root@178.104.1.152 "..."` — never cd.
5. **Git workflow:** Edit locally → commit → `git push origin main` → SSH to pull and rebuild.
6. **Backend-only changes:** Only rebuild backend: `docker compose ... up -d --build backend`
7. **Frontend changes:** Must rebuild frontend: `docker compose ... up -d --build frontend`
8. **Both changed:** Rebuild all: `docker compose ... up -d --build`
9. **Wait for startup:** Backend takes ~60-90s to start (migrations + seed). Check logs before testing.
10. **No user input required.** Run commands, check output, adapt, continue.
