"""
Superset MCP server. Exposes tools for listing/creating dashboards, charts, datasets,
and updating dashboard filters. Configure via environment variables.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import FastMCP

from mcp_superset.client import SupersetClient
from mcp_superset.tools import register_tools


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name, default)
    return v.strip() if v else None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[SupersetClient]:
    base_url = _env("SUPERSET_URL")
    if not base_url:
        raise RuntimeError("Superset MCP requires SUPERSET_URL.")
    access_token = _env("SUPERSET_ACCESS_TOKEN")
    refresh_token = _env("SUPERSET_REFRESH_TOKEN")
    session_cookie = _env("SUPERSET_SESSION_COOKIE")
    username = _env("SUPERSET_USERNAME")
    password = _env("SUPERSET_PASSWORD")
    if session_cookie:
        client = SupersetClient(
            base_url=base_url,
            session_cookie=session_cookie,
        )
    elif access_token:
        client = SupersetClient(
            base_url=base_url,
            username=username,
            password=password,
            provider=_env("SUPERSET_AUTH_PROVIDER") or "db",
            access_token=access_token,
            refresh_token=refresh_token,
        )
    elif username and password:
        client = SupersetClient(
            base_url=base_url,
            username=username,
            password=password,
            provider=_env("SUPERSET_AUTH_PROVIDER") or "db",
        )
    else:
        raise RuntimeError(
            "Set SUPERSET_SESSION_COOKIE (cookie from browser), "
            "SUPERSET_ACCESS_TOKEN, or both SUPERSET_USERNAME and SUPERSET_PASSWORD."
        )
    register_tools(server, client)
    yield client


def main() -> None:
    mcp = FastMCP(
        "Superset MCP Server",
        lifespan=lifespan,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
