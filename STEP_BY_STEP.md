# Superset MCP — Step-by-step setup

Do these steps in order. Steps 1–2 are one-time; step 3 is where you add your Superset server in Cursor.

**Moving the agent:** You can place the `mcp_superset` folder anywhere (e.g. a separate repo or `c:\Bio\cursor_projects\mcp_superset`). After moving, run `pip install -e .` from the new folder and set Cursor MCP **CWD** to that path. No code changes needed.

---

## Step 1: Install the Superset MCP package

Open a terminal, go to the **mcp_superset** folder (wherever you placed it), and run:

```powershell
cd <path-to-mcp_superset>
pip install -e .
```

Example: if you moved it to `c:\Bio\cursor_projects\mcp_superset`, run `cd c:\Bio\cursor_projects\mcp_superset` then `pip install -e .`

You should see "Successfully installed mcp-superset-0.1.0". If you use a virtual environment, activate it first, then run the same commands.

---

## Step 2: Have your Superset details ready

You will need:

- **Superset base URL** (e.g. `https://superset.yourcompany.com`)
- **Either:** (A) **Access token** from the browser (if you sign in with Google/OAuth and don’t have a password), or (B) **Username** and **Password** for a Superset user that can use the API.

**If you use Google/OAuth and have no password:** Log in to Superset in your browser, then open DevTools (F12) → Application → Local Storage → your Superset URL. Find the key that holds the JWT (e.g. `access_token` or under `superset`) and copy its value. Use it as `SUPERSET_ACCESS_TOKEN` in Step 3. Tokens expire (often in 1 day); when the MCP fails with auth errors, get a fresh token and update the config.

Superset must be running and the REST API enabled. In Superset you should already have at least one database (e.g. Snowflake) and datasets (tables/views) that you want to use in dashboards.

---

## Step 3: Add the Superset MCP server in Cursor

1. In Cursor, go to **Settings** (gear icon or `Ctrl+,`).
2. Open **Features** → **MCP** (or search for "MCP" in settings).
3. Click **"Add new MCP server"** (or **Edit in settings.json** if you prefer JSON).
4. Add a new server with one of the options below.

### Option A — Using the UI (recommended)

- **Name:** `superset` (or any name you like).
- **Command:** `python`  
  (Or the full path to your Python executable if you use a venv, e.g. `<path-to-mcp_superset>\.venv\Scripts\python.exe`.)
- **Arguments:** `-m mcp_superset.server`
- **CWD / Working directory:** the full path to your **mcp_superset** folder (e.g. `c:\Bio\cursor_projects\mcp_superset` if you moved it there)
- **Environment variables:** add these (replace with your real values):
  - `SUPERSET_URL` = your Superset base URL  
  - **If you have a password:** `SUPERSET_USERNAME` and `SUPERSET_PASSWORD`  
  - **If you use Google/OAuth (no password):** `SUPERSET_ACCESS_TOKEN` = token from browser (see Step 2); optionally `SUPERSET_USERNAME` = your username  

Save. Cursor will start the server when you use the Superset tools.

### Option B — Using JSON config

If you edit MCP config as JSON (e.g. in `~/.cursor/mcp.json` or Cursor’s MCP settings file), add a block like this. Use the path where you placed the folder (e.g. `C:\\Bio\\cursor_projects\\superset_agent`). For Google/OAuth (no password) use `SUPERSET_ACCESS_TOKEN`; otherwise use `SUPERSET_USERNAME` and `SUPERSET_PASSWORD`.

```json
{
  "mcpServers": {
    "superset": {
      "command": "python",
      "args": ["-m", "mcp_superset.server"],
      "cwd": "C:\\Bio\\cursor_projects\\superset_agent",
      "env": {
        "SUPERSET_URL": "https://your-superset-instance.com",
        "SUPERSET_ACCESS_TOKEN": "paste_token_from_browser"
      }
    }
  }
}
```

If you already have other servers (e.g. Snowflake), add only the `"superset": { ... }` block inside `mcpServers`.

---

## Step 4: Restart Cursor or reload MCP

Close and reopen Cursor, or use the option to reload MCP servers so it picks up the new Superset server.

---

## Step 5: Test it

In a Cursor chat, ask the AI to do something that uses Superset, for example:

- “List my Superset databases.”
- “List datasets in Superset and then create a new dashboard called Test Dashboard.”

The AI should use the Superset MCP tools. If you see errors about connection or login, check Step 2 and Step 3 (URL and credentials).

---

## Summary checklist

- [ ] Step 1: Ran `pip install -e .` in `mcp_superset`
- [ ] Step 2: Have Superset URL, username, and password
- [ ] Step 3: Added Superset MCP server in Cursor (UI or JSON) with env vars
- [ ] Step 4: Restarted Cursor or reloaded MCP
- [ ] Step 5: Tested with a simple request (e.g. list databases or create a dashboard)

After this, you can say things like: “Create a Superset dashboard from Snowflake view X with a bar chart and a date filter,” and the AI will use Snowflake MCP to inspect the data and Superset MCP to build the dashboard.
