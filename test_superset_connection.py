#!/usr/bin/env python3
"""
Quick test script to verify Superset connection.
Run from project root with env vars set.

Cookie (when you only have cookie, no Authorization header):
  set SUPERSET_URL=https://dashboards.bioptimizers.net
  set SUPERSET_SESSION_COOKIE=session=<paste cookie value>
  python test_superset_connection.py

Or token / username+password - see GET_TOKEN.md.
"""
from __future__ import annotations

import os
import sys

# Add project so mcp_superset is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main() -> None:
    base_url = (os.environ.get("SUPERSET_URL") or "https://dashboards.bioptimizers.net").strip().rstrip("/")
    token = (os.environ.get("SUPERSET_ACCESS_TOKEN") or "").strip()
    session_cookie = (os.environ.get("SUPERSET_SESSION_COOKIE") or "").strip()
    username = (os.environ.get("SUPERSET_USERNAME") or "").strip()
    password = (os.environ.get("SUPERSET_PASSWORD") or "").strip()

    if session_cookie:
        pass  # use cookie
    elif token and token.upper() not in ("PASTE_TOKEN_FROM_BROWSER", "YOUR_TOKEN", ""):
        pass  # use token
    elif username and password:
        pass  # use username/password
    else:
        print("Missing credentials. Set one of:")
        print("  SUPERSET_SESSION_COOKIE  (e.g. session=xxx from browser cookies - see GET_TOKEN.md)")
        print("  SUPERSET_ACCESS_TOKEN    (JWT from browser)")
        print("  SUPERSET_USERNAME + SUPERSET_PASSWORD")
        print()
        print("Example with cookie (PowerShell):")
        print('  $env:SUPERSET_URL="https://dashboards.bioptimizers.net"')
        print('  $env:SUPERSET_SESSION_COOKIE="session=<paste value from Application -> Cookies>"')
        print("  python test_superset_connection.py")
        sys.exit(1)

    from mcp_superset.client import SupersetClient, SupersetAPIError

    try:
        if session_cookie:
            client = SupersetClient(base_url=base_url, session_cookie=session_cookie)
            print("Using SUPERSET_SESSION_COOKIE.")
        elif token:
            client = SupersetClient(base_url=base_url, access_token=token)
            print("Using SUPERSET_ACCESS_TOKEN.")
        else:
            client = SupersetClient(base_url=base_url, username=username, password=password)
            print("Using username/password.")
    except Exception as e:
        print(f"Client init failed: {e}")
        sys.exit(1)

    print(f"Connecting to {base_url} ...")
    print()

    try:
        dbs = client.list_databases()
        print(f"Databases ({len(dbs)}):")
        for db in dbs[:10]:
            print(f"  - id={db.get('id')} name={db.get('database_name', db.get('name', '?'))}")
        if len(dbs) > 10:
            print(f"  ... and {len(dbs) - 10} more")
        print()
    except SupersetAPIError as e:
        print(f"List databases failed: {e}")
        if e.status_code == 401:
            print("Token may be expired or invalid. Get a fresh token from the browser.")
        sys.exit(1)

    try:
        dashboards = client.list_dashboards()
        print(f"Dashboards ({len(dashboards)}):")
        for d in dashboards[:10]:
            print(f"  - id={d.get('id')} title={d.get('dashboard_title', '?')}")
        if len(dashboards) > 10:
            print(f"  ... and {len(dashboards) - 10} more")
        print()
    except SupersetAPIError as e:
        print(f"List dashboards failed: {e}")
        sys.exit(1)

    print("Connection OK. You can use the Superset MCP tools in Cursor.")
    print("Make sure the same SUPERSET_URL and SUPERSET_SESSION_COOKIE (or SUPERSET_ACCESS_TOKEN) are in Cursor MCP config, then reload MCP.")


if __name__ == "__main__":
    main()
