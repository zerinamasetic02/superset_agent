# Setup for Your Team (Colleagues)

Use this when **sharing the Superset agent** with others. Everyone gets the same code; each person configures their **own** credentials in Cursor (no credentials go in the repo).

---

## How it works

- **You share:** This repo (e.g. via Git: GitHub, Azure DevOps, or internal server).  
- **You do not share:** `.env` files or Cursor MCP config with real credentials.  
- **Each colleague:** Clones the repo, installs once, then adds their own Superset auth in Cursor.

---

## Quick setup (each person does this once)

### 1. Get the code

Clone or download the repo to a folder on your machine, e.g.:

```bash
git clone <your-repo-url> superset_agent
cd superset_agent
```

Or unzip a shared copy into a folder and `cd` into it.

### 2. Install the package

From the **project root** (the folder that contains `pyproject.toml` and `mcp_superset`):

**Windows (PowerShell):**
```powershell
cd C:\path\to\superset_agent
pip install -e .
```

**macOS / Linux:**
```bash
cd /path/to/superset_agent
pip install -e .
```

You should see `Successfully installed mcp-superset-0.1.0`. Use a virtual environment if your team prefers (e.g. `python -m venv .venv` then activate, then `pip install -e .`).

### 3. Get your Superset credentials

Each person must use **their own** login (e.g. their own Google account or username/password).

- **Session cookie (typical with Google login):** See **[GET_TOKEN.md](GET_TOKEN.md)** — log in to Superset in the browser, then copy the `session` cookie value.
- **Username + password:** If your Superset admin gave you an API user, use that.

Do **not** commit `.env` or put real credentials in the repo.

### 4. Add the Superset MCP server in Cursor

Each person adds the server **on their own machine**, with **their own** path and credentials.

1. Open **Cursor** → **Settings** (gear or `Ctrl+,`) → **Features** → **MCP**.
2. Click **Edit in settings.json** (or add a new MCP server via the UI).
3. Add the `superset` block inside `mcpServers`. Use **your** clone path and **your** credentials:

```json
"superset": {
  "command": "python",
  "args": ["-m", "mcp_superset.server"],
  "cwd": "C:\\path\\to\\superset_agent",
  "env": {
    "SUPERSET_URL": "https://your-superset-instance.com",
    "SUPERSET_SESSION_COOKIE": "session=YOUR_SESSION_VALUE"
  }
}
```

- Replace `C:\\path\\to\\superset_agent` with the **actual path** where you cloned the repo (on Windows use double backslashes `\\`).
- Replace `https://your-superset-instance.com` with your Superset URL (e.g. `https://dashboards.bioptimizers.net`).
- Replace `YOUR_SESSION_VALUE` with the cookie value you got from [GET_TOKEN.md](GET_TOKEN.md). If you use username/password instead, use `SUPERSET_USERNAME` and `SUPERSET_PASSWORD` and omit `SUPERSET_SESSION_COOKIE`.

4. Save the file and **reload MCP** (or restart Cursor).

### 5. Test

In a Cursor chat, ask: *"List my Superset dashboards."* The AI should use the Superset MCP tools. If you get auth errors, get a fresh session cookie (see GET_TOKEN.md) and update the `env` in your MCP config.

---

## Checklist for each colleague

- [ ] Cloned / downloaded the repo
- [ ] Ran `pip install -e .` from the project root
- [ ] Got my own Superset auth (cookie or username/password) — see GET_TOKEN.md
- [ ] Added the `superset` MCP server in Cursor with **my** path and **my** credentials
- [ ] Reloaded MCP and tested (e.g. "List my Superset dashboards")

---

## If your team uses a shared Superset URL

You can share **only the URL** in the repo (e.g. in this doc or in `.env.example`). Keep the URL in the example MCP block as a default; each person still sets their **own** `SUPERSET_SESSION_COOKIE` (or username/password) in their local Cursor config.

---

## Optional: test from the command line

To verify credentials without Cursor:

```powershell
# Windows PowerShell
cd C:\path\to\superset_agent
$env:SUPERSET_URL="https://your-superset-instance.com"
$env:SUPERSET_SESSION_COOKIE="session=YOUR_SESSION_VALUE"
python test_superset_connection.py
```

If connection is OK, you'll see databases and dashboards listed. Then use the same URL and cookie in Cursor MCP.
