# How to Get Superset Auth (Cookie or Token)

If your browser uses **cookies** (no `Authorization` header), use the **session cookie** method below. Otherwise use the token method.

---

## Method 1: Session cookie (when you only have cookie, no JWT)

Use this when DevTools shows only cookies and no `Authorization: Bearer` header.

1. **Log in to Superset** in your browser:  
   https://dashboards.bioptimizers.net  
   Sign in with Google until you see the Superset UI.

2. **Open DevTools**  
   Press **F12**.

3. **Open the Application tab**  
   Click **Application** (Chrome/Edge). In Firefox: **Storage** then **Cookies**.

4. **Open Cookies for your Superset site**  
   In the left sidebar under **Cookies**, click  
   `https://dashboards.bioptimizers.net`.

5. **Find the `session` cookie**  
   In the table, find the row where **Name** is `session`.  
   Copy the **Value** (the long string in the Value column).

6. **Use it as SUPERSET_SESSION_COOKIE**  
   The value must be sent as a cookie string. Use either:
   - Just the value: `session=<paste the value here>`
   - Or the full Cookie header if you have more than one cookie: `session=<value>; other=optional`

**Test (PowerShell):**
```powershell
cd C:\Bio\cursor_projects\superset_agent
$env:SUPERSET_URL="https://dashboards.bioptimizers.net"
$env:SUPERSET_SESSION_COOKIE="session=<paste the session value here>"
python test_superset_connection.py
```

**Cursor MCP:** In `C:\Users\zerin\.cursor\mcp.json`, in the `superset` server's `env`, set:
```json
"SUPERSET_SESSION_COOKIE": "session=<paste the session value here>"
```
Remove or leave empty `SUPERSET_ACCESS_TOKEN` when using the cookie. Save and reload MCP.

**Note:** The session expires (e.g. when you close the browser or after some hours). When the MCP or script returns 401, log in again in the browser and copy a fresh `session` cookie value.

---

## Method 2: Access token (when you see Authorization: Bearer in Network)

Use this only if your Superset instance sends a JWT in request headers.

1. **Log in to Superset**  
   https://dashboards.bioptimizers.net (sign in with Google).

2. **Open DevTools** -> **Network** tab.

3. **Trigger a request**  
   Click something in Superset (e.g. Dashboards, Charts). Find a request whose URL contains `/api/`.

4. **Copy the token**  
   Click that request -> **Headers** -> **Request Headers**. Find  
   `Authorization: Bearer eyJ...`  
   Copy only the part **after `Bearer `** (the long string starting with `eyJ`).

5. **Use it as SUPERSET_ACCESS_TOKEN**  
   Set `SUPERSET_ACCESS_TOKEN` to that string (in env or in Cursor MCP config).

---

## Method 3: Local Storage (if your app stores a JWT there)

1. Log in to Superset, then **F12** -> **Application** -> **Local Storage** -> `https://dashboards.bioptimizers.net`.
2. Look for a key like `access_token` or `token`. Copy its **value** (often starts with `eyJ`).
3. Use that value as `SUPERSET_ACCESS_TOKEN`.

---

## Summary

| You have              | Set this                     |
|-----------------------|------------------------------|
| Only cookie (session) | `SUPERSET_SESSION_COOKIE` = `session=<value>` |
| JWT in headers/storage| `SUPERSET_ACCESS_TOKEN` = `<token>`          |
| Username + password   | `SUPERSET_USERNAME` + `SUPERSET_PASSWORD`    |

After updating, run `python test_superset_connection.py` (with the same env) or reload MCP in Cursor.
