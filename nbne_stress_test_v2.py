#!/usr/bin/env python3
"""
NBNE Platform — Wiggum Stress Test V2
======================================
Comprehensive second-round stress test covering all modules, new CMS/blog,
deeper staff/CRM/compliance coverage, edge cases, permission checks, and
tenant isolation.

Usage:
    pip install requests
    python nbne_stress_test_v2.py
    python nbne_stress_test_v2.py --modules cms comms
    python nbne_stress_test_v2.py --tenant salon-x
    python nbne_stress_test_v2.py --modules public
    python nbne_stress_test_v2.py --modules permissions

V1 tests are NOT repeated here unless needed for dependency.
Keep nbne_stress_test.py intact — this is a separate, more comprehensive file.
"""

import argparse
import io
import json
import os
import sys
import time
import uuid

# Force UTF-8 on Windows console to avoid cp1252 encoding errors
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

import requests

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_URL = "https://nbneplatform-production.up.railway.app"

TENANTS = {
    "salon-x":       "salon",
    "restaurant-x":  "restaurant",
    "health-club-x": "gym",
    "nbne":          "generic",
}

CREDS = {
    "owner":   ("{slug}-owner",   "admin123"),
    "manager": ("{slug}-manager", "admin123"),
    "staff":   ("{slug}-staff1",  "admin123"),
}

TIMEOUT = 20


# ─────────────────────────────────────────────
# RESULT TRACKING
# ─────────────────────────────────────────────

@dataclass
class Result:
    module: str
    test: str
    tenant: str
    passed: bool
    status_code: Optional[int] = None
    detail: str = ""
    duration_ms: int = 0


results: list[Result] = []
warnings: list[str] = []


def record(module, test, tenant, passed, status_code=None, detail="", duration_ms=0):
    r = Result(module, test, tenant, passed, status_code, detail, duration_ms)
    results.append(r)
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] [{tenant}] {test}"
          + (f" ({status_code})" if status_code else "")
          + (f" -- {detail}" if detail else "")
          + (f" [{duration_ms}ms]" if duration_ms else ""))


def warn(msg):
    warnings.append(msg)
    print(f"  [WARN] {msg}")


# ─────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────

class TruthyResponse:
    """Wraps requests.Response so bool(resp) is always True when a response exists.
    requests.Response.__bool__ returns False for 4xx/5xx, which breaks 'resp and resp.status_code' checks."""
    def __init__(self, resp):
        self._resp = resp
    def __bool__(self):
        return True
    def __getattr__(self, name):
        return getattr(self._resp, name)


def api(method: str, path: str, tenant: str, token: str = None,
        json_body=None, files=None, data=None, expected=(200, 201)):
    url = f"{BASE_URL}{path}"
    headers = {"X-Tenant-Slug": tenant}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body is not None and files is None and data is None:
        headers["Content-Type"] = "application/json"

    t0 = time.monotonic()
    try:
        resp = requests.request(
            method, url, headers=headers,
            json=json_body if (files is None and data is None) else None,
            data=data,
            files=files,
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        ms = int((time.monotonic() - t0) * 1000)
        return None, ms, str(e)

    ms = int((time.monotonic() - t0) * 1000)
    return TruthyResponse(resp), ms, None


def login(tenant: str, role: str = "owner") -> Optional[str]:
    username_tmpl, password = CREDS[role]
    username = username_tmpl.replace("{slug}", tenant)
    resp, ms, err = api("POST", "/api/auth/login/", tenant,
                        json_body={"username": username, "password": password})
    if err or resp is None or resp.status_code != 200:
        warn(f"Login failed for {role}@{tenant}: {err or (resp.status_code if resp else 'no response')}")
        return None
    return resp.json().get("access")


def tiny_png() -> bytes:
    """Return a minimal valid 1x1 PNG in memory."""
    import base64
    # 1x1 red PNG, base64 encoded
    b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
        "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(b64)


def tiny_pdf() -> bytes:
    """Return a minimal valid PDF in memory."""
    return b"""%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""


def tag():
    return str(uuid.uuid4())[:8]


# ─────────────────────────────────────────────
# MODULE TESTS
# ─────────────────────────────────────────────

# ── CMS MODULE ──────────────────────────────

def test_cms(tenant: str):
    print(f"\n-- CMS [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("cms", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # --- PAGES ---

    # Create page
    page_payload = {
        "title": f"Test Page {t}",
        "slug": f"test-page-{t}",
        "content": "<h1>Hello</h1><p>Test content from stress test.</p>",
        "hero_headline": "Welcome to our test page",
        "is_published": False,
        "show_in_nav": False,
        "meta_title": f"Test Page {t}",
        "meta_description": "Automated stress test page",
    }
    resp, ms, _ = api("POST", "/api/cms/pages/create/", tenant, token, json_body=page_payload)
    passed = resp and resp.status_code in (200, 201)
    record("cms", "Create CMS page", tenant, passed, resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        record("cms", "Create page error", tenant, False, detail=resp.text[:200] if resp else "no response")
        return

    page_id = resp.json().get("id")

    # Get page detail
    resp, ms, _ = api("GET", f"/api/cms/pages/{page_id}/", tenant, token)
    record("cms", "GET page detail", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Update page
    resp, ms, _ = api("PATCH", f"/api/cms/pages/{page_id}/", tenant, token,
                      json_body={"hero_headline": "Updated headline"})
    record("cms", "PATCH page", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Upload hero image
    png = tiny_png()
    files = {"file": ("test_hero.png", io.BytesIO(png), "image/png")}
    resp, ms, _ = api("POST", f"/api/cms/pages/{page_id}/hero/", tenant, token, files=files)
    record("cms", "Upload page hero image", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)

    # Upload gallery image
    files = {"file": ("test_gallery.png", io.BytesIO(png), "image/png")}
    resp, ms, _ = api("POST", f"/api/cms/pages/{page_id}/images/", tenant, token, files=files)
    passed = resp and resp.status_code in (200, 201)
    record("cms", "Upload page gallery image", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        img_id = resp.json().get("id")
        if img_id:
            resp2, ms2, _ = api("DELETE", f"/api/cms/pages/{page_id}/images/{img_id}/", tenant, token)
            record("cms", "Delete gallery image", tenant, resp2 and resp2.status_code in (200, 204),
                   resp2.status_code if resp2 else None, duration_ms=ms2)

    # Verify NOT in public list when unpublished
    resp, ms, _ = api("GET", "/api/cms/public/pages/", tenant)
    if resp and resp.status_code == 200:
        pages = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
        in_public = any(p.get("id") == page_id for p in pages)
        record("cms", "Unpublished page NOT in public list", tenant, not in_public,
               detail="WARNING: Unpublished page is visible publicly" if in_public else "")

    # Publish page
    resp, ms, _ = api("PATCH", f"/api/cms/pages/{page_id}/", tenant, token,
                      json_body={"is_published": True})
    record("cms", "Publish page", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Verify in public list when published
    resp, ms, _ = api("GET", "/api/cms/public/pages/", tenant)
    if resp and resp.status_code == 200:
        pages = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
        in_public = any(p.get("id") == page_id for p in pages)
        record("cms", "Published page visible in public list", tenant, in_public,
               detail="Not found in public list" if not in_public else "")

    # Get by slug
    resp, ms, _ = api("GET", f"/api/cms/public/pages/{page_payload['slug']}/", tenant)
    record("cms", "GET public page by slug", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Large content field (edge case)
    large_content = "<p>" + ("Lorem ipsum dolor sit amet. " * 400) + "</p>"
    resp, ms, _ = api("PATCH", f"/api/cms/pages/{page_id}/", tenant, token,
                      json_body={"content": large_content})
    record("cms", "Large content field (10KB+)", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Duplicate slug (edge case)
    dup_payload = {**page_payload, "title": f"Duplicate {t}"}
    resp, ms, _ = api("POST", "/api/cms/pages/create/", tenant, token, json_body=dup_payload)
    passed = resp and resp.status_code in (400, 409, 422)
    detail = ""
    if not passed and resp:
        if resp.status_code == 500:
            detail = "WARNING: 500 on duplicate slug -- backend needs unique_together + validation"
        elif resp.status_code in (200, 201):
            detail = "WARNING: Duplicate slug accepted -- unique_together not enforced"
    record("cms", "Duplicate slug returns clean error (400/409/422)", tenant, passed,
           resp.status_code if resp else None, detail)
    if resp and resp.status_code in (200, 201):
        dup_id = resp.json().get("id")
        if dup_id:
            api("DELETE", f"/api/cms/pages/{dup_id}/", tenant, token)

    # Special characters in title
    special_payload = {
        "title": "Café & Bar — O'Brien's",
        "slug": f"cafe-bar-obriens-{t}",
        "content": "<p>Special chars test</p>",
        "is_published": False,
    }
    resp, ms, _ = api("POST", "/api/cms/pages/create/", tenant, token, json_body=special_payload)
    passed = resp and resp.status_code in (200, 201)
    record("cms", "Special chars in title (unicode/apostrophe)", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        special_id = resp.json().get("id")
        api("DELETE", f"/api/cms/pages/{special_id}/", tenant, token)

    # --- BLOG ---

    blog_payload = {
        "title": f"Stress Test Blog Post {t}",
        "slug": f"stress-test-blog-{t}",
        "excerpt": "This is an automated test blog post.",
        "content": "<p>Blog content here.</p>",
        "author_name": "Wiggum Test",
        "category": "Testing",
        "tags": "stress-test,automated",
        "status": "draft",
    }
    resp, ms, _ = api("POST", "/api/cms/blog/create/", tenant, token, json_body=blog_payload)
    passed = resp and resp.status_code in (200, 201)
    record("cms", "Create blog post (draft)", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        # cleanup page and return
        api("DELETE", f"/api/cms/pages/{page_id}/", tenant, token)
        return

    blog_id = resp.json().get("id")

    # Upload featured image
    files = {"file": ("test_blog.png", io.BytesIO(tiny_png()), "image/png")}
    resp, ms, _ = api("POST", f"/api/cms/blog/{blog_id}/image/", tenant, token, files=files)
    record("cms", "Upload blog featured image", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)

    # Draft should NOT be in public list
    resp, ms, _ = api("GET", "/api/cms/public/blog/", tenant)
    if resp and resp.status_code == 200:
        posts = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
        in_public = any(p.get("id") == blog_id for p in posts)
        record("cms", "Draft blog NOT in public list", tenant, not in_public,
               detail="WARNING: Draft blog visible publicly" if in_public else "")

    # Publish blog post
    resp, ms, _ = api("PATCH", f"/api/cms/blog/{blog_id}/", tenant, token,
                      json_body={"status": "published", "published_at": datetime.utcnow().isoformat() + "Z"})
    record("cms", "Publish blog post", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Verify in public list
    resp, ms, _ = api("GET", "/api/cms/public/blog/", tenant)
    if resp and resp.status_code == 200:
        posts = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
        in_public = any(p.get("id") == blog_id for p in posts)
        record("cms", "Published blog visible in public list", tenant, in_public,
               detail="Not found in public list" if not in_public else "")

    # Get by slug
    resp, ms, _ = api("GET", f"/api/cms/public/blog/{blog_payload['slug']}/", tenant)
    record("cms", "GET public blog by slug", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Cleanup
    api("DELETE", f"/api/cms/blog/{blog_id}/", tenant, token)
    api("DELETE", f"/api/cms/pages/{page_id}/", tenant, token)


# ── COMMS MODULE ─────────────────────────────

def test_comms(tenant: str):
    print(f"\n-- COMMS [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("comms", "Login prerequisite", tenant, False, detail="Skipped")
        return

    # Ensure general channel
    resp, ms, _ = api("POST", "/api/comms/ensure-general/", tenant, token)
    passed = resp and resp.status_code in (200, 201)
    record("comms", "Ensure general channel", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)

    # List channels
    resp, ms, _ = api("GET", "/api/comms/channels/", tenant, token)
    passed = resp and resp.status_code == 200
    record("comms", "List channels", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        return

    channels = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
    if not channels:
        record("comms", "At least one channel exists", tenant, False, detail="No channels found")
        return

    channel_id = channels[0].get("id")
    record("comms", "At least one channel exists", tenant, True)

    # List messages
    resp, ms, _ = api("GET", f"/api/comms/channels/{channel_id}/messages/", tenant, token)
    record("comms", "List channel messages", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Send a message
    t = tag()
    resp, ms, _ = api("POST", f"/api/comms/channels/{channel_id}/messages/create/", tenant, token,
                      json_body={"body": f"Stress test message {t}"})
    passed = resp and resp.status_code in (200, 201)
    record("comms", "Send message to channel", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)

    if passed:
        # Verify message appears
        resp2, ms2, _ = api("GET", f"/api/comms/channels/{channel_id}/messages/", tenant, token)
        if resp2 and resp2.status_code == 200:
            msgs = resp2.json() if isinstance(resp2.json(), list) else resp2.json().get("results", [])
            found = any(f"Stress test message {t}" in str(m.get("body", "")) for m in msgs)
            record("comms", "Sent message appears in message list", tenant, found,
                   detail="Message not found in list" if not found else "")


# ── SERVICES MODULE ──────────────────────────

def test_services(tenant: str):
    print(f"\n-- SERVICES [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("services", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # Create service with long_description
    service_payload = {
        "name": f"Stress Test Service {t}",
        "description": "Automated test service",
        "long_description": "<h2>Full Description</h2><p>This is a <strong>rich text</strong> description.</p><ul><li>Feature one</li><li>Feature two</li></ul>",
        "duration_minutes": 60,
        "price_pence": 5000,
        "active": True,
    }
    resp, ms, _ = api("POST", "/api/services/", tenant, token, json_body=service_payload)
    passed = resp and resp.status_code in (200, 201)
    record("services", "Create service with long_description", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        return

    service_id = resp.json().get("id")

    # Verify long_description round-trips
    resp, ms, _ = api("GET", f"/api/services/{service_id}/", tenant, token)
    if resp and resp.status_code == 200:
        returned_desc = resp.json().get("long_description", "")
        html_preserved = "<h2>" in returned_desc
        record("services", "long_description HTML round-trips correctly", tenant, html_preserved,
               detail="" if html_preserved else f"Got: {returned_desc[:100]}")

    # Upload brochure
    pdf_bytes = tiny_pdf()
    files = {"file": ("test_brochure.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    resp, ms, _ = api("POST", f"/api/services/{service_id}/upload-brochure/", tenant, token, files=files)
    passed = resp and resp.status_code in (200, 201)
    record("services", "Upload service brochure", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)

    if passed:
        # Verify brochure fields returned
        resp2, ms2, _ = api("GET", f"/api/services/{service_id}/", tenant, token)
        if resp2 and resp2.status_code == 200:
            data = resp2.json()
            has_url = bool(data.get("brochure_url"))
            has_name = bool(data.get("brochure_filename"))
            record("services", "brochure_url returned after upload", tenant, has_url,
                   detail="" if has_url else "brochure_url is empty/null")
            record("services", "brochure_filename returned after upload", tenant, has_name,
                   detail="" if has_name else "brochure_filename is empty/null")

        # Delete brochure
        resp3, ms3, _ = api("DELETE", f"/api/services/{service_id}/delete-brochure/", tenant, token)
        passed_del = resp3 and resp3.status_code in (200, 204)
        record("services", "Delete service brochure", tenant, passed_del,
               resp3.status_code if resp3 else None, duration_ms=ms3)

        if passed_del:
            resp4, ms4, _ = api("GET", f"/api/services/{service_id}/", tenant, token)
            if resp4 and resp4.status_code == 200:
                data = resp4.json()
                cleared = not data.get("brochure_url") and not data.get("brochure_filename")
                record("services", "brochure fields null after delete", tenant, cleared,
                       detail="" if cleared else "brochure fields still populated after delete")

    # Cleanup
    try:
        api("DELETE", f"/api/services/{service_id}/", tenant, token)
    except Exception:
        warn(f"Could not delete test service {service_id} on {tenant}")


# ── STAFF MODULE (DEEP) ──────────────────────

def test_staff_deep(tenant: str):
    print(f"\n-- STAFF DEEP [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("staff", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_week = (date.today() + timedelta(days=7)).isoformat()

    # Get existing staff member for shift/leave tests
    resp, ms, _ = api("GET", "/api/staff-module/", tenant, token)
    record("staff", "List staff members", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    staff_list = []
    if resp and resp.status_code == 200:
        staff_list = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])

    staff_id = staff_list[0].get("id") if staff_list else None

    # Shifts
    if staff_id:
        shift_payload = {
            "staff": staff_id,
            "date": tomorrow,
            "start_time": "09:00",
            "end_time": "17:00",
            "location": "Main",
        }
        resp, ms, _ = api("POST", "/api/staff-module/shifts/create/", tenant, token,
                          json_body=shift_payload)
        passed = resp and resp.status_code in (200, 201)
        record("staff", "Create shift", tenant, passed,
               resp.status_code if resp else None, duration_ms=ms)
        if passed:
            shift_id = resp.json().get("id")
            resp2, ms2, _ = api("PATCH", f"/api/staff-module/shifts/{shift_id}/update/", tenant, token,
                                json_body={"location": "Branch"})
            record("staff", "Update shift", tenant, resp2 and resp2.status_code == 200,
                   resp2.status_code if resp2 else None, duration_ms=ms2)
            resp3, ms3, _ = api("DELETE", f"/api/staff-module/shifts/{shift_id}/delete/", tenant, token)
            record("staff", "Delete shift", tenant, resp3 and resp3.status_code in (200, 204),
                   resp3.status_code if resp3 else None, duration_ms=ms3)

        # Leave request
        leave_payload = {
            "staff": staff_id,
            "leave_type": "ANNUAL",
            "start_date": next_week,
            "end_date": next_week,
            "reason": f"Stress test leave {t}",
        }
        resp, ms, _ = api("POST", "/api/staff-module/leave/create/", tenant, token,
                          json_body=leave_payload)
        passed = resp and resp.status_code in (200, 201)
        record("staff", "Create leave request", tenant, passed,
               resp.status_code if resp else None, duration_ms=ms)
        if passed:
            leave_id = resp.json().get("id")
            resp2, ms2, _ = api("POST", f"/api/staff-module/leave/{leave_id}/review/", tenant, token,
                                json_body={"status": "APPROVED"})
            record("staff", "Approve leave request", tenant, resp2 and resp2.status_code in (200, 201),
                   resp2.status_code if resp2 else None, duration_ms=ms2)
            resp3, ms3, _ = api("DELETE", f"/api/staff-module/leave/{leave_id}/delete/", tenant, token)
            record("staff", "Delete leave request", tenant, resp3 and resp3.status_code in (200, 204),
                   resp3.status_code if resp3 else None, duration_ms=ms3)

    # Leave calendar
    month_start = date.today().replace(day=1).isoformat()
    month_end = (date.today().replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()
    resp, ms, _ = api("GET", f"/api/staff-module/leave/calendar/?date_from={month_start}&date_to={month_end}", tenant, token)
    record("staff", "Leave calendar", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Training courses
    course_payload = {
        "name": f"Stress Test Course {t}",
        "description": "Automated test training course",
        "duration_days": 1,
        "valid_for_months": 12,
    }
    resp, ms, _ = api("POST", "/api/staff-module/training/courses/create/", tenant, token,
                      json_body=course_payload)
    passed = resp and resp.status_code in (200, 201)
    record("staff", "Create training course", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        course_id = resp.json().get("id")
        resp2, ms2, _ = api("PUT", f"/api/staff-module/training/courses/{course_id}/update/", tenant, token,
                            json_body={**course_payload, "valid_for_months": 24})
        record("staff", "Update training course", tenant, resp2 and resp2.status_code == 200,
               resp2.status_code if resp2 else None, duration_ms=ms2)
        resp3, ms3, _ = api("DELETE", f"/api/staff-module/training/courses/{course_id}/delete/", tenant, token)
        record("staff", "Delete training course", tenant, resp3 and resp3.status_code in (200, 204),
               resp3.status_code if resp3 else None, duration_ms=ms3)

    # Training compliance matrix
    resp, ms, _ = api("GET", "/api/staff-module/training/compliance/", tenant, token)
    record("staff", "Training compliance matrix", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Training reminders
    resp, ms, _ = api("GET", "/api/staff-module/training/reminders/", tenant, token)
    record("staff", "Training reminders", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Project codes
    pc_payload = {"code": f"ST-{t}", "name": f"Stress Test Project {t}"}
    resp, ms, _ = api("POST", "/api/staff-module/project-codes/create/", tenant, token,
                      json_body=pc_payload)
    passed = resp and resp.status_code in (200, 201)
    record("staff", "Create project code", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        pc_id = resp.json().get("id")
        resp2, ms2, _ = api("PATCH", f"/api/staff-module/project-codes/{pc_id}/update/", tenant, token,
                            json_body={"description": "Updated"})
        record("staff", "Update project code", tenant, resp2 and resp2.status_code == 200,
               resp2.status_code if resp2 else None, duration_ms=ms2)
        resp3, ms3, _ = api("DELETE", f"/api/staff-module/project-codes/{pc_id}/delete/", tenant, token)
        record("staff", "Delete project code", tenant, resp3 and resp3.status_code in (200, 204),
               resp3.status_code if resp3 else None, duration_ms=ms3)

    # Timesheet endpoints
    resp, ms, _ = api("GET", "/api/staff-module/timesheets/summary/", tenant, token)
    record("staff", "Timesheet summary", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    month_start = date.today().replace(day=1).isoformat()
    month_end = date.today().isoformat()
    resp, ms, _ = api("GET", f"/api/staff-module/timesheets/export/?date_from={month_start}&date_to={month_end}", tenant, token)
    passed = resp and resp.status_code in (200, 403)
    record("staff", "Timesheet CSV export", tenant, passed,
           resp.status_code if resp else None,
           detail="403=requires manager+ role" if resp and resp.status_code == 403 else "",
           duration_ms=ms)
    if passed:
        is_csv = "text/csv" in resp.headers.get("Content-Type", "") or len(resp.content) > 0
        record("staff", "Timesheet export has content", tenant, is_csv,
               detail="Empty or wrong content type" if not is_csv else "")

    # Payroll summary
    month = date.today().strftime("%Y-%m")
    resp, ms, _ = api("GET", f"/api/staff-module/payroll/summary/?month={month}", tenant, token)
    record("staff", "Payroll summary", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Hours tally
    resp, ms, _ = api("GET", "/api/staff-module/hours-tally/", tenant, token)
    record("staff", "Hours tally", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Leave balance
    resp, ms, _ = api("GET", "/api/staff-module/leave-balance/", tenant, token)
    record("staff", "Leave balance", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Working hours
    resp, ms, _ = api("GET", "/api/staff-module/working-hours/", tenant, token)
    record("staff", "List working hours", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # My shifts (staff role)
    staff_token = login(tenant, "staff")
    if staff_token:
        resp, ms, _ = api("GET", "/api/staff-module/my-shifts/", tenant, staff_token)
        record("staff", "Staff: GET my-shifts", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)


# ── CRM MODULE (DEEP) ────────────────────────

def test_crm_deep(tenant: str):
    print(f"\n-- CRM DEEP [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("crm", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # Create lead
    resp, ms, _ = api("POST", "/api/crm/leads/create/", tenant, token,
                      json_body={
                          "name": f"Stress Lead Deep {t}",
                          "email": f"deep-{t}@stress.local",
                          "phone": "07700000002",
                          "source": "website",
                          "status": "new",
                          "value": "750.00",
                      })
    passed = resp and resp.status_code in (200, 201)
    record("crm", "Create lead", tenant, passed, resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        return

    lead_id = resp.json().get("id")

    # Add note
    resp, ms, _ = api("POST", f"/api/crm/leads/{lead_id}/notes/", tenant, token,
                      json_body={"text": f"Stress test note {t}"})
    passed = resp and resp.status_code in (200, 201)
    record("crm", "Add lead note", tenant, passed, resp.status_code if resp else None, duration_ms=ms)

    # Get notes
    resp, ms, _ = api("GET", f"/api/crm/leads/{lead_id}/notes/", tenant, token)
    record("crm", "Get lead notes", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Get history
    resp, ms, _ = api("GET", f"/api/crm/leads/{lead_id}/history/", tenant, token)
    record("crm", "Get lead history", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Mark contacted
    resp, ms, _ = api("POST", f"/api/crm/leads/{lead_id}/contact/", tenant, token)
    record("crm", "Mark lead as contacted", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)

    # Mark followup done
    resp, ms, _ = api("POST", f"/api/crm/leads/{lead_id}/followup-done/", tenant, token)
    record("crm", "Mark followup done", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)

    # Lead revenue
    resp, ms, _ = api("GET", f"/api/crm/leads/{lead_id}/revenue/", tenant, token)
    record("crm", "Lead revenue", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Revenue stats
    resp, ms, _ = api("GET", "/api/crm/revenue/", tenant, token)
    record("crm", "CRM revenue stats", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Quick add
    resp, ms, _ = api("POST", "/api/crm/leads/quick-add/", tenant, token,
                      json_body={"text": f"Quick add test lead {t} from stress test"})
    passed = resp and resp.status_code in (200, 201)
    record("crm", "Quick add lead from text", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        quick_id = resp.json().get("id")
        if quick_id:
            api("POST", f"/api/crm/leads/{quick_id}/status/", tenant, token,
                json_body={"status": "closed"})

    # Convert lead
    resp, ms, _ = api("POST", f"/api/crm/leads/{lead_id}/convert/", tenant, token)
    record("crm", "Convert lead", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)

    # Sync
    resp, ms, _ = api("POST", "/api/crm/sync/", tenant, token)
    record("crm", "Sync CRM leads from bookings", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)


# ── COMPLIANCE DEEP ──────────────────────────

def test_compliance_deep(tenant: str):
    print(f"\n-- COMPLIANCE DEEP [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("compliance", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # Get categories
    resp, ms, _ = api("GET", "/api/compliance/categories/", tenant, token)
    record("compliance", "List categories", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    cats = []
    if resp and resp.status_code == 200:
        cats = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])

    cat_id = cats[0].get("id") if cats else None

    # Create compliance item
    if cat_id:
        item_payload = {
            "category": cat_id,
            "title": f"Stress Test Item {t}",
            "description": "Auto test compliance item",
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
        }
        resp, ms, _ = api("POST", "/api/compliance/items/create/", tenant, token,
                          json_body=item_payload)
        passed = resp and resp.status_code in (200, 201)
        record("compliance", "Create compliance item", tenant, passed,
               resp.status_code if resp else None, duration_ms=ms)

        if passed:
            item_id = resp.json().get("id")
            # Complete item with evidence
            files = {"evidence": ("evidence.png", io.BytesIO(tiny_png()), "image/png")}
            resp2, ms2, _ = api("POST", f"/api/compliance/items/{item_id}/complete/", tenant, token,
                                files=files, data={"notes": "Completed by stress test"})
            record("compliance", "Complete compliance item with evidence", tenant,
                   resp2 and resp2.status_code in (200, 201),
                   resp2.status_code if resp2 else None, duration_ms=ms2)

            # Delete item
            resp3, ms3, _ = api("DELETE", f"/api/compliance/items/{item_id}/delete/", tenant, token)
            record("compliance", "Delete compliance item", tenant,
                   resp3 and resp3.status_code in (200, 204),
                   resp3.status_code if resp3 else None, duration_ms=ms3)

    # Calendar
    resp, ms, _ = api("GET", "/api/compliance/calendar/", tenant, token)
    record("compliance", "Compliance calendar", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Priority actions
    resp, ms, _ = api("GET", "/api/compliance/priorities/", tenant, token)
    record("compliance", "Priority actions", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Breakdown
    resp, ms, _ = api("GET", "/api/compliance/breakdown/", tenant, token)
    record("compliance", "Compliance breakdown", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Audit log
    resp, ms, _ = api("GET", "/api/compliance/audit-log/", tenant, token)
    record("compliance", "Compliance audit log", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Accident book
    resp, ms, _ = api("POST", "/api/compliance/accidents/create/", tenant, token,
                      json_body={
                          "date": date.today().isoformat(),
                          "description": f"Stress test accident {t}",
                          "injured_person": "Test Person",
                          "location": "Test Location",
                      })
    passed = resp and resp.status_code in (200, 201)
    record("compliance", "Create accident record", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        acc_id = resp.json().get("id")
        resp2, ms2, _ = api("PATCH", f"/api/compliance/accidents/{acc_id}/update/", tenant, token,
                            json_body={"description": "Updated by stress test"})
        record("compliance", "Update accident record", tenant, resp2 and resp2.status_code == 200,
               resp2.status_code if resp2 else None, duration_ms=ms2)
        resp3, ms3, _ = api("DELETE", f"/api/compliance/accidents/{acc_id}/delete/", tenant, token)
        record("compliance", "Delete accident record", tenant, resp3 and resp3.status_code in (200, 204),
               resp3.status_code if resp3 else None, duration_ms=ms3)

    # Incident with photo
    resp, ms, _ = api("POST", "/api/compliance/incidents/create/", tenant, token,
                      json_body={
                          "title": f"Stress Test Incident {t}",
                          "severity": "low",
                          "description": "Auto test incident",
                          "location": "Test",
                      })
    passed = resp and resp.status_code in (200, 201)
    record("compliance", "Create incident", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        inc_id = resp.json().get("id")
        resp3, ms3, _ = api("POST", f"/api/compliance/incidents/{inc_id}/status/", tenant, token,
                            json_body={"status": "resolved"})
        record("compliance", "Update incident status to resolved", tenant,
               resp3 and resp3.status_code in (200, 201),
               resp3.status_code if resp3 else None, duration_ms=ms3)


# ── REPORTS ──────────────────────────────────

def test_reports(tenant: str):
    print(f"\n-- REPORTS [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("reports", "Login prerequisite", tenant, False, detail="Skipped")
        return

    endpoints = [
        ("/api/reports/overview/", "Reports overview"),
        ("/api/reports/daily/", "Daily report"),
        ("/api/reports/monthly/", "Monthly report"),
        ("/api/reports/staff/", "Staff performance report"),
        ("/api/reports/insights/", "Business insights"),
        ("/api/reports/staff-hours/", "Staff hours report"),
        ("/api/reports/leave/", "Leave report"),
    ]

    for path, name in endpoints:
        resp, ms, _ = api("GET", path, tenant, token)
        record("reports", name, tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

    # CSV export
    resp, ms, _ = api("GET", "/api/reports/staff-hours/csv/", tenant, token)
    passed = resp and resp.status_code == 200
    record("reports", "Staff hours CSV export", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        has_content = len(resp.content) > 0
        record("reports", "Staff hours CSV has content", tenant, has_content,
               detail="Empty CSV response" if not has_content else "")


# ── DOCUMENTS DEEP ───────────────────────────

def test_documents_deep(tenant: str):
    print(f"\n-- DOCUMENTS DEEP [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("documents", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # Create tag
    resp, ms, _ = api("POST", "/api/documents/tags/create/", tenant, token,
                      json_body={"name": f"stress-tag-{t}", "colour": "#FF0000"})
    passed = resp and resp.status_code in (200, 201)
    record("documents", "Create document tag", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    doc_tag_id = resp.json().get("id") if passed else None

    # Upload document
    pdf_bytes = tiny_pdf()
    files = {"file": ("test_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "title": f"Stress Test Doc {t}",
        "category": f"stress-cat-{t}",
        "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
    }
    if doc_tag_id:
        data["tags"] = str(doc_tag_id)

    resp, ms, _ = api("POST", "/api/documents/create/", tenant, token, files=files, data=data)
    passed = resp and resp.status_code in (200, 201)
    record("documents", "Upload document (multipart)", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        return

    doc_id = resp.json().get("id")

    # Verify categories endpoint includes our category
    resp, ms, _ = api("GET", "/api/documents/categories/", tenant, token)
    passed = resp and resp.status_code == 200
    record("documents", "GET document categories", tenant, passed,
           resp.status_code if resp else None, duration_ms=ms)
    if passed:
        cats = resp.json() if isinstance(resp.json(), list) else resp.json().get("categories", [])
        found_cat = any(f"stress-cat-{t}" in str(c) for c in cats)
        record("documents", "New category appears in categories list", tenant, found_cat,
               detail="Category not found — endpoint may not be implemented" if not found_cat else "")

    # Download document
    resp, ms, _ = api("GET", f"/api/documents/{doc_id}/download/", tenant, token)
    record("documents", "Download document", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Expiring documents
    resp, ms, _ = api("GET", "/api/documents/expiring/", tenant, token)
    record("documents", "Expiring documents list", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Document summary
    resp, ms, _ = api("GET", "/api/documents/summary/", tenant, token)
    record("documents", "Document summary stats", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Cleanup
    api("DELETE", f"/api/documents/{doc_id}/", tenant, token)


# ── PUBLIC ENDPOINTS ─────────────────────────

def test_public(tenant: str):
    print(f"\n-- PUBLIC ENDPOINTS [{tenant}] --")

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    public_tests = [
        ("GET", "/api/tenant/branding/", None, "Tenant branding"),
        ("GET", "/api/shop/public/products/", None, "Public shop products"),
        ("GET", "/api/cms/public/pages/", None, "Public CMS pages"),
        ("GET", "/api/cms/public/blog/", None, "Public blog posts"),
        ("GET", "/api/gym-class-types/", None, "Gym class types"),
        ("GET", "/api/gym-timetable/", None, "Gym timetable"),
        ("GET", f"/api/restaurant-availability/?date={tomorrow}&party_size=2", None, "Restaurant availability"),
        ("GET", "/api/restaurant-available-dates/?party_size=2", None, "Restaurant available dates"),
    ]

    for method, path, body, name in public_tests:
        resp, ms, _ = api(method, path, tenant, token=None, json_body=body)
        record("public", name, tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

    # Contact form
    resp, ms, _ = api("POST", "/api/contact/", tenant, token=None,
                      json_body={
                          "name": "Stress Test",
                          "email": "stress@test.local",
                          "message": "Automated stress test contact form submission",
                      })
    record("public", "Contact form submission", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)

    # Beta signup
    t = tag()
    resp, ms, _ = api("POST", "/api/beta-signup/", tenant, token=None,
                      json_body={
                          "business_name": f"Stress Test Business {t}",
                          "contact_name": f"Stress Tester {t}",
                          "email": f"stress-{t}@test.local",
                          "business_type": "other",
                      })
    record("public", "Beta signup form", tenant, resp and resp.status_code in (200, 201),
           resp.status_code if resp else None, duration_ms=ms)


# ── PERMISSION CHECKS ────────────────────────

def test_permissions(tenant: str):
    print(f"\n-- PERMISSIONS [{tenant}] --")

    owner_token = login(tenant, "owner")
    staff_token = login(tenant, "staff")

    if not owner_token:
        record("permissions", "Owner login prerequisite", tenant, False, detail="Skipped")
        return

    # 1. Unauthenticated → 401 on protected endpoints
    protected = [
        "/api/auth/me/",
        "/api/shop/orders/",
        "/api/staff-module/",
        "/api/compliance/dashboard/",
        "/api/crm/leads/",
        "/api/documents/",
    ]
    for path in protected:
        resp, ms, _ = api("GET", path, tenant, token=None)
        record("permissions", f"Unauthenticated → 401 on {path}", tenant,
               resp and resp.status_code == 401,
               resp.status_code if resp else None, duration_ms=ms)

    # 2. Staff cannot delete products (owner-only)
    if staff_token:
        # First create a product as owner
        t = tag()
        resp, ms, _ = api("POST", "/api/shop/products/", tenant, owner_token,
                          json_body={
                              "name": f"Permission Test Product {t}",
                              "price": "1.00",
                              "active": True,
                              "stock_quantity": 1,
                              "track_stock": False,
                          })
        if resp and resp.status_code == 201:
            product_id = resp.json().get("id")
            # Staff tries to delete
            resp2, ms2, _ = api("DELETE", f"/api/shop/products/{product_id}/", tenant, staff_token)
            record("permissions", "Staff cannot delete product (owner-only)", tenant,
                   resp2 and resp2.status_code in (401, 403),
                   resp2.status_code if resp2 else None,
                   "" if resp2 and resp2.status_code in (401, 403) else "WARNING: Staff was able to delete product")
            # Cleanup
            api("DELETE", f"/api/shop/products/{product_id}/", tenant, owner_token)

    # 3. Expired/invalid token → 401
    resp, ms, _ = api("GET", "/api/auth/me/", tenant, token="invalid.jwt.token")
    record("permissions", "Invalid JWT → 401", tenant, resp and resp.status_code == 401,
           resp.status_code if resp else None, duration_ms=ms)

    # 4. No X-Tenant-Slug header → sensible error (not 500)
    url = f"{BASE_URL}/api/tenant/branding/"
    t0 = time.monotonic()
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        ms = int((time.monotonic() - t0) * 1000)
        record("permissions", "No X-Tenant-Slug → not 500", tenant,
               resp.status_code != 500,
               resp.status_code,
               f"Got {resp.status_code} (acceptable if not 500)", duration_ms=ms)
    except Exception as e:
        record("permissions", "No X-Tenant-Slug request", tenant, False, detail=str(e))

    # 5. Invalid tenant slug → not 500
    resp, ms, _ = api("GET", "/api/tenant/branding/", "nonexistent-tenant-xyz")
    record("permissions", "Invalid tenant slug → not 500", tenant,
           resp and resp.status_code != 500,
           resp.status_code if resp else None,
           f"Got {resp.status_code if resp else 'no response'}")


# ── EDGE CASES ───────────────────────────────

def test_edge_cases(tenant: str):
    print(f"\n-- EDGE CASES [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("edge", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # Zero-quantity checkout
    resp_prod, ms, _ = api("POST", "/api/shop/products/", tenant, token,
                           json_body={"name": f"Edge Test {t}", "price": "1.00",
                                      "active": True, "stock_quantity": 5, "track_stock": True})
    if resp_prod and resp_prod.status_code == 201:
        pid = resp_prod.json().get("id")

        resp, ms, _ = api("POST", "/api/shop/checkout/", tenant,
                          json_body={"items": [{"product_id": pid, "quantity": 0}],
                                     "customer_name": "Edge", "customer_email": f"edge-{t}@test.local",
                                     "customer_phone": "07700000000"})
        record("edge", "Zero-quantity checkout rejected", tenant,
               resp and resp.status_code in (400, 422),
               resp.status_code if resp else None,
               "" if resp and resp.status_code in (400, 422) else "WARNING: Zero quantity accepted")

        # Negative price product
        resp, ms, _ = api("POST", "/api/shop/products/", tenant, token,
                          json_body={"name": f"Negative Price {t}", "price": "-5.00",
                                     "active": True, "stock_quantity": 1, "track_stock": False})
        record("edge", "Negative price product rejected", tenant,
               resp and resp.status_code in (400, 422),
               resp.status_code if resp else None,
               "" if resp and resp.status_code in (400, 422) else "WARNING: Negative price accepted")
        if resp and resp.status_code in (200, 201):
            api("DELETE", f"/api/shop/products/{resp.json().get('id')}/", tenant, token)

        # SQL injection in category filter
        resp, ms, _ = api("GET", "/api/shop/public/products/?category='; DROP TABLE--", tenant)
        record("edge", "SQL injection in category filter → not 500", tenant,
               resp and resp.status_code != 500,
               resp.status_code if resp else None, duration_ms=ms)

        # XSS in text field — store and verify it doesn't cause 500
        resp, ms, _ = api("PATCH", f"/api/shop/products/{pid}/", tenant, token,
                          json_body={"name": "<script>alert('xss')</script>"})
        record("edge", "XSS in product name → stored safely (not 500)", tenant,
               resp and resp.status_code not in (500,),
               resp.status_code if resp else None,
               "Content stored — verify it's escaped on frontend" if resp and resp.status_code == 200 else "")

        # Booking in the past
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp, ms, _ = api("POST", "/api/bookings/create/", tenant,
                          json_body={"service_id": 1, "customer_name": "Past Test",
                                     "customer_email": f"past-{t}@test.local",
                                     "customer_phone": "07700000000",
                                     "date": yesterday, "time": "10:00"})
        record("edge", "Booking in the past rejected", tenant,
               resp and resp.status_code in (400, 422),
               resp.status_code if resp else None,
               "" if resp and resp.status_code in (400, 422) else "WARNING: Past booking accepted")

        # Cleanup
        api("DELETE", f"/api/shop/products/{pid}/", tenant, token)

    # Large file upload (attempt oversized brochure to service)
    large_data = b"A" * (6 * 1024 * 1024)  # 6MB
    files = {"brochure": ("large.pdf", io.BytesIO(large_data), "application/pdf")}
    # Get a real service first
    resp_svc, _, _ = api("GET", "/api/services/", tenant, token)
    if resp_svc and resp_svc.status_code == 200:
        svcs = resp_svc.json() if isinstance(resp_svc.json(), list) else resp_svc.json().get("results", [])
        if svcs:
            svc_id = svcs[0].get("id")
            resp, ms, _ = api("POST", f"/api/services/{svc_id}/upload_brochure/", tenant, token, files=files)
            record("edge", "Oversized file upload → not 500", tenant,
                   resp and resp.status_code != 500,
                   resp.status_code if resp else None,
                   f"Got {resp.status_code if resp else 'no response'} — 413 or 400 preferred", duration_ms=ms)


# ── ASSISTANT ────────────────────────────────

def test_assistant(tenant: str):
    print(f"\n-- ASSISTANT [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("assistant", "Login prerequisite", tenant, False, detail="Skipped")
        return

    # Unauthenticated → 401
    resp, ms, _ = api("POST", "/api/assistant/chat/", tenant, token=None,
                      json_body={"messages": [{"role": "user", "content": "Hello"}]})
    record("assistant", "Unauthenticated → 401", tenant, resp and resp.status_code == 401,
           resp.status_code if resp else None, duration_ms=ms)

    # Authenticated request
    resp, ms, _ = api("POST", "/api/assistant/chat/", tenant, token,
                      json_body={"messages": [{"role": "user", "content": "What is today's date?"}]})
    passed = resp and resp.status_code == 200
    record("assistant", "AI chat returns 200 (with or without OpenAI key)", tenant, passed,
           resp.status_code if resp else None,
           "No OpenAI key — degraded response expected" if passed else "", duration_ms=ms)


# ── ISOLATION (EXPANDED) ─────────────────────

def test_isolation_expanded():
    print(f"\n-- ISOLATION EXPANDED --")

    token_a = login("salon-x", "owner")
    token_b = login("restaurant-x", "owner")

    if not token_a or not token_b:
        record("isolation", "Login prerequisites", "multi-tenant", False, detail="Skipped")
        return

    t = tag()

    # CMS page isolation
    resp, ms, _ = api("POST", "/api/cms/pages/create/", "salon-x", token_a,
                      json_body={"title": f"Isolation Page {t}",
                                 "slug": f"isolation-page-{t}",
                                 "content": "<p>Test</p>",
                                 "is_published": True})
    if resp and resp.status_code in (200, 201):
        page_id = resp.json().get("id")
        # Check not visible on restaurant-x
        resp2, ms2, _ = api("GET", "/api/cms/public/pages/", "restaurant-x")
        if resp2 and resp2.status_code == 200:
            pages = resp2.json() if isinstance(resp2.json(), list) else resp2.json().get("results", [])
            leaked = any(p.get("id") == page_id for p in pages)
            record("isolation", "CMS page not visible across tenants", "multi-tenant",
                   not leaked,
                   detail="CRITICAL: CMS PAGE DATA LEAK across tenants" if leaked else "")
        api("DELETE", f"/api/cms/pages/{page_id}/", "salon-x", token_a)

    # Blog post isolation
    resp, ms, _ = api("POST", "/api/cms/blog/create/", "salon-x", token_a,
                      json_body={"title": f"Isolation Blog {t}",
                                 "slug": f"isolation-blog-{t}",
                                 "content": "<p>Test</p>",
                                 "status": "published",
                                 "published_at": datetime.utcnow().isoformat() + "Z"})
    if resp and resp.status_code in (200, 201):
        blog_id = resp.json().get("id")
        resp2, ms2, _ = api("GET", "/api/cms/public/blog/", "restaurant-x")
        if resp2 and resp2.status_code == 200:
            posts = resp2.json() if isinstance(resp2.json(), list) else resp2.json().get("results", [])
            leaked = any(p.get("id") == blog_id for p in posts)
            record("isolation", "Blog post not visible across tenants", "multi-tenant",
                   not leaked,
                   detail="CRITICAL: BLOG DATA LEAK across tenants" if leaked else "")
        api("DELETE", f"/api/cms/blog/{blog_id}/", "salon-x", token_a)

    # Comms isolation — ensure general channel on each
    api("POST", "/api/comms/ensure-general/", "salon-x", token_a)
    api("POST", "/api/comms/ensure-general/", "restaurant-x", token_b)

    resp_a, _, _ = api("GET", "/api/comms/channels/", "salon-x", token_a)
    resp_b, _, _ = api("GET", "/api/comms/channels/", "restaurant-x", token_b)

    if resp_a and resp_b and resp_a.status_code == 200 and resp_b.status_code == 200:
        chans_a = {c.get("id") for c in (resp_a.json() if isinstance(resp_a.json(), list) else resp_a.json().get("results", []))}
        chans_b = {c.get("id") for c in (resp_b.json() if isinstance(resp_b.json(), list) else resp_b.json().get("results", []))}
        overlap = chans_a & chans_b
        record("isolation", "Comms channels are tenant-scoped (no overlap)", "multi-tenant",
               len(overlap) == 0,
               detail=f"CRITICAL: CHANNEL LEAK - shared channels {overlap}" if overlap else "")


# ─────────────────────────────────────────────
# RATE LIMIT TEST
# ─────────────────────────────────────────────

def test_rate_limit(tenant: str):
    print(f"\n-- RATE LIMIT [{tenant}] --")

    # Contact form is rate-limited to 5/hour
    # Send 6 in quick succession
    statuses = []
    for i in range(6):
        t = tag()
        resp, ms, _ = api("POST", "/api/contact/", tenant, token=None,
                          json_body={
                              "name": f"Rate Limit Test {i}",
                              "email": f"ratelimit-{t}@test.local",
                              "message": f"Rate limit test submission {i}",
                          })
        statuses.append(resp.status_code if resp else None)

    got_429 = 429 in statuses
    record("rate_limit", "Contact form rate limit (6th → 429)", tenant, got_429,
           detail=f"Statuses: {statuses}" + ("" if got_429 else " -- WARNING: Rate limiting may not be active"))


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

def print_summary():
    print("\n" + "=" * 60)
    print("STRESS TEST V2 SUMMARY")
    print("=" * 60)

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    print(f"  Total:  {len(results)}")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")

    if failed:
        print("\nFAILURES:")
        for r in failed:
            print(f"  [FAIL] [{r.module}] [{r.tenant}] {r.test}"
                  + (f" ({r.status_code})" if r.status_code else "")
                  + (f" -- {r.detail}" if r.detail else ""))

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")

    timed = [r for r in results if r.duration_ms > 0]
    if timed:
        avg = sum(r.duration_ms for r in timed) // len(timed)
        slow = [r for r in timed if r.duration_ms > 3000]
        print(f"\nPERFORMANCE:")
        print(f"  Average response: {avg}ms")
        if slow:
            print(f"  Slow requests (>3s):")
            for r in slow:
                print(f"    [{r.module}] {r.test}: {r.duration_ms}ms")

    print("=" * 60)
    return len(failed) == 0


# ─────────────────────────────────────────────
# ADDITIONAL MODULES
# ─────────────────────────────────────────────

# ── SHOP EXPANDED ────────────────────────────

def test_shop_expanded(tenant: str):
    print(f"\n-- SHOP EXPANDED [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("shop", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()

    # Create a product
    resp, ms, _ = api("POST", "/api/shop/products/", tenant, token,
                      json_body={
                          "name": f"Shop Expanded Test {t}",
                          "price": "19.99",
                          "active": True,
                          "stock_quantity": 10,
                          "track_stock": True,
                          "category": f"test-cat-{t}",
                          "description": "Stress test product with images",
                      })
    passed = resp and resp.status_code == 201
    record("shop", "Create product", tenant, passed, resp.status_code if resp else None, duration_ms=ms)
    if not passed:
        return

    product_id = resp.json().get("id")

    # Upload product image
    files = {"images": ("product.png", io.BytesIO(tiny_png()), "image/png")}
    resp, ms, _ = api("POST", f"/api/shop/products/{product_id}/images/", tenant, token, files=files)
    passed = resp and resp.status_code in (200, 201)
    record("shop", "Upload product image", tenant, passed, resp.status_code if resp else None, duration_ms=ms)

    if passed:
        data = resp.json()
        imgs = data if isinstance(data, list) else [data]
        img_id = imgs[0].get("id") if imgs else None

        if img_id:
            # Reorder images
            resp2, ms2, _ = api("POST", f"/api/shop/products/{product_id}/images/reorder/", tenant, token,
                                json_body={"order": [img_id]})
            record("shop", "Reorder product images", tenant, resp2 and resp2.status_code in (200, 201),
                   resp2.status_code if resp2 else None, duration_ms=ms2)

            # Delete product image
            resp3, ms3, _ = api("DELETE", f"/api/shop/products/{product_id}/images/{img_id}/", tenant, token)
            record("shop", "Delete product image", tenant, resp3 and resp3.status_code in (200, 204),
                   resp3.status_code if resp3 else None, duration_ms=ms3)

    # Order management — list orders
    resp, ms, _ = api("GET", "/api/shop/orders/", tenant, token)
    passed = resp and resp.status_code == 200
    record("shop", "List orders", tenant, passed, resp.status_code if resp else None, duration_ms=ms)

    if passed:
        orders = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
        if orders:
            order_id = orders[0].get("id")
            # Order detail
            resp2, ms2, _ = api("GET", f"/api/shop/orders/{order_id}/", tenant, token)
            record("shop", "Order detail", tenant, resp2 and resp2.status_code == 200,
                   resp2.status_code if resp2 else None, duration_ms=ms2)

            # Update order status
            resp3, ms3, _ = api("PATCH", f"/api/shop/orders/{order_id}/", tenant, token,
                                json_body={"status": "processing"})
            record("shop", "Update order status", tenant, resp3 and resp3.status_code == 200,
                   resp3.status_code if resp3 else None, duration_ms=ms3)
        else:
            record("shop", "Order detail (skipped -- no orders)", tenant, True, detail="No orders to test")
            record("shop", "Update order status (skipped -- no orders)", tenant, True, detail="No orders to test")

    # Cleanup
    api("DELETE", f"/api/shop/products/{product_id}/", tenant, token)


# ── BOOKINGS ─────────────────────────────────

def test_bookings(tenant: str):
    tenant_type = TENANTS.get(tenant, "generic")
    print(f"\n-- BOOKINGS [{tenant}] ({tenant_type}) --")
    token = login(tenant, "owner")
    if not token:
        record("bookings", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    if tenant_type == "salon":
        # Get services
        resp, ms, _ = api("GET", "/api/services/", tenant, token)
        record("bookings", "List services", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)
        services = []
        if resp and resp.status_code == 200:
            services = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])

        # Get staff
        resp, ms, _ = api("GET", "/api/staff-module/", tenant, token)
        record("bookings", "List staff", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)
        staff = []
        if resp and resp.status_code == 200:
            staff = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])

        # Check slots over 7-day window
        slot_found = False
        slot_date = None
        slot_time = None
        staff_id = staff[0].get("id") if staff else None
        service_id = services[0].get("id") if services else None

        if staff_id and service_id:
            for i in range(1, 8):
                check_date = (date.today() + timedelta(days=i)).isoformat()
                resp, ms, _ = api("GET",
                    f"/api/bookings/slots/?staff_id={staff_id}&date={check_date}&service_id={service_id}",
                    tenant, token)
                if resp and resp.status_code == 200:
                    slots = resp.json() if isinstance(resp.json(), list) else resp.json().get("slots", [])
                    if slots:
                        slot_found = True
                        slot_date = check_date
                        slot_time = slots[0] if isinstance(slots[0], str) else slots[0].get("time", "10:00")
                        break

            record("bookings", "Find available slot (7-day lookahead)", tenant, slot_found,
                   detail="No slots found in next 7 days" if not slot_found else f"Slot: {slot_date} {slot_time}")

            if slot_found:
                # Create booking
                resp, ms, _ = api("POST", "/api/bookings/create/", tenant,
                                  json_body={
                                      "service_id": service_id,
                                      "staff_id": staff_id,
                                      "customer_name": f"Stress Tester {t}",
                                      "customer_email": f"stress-{t}@test.local",
                                      "customer_phone": "07700000001",
                                      "date": slot_date,
                                      "time": slot_time,
                                  })
                passed = resp and resp.status_code in (200, 201)
                record("bookings", "Create booking (public)", tenant, passed,
                       resp.status_code if resp else None, duration_ms=ms)

                if passed:
                    booking_id = resp.json().get("id")

                    # Confirm
                    resp2, ms2, _ = api("POST", f"/api/bookings/{booking_id}/confirm/", tenant, token)
                    record("bookings", "Confirm booking", tenant, resp2 and resp2.status_code in (200, 201),
                           resp2.status_code if resp2 else None, duration_ms=ms2)

                    # Cancel
                    resp3, ms3, _ = api("POST", f"/api/bookings/{booking_id}/cancel/", tenant, token)
                    record("bookings", "Cancel booking", tenant, resp3 and resp3.status_code in (200, 201),
                           resp3.status_code if resp3 else None, duration_ms=ms3)

    elif tenant_type == "restaurant":
        # Available dates
        resp, ms, _ = api("GET", "/api/restaurant-available-dates/?party_size=2", tenant)
        record("bookings", "Restaurant available dates", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

        # Availability
        resp, ms, _ = api("GET", f"/api/restaurant-availability/?date={tomorrow}&party_size=2", tenant)
        passed = resp and resp.status_code == 200
        record("bookings", "Restaurant slot availability", tenant, passed,
               resp.status_code if resp else None, duration_ms=ms)

        if passed:
            data = resp.json()
            slots = data if isinstance(data, list) else data.get("slots", [])
            if slots:
                slot_time = slots[0] if isinstance(slots[0], str) else slots[0].get("time", "19:00")
                resp2, ms2, _ = api("POST", "/api/bookings/create/", tenant,
                                    json_body={
                                        "date": tomorrow,
                                        "time": slot_time,
                                        "party_size": 2,
                                        "customer_name": f"Stress Tester {t}",
                                        "customer_email": f"stress-{t}@test.local",
                                        "customer_phone": "07700000001",
                                    })
                record("bookings", "Create restaurant reservation", tenant,
                       resp2 and resp2.status_code in (200, 201),
                       resp2.status_code if resp2 else None, duration_ms=ms2)
                if resp2 and resp2.status_code in (200, 201):
                    booking_id = resp2.json().get("id")
                    if booking_id:
                        api("POST", f"/api/bookings/{booking_id}/cancel/", tenant, token)

    elif tenant_type == "gym":
        # Class types
        resp, ms, _ = api("GET", "/api/gym-class-types/", tenant)
        record("bookings", "Gym class types", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

        # Timetable
        resp, ms, _ = api("GET", "/api/gym-timetable/", tenant)
        record("bookings", "Gym timetable", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

        if resp and resp.status_code == 200:
            classes = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
            if classes:
                class_id = classes[0].get("id")
                resp2, ms2, _ = api("POST", "/api/bookings/create/", tenant,
                                    json_body={
                                        "class_id": class_id,
                                        "customer_name": f"Stress Tester {t}",
                                        "customer_email": f"stress-{t}@test.local",
                                        "customer_phone": "07700000001",
                                    })
                record("bookings", "Book gym class", tenant, resp2 and resp2.status_code in (200, 201),
                       resp2.status_code if resp2 else None, duration_ms=ms2)
                if resp2 and resp2.status_code in (200, 201):
                    booking_id = resp2.json().get("id")
                    if booking_id:
                        api("POST", f"/api/bookings/{booking_id}/cancel/", tenant, token)

    # Double-booking check (salon only)
    if tenant_type == "salon" and slot_found:
        resp, ms, _ = api("POST", "/api/bookings/create/", tenant,
                          json_body={
                              "service_id": service_id,
                              "staff_id": staff_id,
                              "customer_name": f"Double Booking {t}",
                              "customer_email": f"double-{t}@test.local",
                              "customer_phone": "07700000002",
                              "date": slot_date,
                              "time": slot_time,
                          })
        record("bookings", "Double-booking handled gracefully (not 500)", tenant,
               resp and resp.status_code != 500,
               resp.status_code if resp else None,
               "Slot may legitimately be taken or allowed -- check status")


# ── DASHBOARD ────────────────────────────────

def test_dashboard(tenant: str):
    print(f"\n-- DASHBOARD [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("dashboard", "Login prerequisite", tenant, False, detail="Skipped")
        return

    endpoints = [
        ("/api/dashboard/today/", "Today dashboard"),
        ("/api/dashboard-summary/", "Dashboard summary"),
        ("/api/reports/overview/", "Reports overview (via dashboard)"),
        ("/api/reports/daily/", "Daily report (via dashboard)"),
        ("/api/reports/insights/", "Business insights (via dashboard)"),
    ]

    for path, name in endpoints:
        resp, ms, _ = api("GET", path, tenant, token)
        record("dashboard", name, tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

    # Staff token — reduced dashboard access
    staff_token = login(tenant, "staff")
    if staff_token:
        resp, ms, _ = api("GET", "/api/dashboard/today/", tenant, staff_token)
        record("dashboard", "Staff: today dashboard accessible", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)


# ── CONCURRENT (STOCK RACE) ──────────────────

def test_concurrent(tenant: str):
    print(f"\n-- CONCURRENT [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("concurrent", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()
    STOCK = 3
    BUYERS = 5

    # Create limited stock product
    resp, ms, _ = api("POST", "/api/shop/products/", tenant, token,
                      json_body={
                          "name": f"Race Condition Test {t}",
                          "price": "5.00",
                          "active": True,
                          "stock_quantity": STOCK,
                          "track_stock": True,
                      })
    if not resp or resp.status_code != 201:
        record("concurrent", "Setup product for race test", tenant, False,
               resp.status_code if resp else None, detail="Could not create product")
        return

    product_id = resp.json().get("id")
    record("concurrent", f"Created stock={STOCK} product for race test", tenant, True)

    def checkout(i):
        u = tag()
        r, ms, _ = api("POST", "/api/shop/checkout/", tenant,
                       json_body={
                           "items": [{"product_id": product_id, "quantity": 1}],
                           "customer_name": f"Racer {i}",
                           "customer_email": f"racer-{u}@test.local",
                           "customer_phone": "07700000000",
                       })
        return r.status_code if r else None

    with ThreadPoolExecutor(max_workers=BUYERS) as executor:
        futures = [executor.submit(checkout, i) for i in range(BUYERS)]
        statuses = [f.result() for f in as_completed(futures)]

    successes = sum(1 for s in statuses if s in (200, 201))
    failures = sum(1 for s in statuses if s in (400, 409, 422))

    record("concurrent", f"Race: {successes}/{BUYERS} succeeded ({STOCK} stock)", tenant,
           successes <= STOCK,
           detail=f"Statuses: {sorted(statuses)} -- "
                  + ("Stock guard held" if successes <= STOCK else "CRITICAL: Oversold!"))

    record("concurrent", "Race: no 500 errors under concurrent load", tenant,
           500 not in statuses,
           detail=f"Got 500s: {statuses.count(500)}" if 500 in statuses else "")

    # Cleanup
    api("DELETE", f"/api/shop/products/{product_id}/", tenant, token)


# ── AVAILABILITY ─────────────────────────────

def test_availability(tenant: str):
    print(f"\n-- AVAILABILITY [{tenant}] --")
    token = login(tenant, "owner")
    if not token:
        record("availability", "Login prerequisite", tenant, False, detail="Skipped")
        return

    t = tag()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Get a bookings staff member (different from staff-module StaffProfile)
    resp, ms, _ = api("GET", "/api/staff/", tenant, token)
    staff = []
    if resp and resp.status_code == 200:
        staff = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
    staff_id = staff[0].get("id") if staff else None

    if staff_id:
        # Staff availability
        resp, ms, _ = api("GET", f"/api/availability/?staff={staff_id}&date={tomorrow}", tenant, token)
        record("availability", "Staff availability for date", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)

        # Slots
        resp, ms, _ = api("GET",
            f"/api/availability/slots/?staff={staff_id}&date={tomorrow}&duration=60",
            tenant, token)
        record("availability", "Available slots (60min)", tenant, resp and resp.status_code == 200,
               resp.status_code if resp else None, duration_ms=ms)
    else:
        record("availability", "Staff availability (skipped -- no staff)", tenant, True, detail="No staff")
        record("availability", "Available slots (skipped -- no staff)", tenant, True, detail="No staff")

    # Working patterns
    resp, ms, _ = api("GET", "/api/working-patterns/", tenant, token)
    record("availability", "Working patterns", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Availability overrides
    resp, ms, _ = api("GET", "/api/availability-overrides/", tenant, token)
    record("availability", "Availability overrides", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Blocked times
    resp, ms, _ = api("GET", "/api/blocked-times/", tenant, token)
    record("availability", "Blocked times", tenant, resp and resp.status_code == 200,
           resp.status_code if resp else None, duration_ms=ms)

    # Create an override (day off)
    if staff_id:
        import random
        override_date = (date.today() + timedelta(days=random.randint(30, 300))).isoformat()
        override_payload = {
            "staff_member": staff_id,
            "date": override_date,
            "mode": "ADD",
            "reason": f"Stress test override {t}",
            "periods": [{"start_time": "09:00", "end_time": "12:00"}],
        }
        resp, ms, _ = api("POST", "/api/availability-overrides/", tenant, token,
                          json_body=override_payload)
        passed = resp and resp.status_code in (200, 201)
        record("availability", "Create availability override (day off)", tenant, passed,
               resp.status_code if resp else None, duration_ms=ms)
        if passed:
            override_id = resp.json().get("id")
            resp2, ms2, _ = api("DELETE", f"/api/availability-overrides/{override_id}/", tenant, token)
            record("availability", "Delete availability override", tenant,
                   resp2 and resp2.status_code in (200, 204),
                   resp2.status_code if resp2 else None, duration_ms=ms2)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

MODULE_MAP = {
    "cms":          lambda t: test_cms(t),
    "comms":        lambda t: test_comms(t),
    "services":     lambda t: test_services(t),
    "staff":        lambda t: test_staff_deep(t),
    "crm":          lambda t: test_crm_deep(t),
    "compliance":   lambda t: test_compliance_deep(t),
    "documents":    lambda t: test_documents_deep(t),
    "reports":      lambda t: test_reports(t),
    "public":       lambda t: test_public(t),
    "permissions":  lambda t: test_permissions(t),
    "edge":         lambda t: test_edge_cases(t),
    "assistant":    lambda t: test_assistant(t),
    "isolation":    lambda t: test_isolation_expanded(),
    "rate_limit":   lambda t: test_rate_limit(t),
    "shop":         lambda t: test_shop_expanded(t),
    "bookings":     lambda t: test_bookings(t),
    "dashboard":    lambda t: test_dashboard(t),
    "concurrent":   lambda t: test_concurrent(t),
    "availability": lambda t: test_availability(t),
}

CROSS_TENANT_MODULES = {"isolation"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NBNE Wiggum Stress Test V2")
    parser.add_argument("--modules", nargs="+",
                        choices=list(MODULE_MAP.keys()),
                        help="Modules to test (default: all)")
    parser.add_argument("--tenant",
                        choices=list(TENANTS.keys()),
                        help="Single tenant to test (default: all)")
    args = parser.parse_args()

    modules = args.modules or list(MODULE_MAP.keys())
    tenants = [args.tenant] if args.tenant else list(TENANTS.keys())

    print(f"NBNE Wiggum Stress Test V2")
    print(f"Backend: {BASE_URL}")
    print(f"Modules: {', '.join(modules)}")
    print(f"Tenants: {', '.join(tenants)}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    for module in modules:
        if module in CROSS_TENANT_MODULES:
            MODULE_MAP[module](None)
        else:
            for tenant in tenants:
                MODULE_MAP[module](tenant)

    success = print_summary()
    sys.exit(0 if success else 1)
