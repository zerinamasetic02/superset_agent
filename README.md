# Superset MCP Server

MCP server that exposes **Apache Superset** as tools so the AI can build dashboards from Cursor: create dashboards, add charts from datasets (e.g. Snowflake views), and set filters from your instructions.

## Sharing with your team

**Best approach:** Share only the **code** (this repo via Git or a shared folder). Each colleague does a one-time setup on their machine with **their own** Superset credentials. No credentials are stored in the repo.

- **You share:** The repo (e.g. `git clone` or internal Git server).
- **You do not share:** `.env` files or Cursor MCP config containing real cookies/tokens/passwords.
- **Each person:** Follows **[TEAM_SETUP.md](TEAM_SETUP.md)** once: clone → `pip install -e .` → get their own auth (see [GET_TOKEN.md](GET_TOKEN.md)) → add Superset MCP in Cursor with their path and credentials → reload MCP.

The repo includes a [.gitignore](.gitignore) so `.env` and other secrets are not committed.

## Prerequisites

- Python 3.10+
- A running **Superset** instance with API enabled
- In Superset: at least one **database** (e.g. Snowflake) and **datasets** (tables/views) that you want to use in dashboards

## Setup

### 1. Install dependencies

From the directory that contains `mcp_superset` (the folder can live anywhere):

```bash
cd <path-to-mcp_superset>
pip install -e .
# or with uv:
uv pip install -e .
```

### 2. Environment variables

Use **one** of: (A) session cookie, (B) access token, or (C) username/password. Set in Cursor MCP config or your shell:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPERSET_URL` | Yes | Base URL of Superset (e.g. `https://superset.yourcompany.com`) |
| **Option A – Session cookie (browser / Google login, no JWT)** | | |
| `SUPERSET_SESSION_COOKIE` | Yes* | Cookie string, e.g. `session=<value>`. Get from DevTools -> Application -> Cookies -> your Superset URL -> copy `session` value. See GET_TOKEN.md. |
| **Option B – Access token** | | |
| `SUPERSET_ACCESS_TOKEN` | Yes* | JWT from browser. Optional: `SUPERSET_REFRESH_TOKEN`. |
| **Option C – Username/password** | | |
| `SUPERSET_USERNAME` | Yes | API user (e.g. `admin`) |
| `SUPERSET_PASSWORD` | Yes | Password for that user |
| `SUPERSET_AUTH_PROVIDER` | No | Auth provider; default `db` |

**Session cookie (when you only have cookie, no Authorization header):**  
See **GET_TOKEN.md**: log in to Superset, F12 -> Application -> Cookies -> your Superset URL -> copy the `session` cookie value, then set `SUPERSET_SESSION_COOKIE=session=<paste value>`. Session expires when you close the browser or after some time; get a fresh cookie when you get 401s.

**Do not commit credentials.** Use Cursor’s MCP env or a local `.env` that is gitignored.

### 3. Add the server in Cursor

1. Open **Cursor Settings → Features → MCP**.
2. Click **Add new MCP server**.
3. Choose **Run a script / command** (stdio).
4. Configure:

**Option A – Use your Python (recommended)**

- **Command:**  
  `python` (or the full path to your Python / venv, e.g. `<path-to-mcp_superset>\.venv\Scripts\python.exe`)
- **Arguments:**  
  `-m mcp_superset.server`
- **Working directory:**  
  Full path to the **mcp_superset** folder (e.g. `c:\Bio\cursor_projects\mcp_superset`)
- **Env (add here or in Cursor MCP env):**  
  `SUPERSET_URL`, `SUPERSET_USERNAME`, `SUPERSET_PASSWORD`

**Option B – Global install**

If you installed the package globally:

- **Command:**  
  `mcp-server-superset`
- **Env:** same as above.

**Option C – JSON config (Cursor MCP)**

If your Cursor MCP is configured via JSON, add something like:

```json
{
  "mcpServers": {
    "superset": {
      "command": "python",
      "args": ["-m", "mcp_superset.server"],
      "cwd": "C:\\path\\to\\mcp_superset",
      "env": {
        "SUPERSET_URL": "https://superset.yourcompany.com",
        "SUPERSET_USERNAME": "your_user",
        "SUPERSET_PASSWORD": "your_password"
      }
    }
  }
}
```
Replace `C:\\path\\to\\mcp_superset` with the actual path where you placed the folder.

Restart Cursor or reload MCP after adding the server.

## Tools exposed to the AI

| Tool | Purpose |
|------|--------|
| `superset_list_databases` | List Superset databases (e.g. Snowflake connection) |
| `superset_list_datasets` | List datasets; optional `database_id`, `search` |
| `superset_get_dataset` | Get dataset by id (columns, metrics) for building charts |
| `superset_list_dashboards` | List dashboards; optional `search` |
| `superset_get_dashboard` | Get dashboard by id or slug (layout, metadata, filters) |
| `superset_create_dashboard` | Create empty dashboard; then add charts and filters |
| `superset_update_dashboard` | Update dashboard (title, slug, published) |
| `superset_delete_dashboard` | Delete a dashboard by id |
| `superset_update_dashboard_filters` | Set native filters (JSON array of filter config) |
| `superset_add_chart_to_dashboard` | Add chart to dashboard with position (x, y, width, height) |
| `superset_list_charts` | List charts; optional `search` |
| `superset_get_chart` | Get chart by id |
| `superset_create_chart` | Create chart (dataset_id, viz_type, slice_name, params JSON) |
| `superset_update_chart` | Update chart (slice_name, params, description) |
| `superset_delete_chart` | Delete a chart by id |
| `superset_get_dashboard_charts` | List charts on a dashboard |

## Workflow: Snowflake views → Superset dashboard

1. **You** tell the AI what you want: e.g. “Dashboard for view X, filter by date and region, bar chart and table.”
2. **AI** uses **Snowflake MCP** to inspect views/tables (e.g. `list_objects`, `run_snowflake_query`).
3. **AI** uses **Superset MCP** to:
   - `superset_list_datasets` to find the dataset that points at that view
   - `superset_get_dataset` to see columns
   - `superset_create_dashboard` and then `superset_create_chart` for each chart
   - `superset_add_chart_to_dashboard` to place them
   - `superset_update_dashboard_filters` to add the filters you asked for
4. You open the dashboard in Superset and refine if needed.

## Native filters (dashboard filters)

`superset_update_dashboard_filters` takes a JSON **string** that is an array of filter objects. Each object typically has:

- `id`: unique string id for the filter
- `name`: label shown in the UI
- `filterType`: e.g. `filter_select`, `filter_time`, `filter_timegrain`
- `targets`: which charts/columns the filter applies to
- `defaultDataMask`: default value
- `scope`: scope of the filter

The AI can build this from your instructions (e.g. “add a date range and a region dropdown”) by following [Superset’s native filter schema](https://superset.apache.org/developer-docs/api/update-native-filters-configuration-for-a-dashboard).

## Chart params

For `superset_create_chart`, `params` is a JSON **string** object. Contents depend on `viz_type`, for example:

- **table:** `metrics`, `groupby`, `order_desc`, `row_limit`, etc.
- **big_number:** `metric`, `compare_lag`, etc.
- **line / bar:** `metrics`, `groupby`, `time_range`, `order_desc`, etc.

The AI should use `superset_get_dataset` to see available columns/metrics and build valid `params`.

## Run the server locally (optional)

```bash
cd mcp_superset
set SUPERSET_URL=https://...
set SUPERSET_USERNAME=admin
set SUPERSET_PASSWORD=...
python -m mcp_superset.server
```

The server uses stdio; Cursor will start it automatically when the tools are used.
