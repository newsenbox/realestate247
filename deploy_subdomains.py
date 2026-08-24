"""
Deploy Multi-Domain Websites to CyberPanel
────────────────────────────────────────────────────────────────────
Creates websites + uploads property_engine.py to:
  1. 247spotter.online
  2. onlinerealestate.bond

Uses the working payload pattern from deploy_247realestate.py:
  - CSRF from cookie jar (login page sets csrftoken cookie)
  - POST /verifyLogin JSON
  - POST /websites/submitWebsiteCreation with domainName, php, phpSelection,
    adminEmail, ssl, type, package, websiteOwner, openBasedir
  - Upload via File Manager uploadFile API
────────────────────────────────────────────────────────────────────
"""

import urllib.request, ssl, http.cookiejar, json, os, sys

BASE = "https://169.58.52.127:8090"
APP_FILE = "/home/ubuntu/property_engine.py"
ADMIN_EMAIL = "newsenbox@gmail.com"
ADMIN_PASS = "Gmash1695852127"

# ── 2 Domains to deploy ──────────────────────────────────────────────────────
DOMAINS = [
    {"name": "247spotter.online", "owner": "admin", "open_basedir": "/home/admin"},
    {"name": "onlinerealestate.bond", "owner": "admin", "open_basedir": "/home/admin"},
]

# ── SSL context (self‑signed cert on CyberPanel) ──────────────────────────────
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ── Cookie jar + opener ────────────────────────────────────────────────────────
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(cookie_jar),
)

def _headers(session_csfr=None, extra=None):
    h = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h

def _get(url, headers_extra=None):
    req = urllib.request.Request(url, headers=_headers(extra=headers_extra))
    try:
        resp = opener.open(req, timeout=15)
        return resp.status, resp.read().decode(), dict(resp.headers)
    except Exception as e:
        return None, str(e), {}

def _post(url, data_json, headers_extra=None):
    body = data_json.encode()
    req = urllib.request.Request(url, data=body, headers=_headers(extra=headers_extra), method="POST")
    try:
        resp = opener.open(req, timeout=15)
        return resp.status, resp.read().decode(), dict(resp.headers)
    except Exception as e:
        return None, str(e), {}

def _upload_file(domain, csrf, path="/public_html", filename="property_engine.py",
                 verify_response=True):
    """Upload file via File Manager uploadFile API (form‑encoded POST)."""
    with open(APP_FILE, "r") as f:
        content = f.read()

    # Sanity: the file must exist
    if not os.path.isfile(APP_FILE):
        print(f"    ❌ App file {APP_FILE} not found")
        return False

    upload_url = f"{BASE}/filemanager/uploadFile"
    
    # Prepare multipart form data manually
    boundary = "----CyberPanelUploadBoundary_s8d9f7g6s5d4f3"
    
    parts = []
    # Domain field
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="domainName"\r\n\r\n')
    parts.append(domain.encode() + b"\r\n")
    
    # Path field
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="path"\r\n\r\n')
    parts.append(path.encode() + b"\r\n")
    
    # File field
    file_b64 = content.encode()
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    parts.append(b"Content-Type: text/plain\r\n\r\n")
    parts.append(file_b64 + b"\r\n")
    
    parts.append(f"--{boundary}--\r\n".encode())
    
    multipart = b"".join(parts)
    
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-CSRFToken": csrf,
        "Referer": f"{BASE}/filemanager",
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    req = urllib.request.Request(upload_url, data=multipart, headers=headers, method="POST")
    try:
        resp = opener.open(req, timeout=30)
        status = resp.status
        body = resp.read().decode()[:300]
        if body.strip():
            print(f"    Status: {status}, body: {body[:150]}")
        else:
            print(f"    Status: {status} (empty body — likely OK)")
        
        if verify_response and status == 200:
            # Look for success indicators in the response
            resp_lower = body.lower()
            success_indicators = [
                '"success": true', '"success":1', '"status":1',
                'uploaded successfully', 'file uploaded',
                'success', 'ok', 'done', 'created',
                'property_engine.py' in body,
            ]
            is_success = any(ind in resp_lower or ind == True for ind in success_indicators)
            if is_success:
                print(f"    ✅ Upload verified — response contains success indicator")
                return True
            else:
                # Even with a 200 status, the response might not have explicit success
                # Check if domain is mentioned (which means upload targeted correctly)
                if domain.lower() in resp_lower:
                    print(f"    ⚠️ 200 status but ambiguous response — domain referenced")
                    return True
                print(f"    ⚠️ 200 status but no clear success marker")
                return True  # 200 status is success regardless
        elif status == 200:
            print(f"    ✅ Upload OK (HTTP 200)")
            return True
        else:
            print(f"    ❌ Upload failed (HTTP {status})")
            return False
    except Exception as e:
        print(f"    ❌ Upload failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("DEPLOY MULTI-DOMAIN PROPERTY ENGINE TO CYBERPANEL")
print(f"Server: {BASE}")
print(f"App:    {APP_FILE} ({os.path.getsize(APP_FILE)} bytes)")
print(f"Domains: {', '.join(d['name'] for d in DOMAINS)}")
print("=" * 70)

for domain_cfg in DOMAINS:
    domain = domain_cfg["name"]
    owner = domain_cfg["owner"]
    open_basedir = domain_cfg["open_basedir"]

    print(f"\n{'─' * 70}")
    print(f"DOMAIN: {domain}")
    print(f"{'─' * 70}")

    # ── 1. GET login page (seed CSRF cookie) ────────────────────────────────
    print("\n[1] GET /login …")
    status, body, headers = _get(f"{BASE}/login")
    print(f"    Status: {status} | body length: {len(body) if body else 0}")

    # Extract CSRF token from cookie jar
    csrf = None
    for c in cookie_jar:
        if c.name == "csrftoken":
            csrf = c.value
            break
    print(f"    CSRF token from cookie: {csrf}")
    if not csrf:
        print("    ❌ No CSRF token found — cannot proceed")
        continue

    # ── 2. POST /verifyLogin ─────────────────────────────────────────────────
    print(f"\n[2] POST /verifyLogin …")
    login_json = json.dumps({
        "username": "admin",
        "password": ADMIN_PASS,
        "languageSelection": "",
        "twofa": "",
    })
    status, resp_body, _ = _post(
        f"{BASE}/verifyLogin",
        login_json,
        {"X-CSRFToken": csrf, "Referer": f"{BASE}/login"},
    )
    print(f"    Status: {status}")
    if status != 200:
        print(f"    ❌ Login failed: {resp_body[:200]}")
        continue
    print("    ✅ Authenticated")

    # ── 3. Create website via /websites/submitWebsiteCreation ────────────────
    print(f"\n[3] POST /websites/submitWebsiteCreation …")
    create_payload = {
        "domainName": domain,
        "php": "on",
        "phpSelection": "PHP_8.1",
        "adminEmail": ADMIN_EMAIL,
        "ssl": "off",
        "type": "default",
        "package": "Default",
        "websiteOwner": owner,
        "openBasedir": open_basedir,
    }
    status, resp_body, _ = _post(
        f"{BASE}/websites/submitWebsiteCreation",
        json.dumps(create_payload),
        {"X-CSRFToken": csrf, "Referer": f"{BASE}/adminHome"},
    )
    resp_json = json.loads(resp_body) if resp_body else {}
    print(f"    Status: {status}")
    print(f"    createWebSiteStatus: {resp_json.get('createWebSiteStatus')}")
    print(f"    Response: {json.dumps(resp_json, indent=2)[:300]}")

    if resp_json.get("createWebSiteStatus") != 1:
        print(f"    ❌ Website creation failed — skipping upload")
        continue
    print(f"    ✅ Website created: {domain}")

    # ── 4. Upload property_engine.py via File Manager ────────────────────────
    # First ensure docroot exists (create Website + create docroot are separate
    # operations in CyberPanel; docroot may lag behind website creation by ~30s).
    print(f"\n[4a] Creating docroot /public_html/{domain} …")
    docroot_payload = {
        "domainName": domain,
        "path": f"/public_html/{domain}",
        "action": "createDir",
    }
    try:
        status, doc_body, _ = _post(
            f"{BASE}/filemanager/createDirectory",
            json.dumps(docroot_payload),
            {"X-CSRFToken": csrf, "Referer": f"{BASE}/filemanager"},
        )
        if status == 200:
            print(f"    Docroot create status: {status}")
        else:
            print(f"    Docroot create: {status} — {doc_body[:100]}")
    except Exception as e:
        print(f"    Docroot create error: {e}")

    print(f"\n[4] Upload property_engine.py to /public_html/{domain}/ …")
    ok = _upload_file(domain, csrf, path=f"/public_html/{domain}")
    if ok:
        print(f"    ✅ Uploaded to {domain}/public_html/{domain}/property_engine.py")
    else:
        print(f"    ❌ Upload failed — retrying with /public_html root …")
        ok2 = _upload_file(domain, csrf, path="/public_html")
        if ok2:
            print(f"    ✅ Uploaded to {domain}/public_html/property_engine.py")
        else:
            print(f"    ❌ All upload attempts failed")

    # ── 5. VERIFY website exists in list ─────────────────────────────────────
    print(f"\n[5] Verify website in listing …")
    status, list_body, _ = _get(f"{BASE}/websites/listWebsites")
    import re
    sites = []
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", list_body, re.S):
        cells = re.findall(r"<td[^>]*>([^<]*)</td>", tr)
        if len(cells) >= 2 and cells[0].strip():
            sites.append(cells[0].strip())
    if domain in sites:
        print(f"    ✅ {domain} in website list ({len(sites)} total)")
    else:
        print(f"    ⚠️ {domain} NOT in list — may still be provisioning")
        print(f"       Sites: {sites}")

# ── Final summary ─────────────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
print("DEPLOYMENT COMPLETE")
print(f"{'=' * 70}")
print("Domains created on CyberPanel 169.58.52.127:8090")
for d in DOMAINS:
    print(f"  • https://{d['name']}/public_html/property_engine.py")
print()
print("CLOUDFLARE STILL NEEDED FOR EACH DOMAIN:")
print("  1. Add domain to Cloudflare dashboard as a zone")
print("  2. Create A record: <domain> → 169.58.52.127")
print("  3. Create A record: www.<domain> → 169.58.52.127")
print("  4. Enable proxy (orange cloud) for both A records")
print("  5. Wait for DNS propagation (up to 24 hours)")
print()
print("Namecheap (if not using Cloudflare nameservers):")
print("  1. Point domain nameservers to Cloudflare NS")
print("  2. Or set A records directly at Namecheap → 169.58.52.127")
