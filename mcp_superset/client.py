"""
Superset REST API client. Handles JWT login and provides typed access to
dashboard, chart, and dataset endpoints.
"""
from __future__ import annotations

from typing import Any

import httpx


def _rison_dumps(obj: dict[str, Any]) -> str:
    """Minimal RISON encoder for simple dicts (e.g. pagination). Format: (k:v,k2:v2)."""
    parts = []
    for k, v in obj.items():
        if isinstance(v, bool):
            parts.append(f"{k}:!{'t' if v else 'f'}")
        elif isinstance(v, (int, float)):
            parts.append(f"{k}:{v}")
        elif isinstance(v, str):
            # Escape quotes and backslashes
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{k}:"{escaped}"')
        else:
            parts.append(f"{k}:{v}")
    return "(" + ",".join(parts) + ")"

# Default timeout for API calls
DEFAULT_TIMEOUT = 60.0


class SupersetAPIError(Exception):
    """Raised when a Superset API request fails."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class SupersetClient:
    """
    Client for Apache Superset REST API (v1).
    Supports (1) session cookie (browser login, e.g. Google OAuth), (2) access token,
    or (3) username/password login. Optionally uses refresh token when using access token.
    """

    def __init__(
        self,
        base_url: str,
        username: str | None = None,
        password: str | None = None,
        provider: str = "db",
        access_token: str | None = None,
        refresh_token: str | None = None,
        session_cookie: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.provider = provider
        self.timeout = timeout
        self._access_token: str | None = access_token
        self._refresh_token: str | None = refresh_token or None
        self._session_cookie: str | None = (session_cookie or "").strip() or None
        if not self._access_token and not self._session_cookie and not (username and password):
            raise ValueError(
                "Provide session_cookie, access_token, or both username and password."
            )

    def _uses_cookie(self) -> bool:
        return bool(self._session_cookie)

    def _headers(self) -> dict[str, str]:
        if self._session_cookie:
            return {
                "Cookie": self._session_cookie,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        if not self._access_token:
            self._obtain_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _obtain_token(self) -> None:
        """Get access token via refresh (if we have refresh_token) or login."""
        if self._refresh_token:
            try:
                self._refresh()
                return
            except SupersetAPIError:
                pass
        if self.username and self.password:
            self.login()
            return
        raise SupersetAPIError(
            "No valid token and no username/password. "
            "Set SUPERSET_ACCESS_TOKEN (e.g. from browser after Google login) or SUPERSET_USERNAME + SUPERSET_PASSWORD."
        )

    def login(self) -> None:
        """Obtain JWT access token via /api/v1/security/login."""
        if not self.username or not self.password:
            raise SupersetAPIError("Login requires SUPERSET_USERNAME and SUPERSET_PASSWORD")
        url = f"{self.base_url}/api/v1/security/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "provider": self.provider,
        }
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, json=payload)
        if r.status_code != 200:
            raise SupersetAPIError(
                f"Login failed: {r.text}",
                status_code=r.status_code,
                body=r.text,
            )
        data = r.json()
        self._access_token = data.get("access_token")
        self._refresh_token = data.get("refresh_token") or self._refresh_token
        if not self._access_token:
            raise SupersetAPIError("Login response missing access_token")

    def _refresh(self) -> None:
        """Refresh access token using refresh_token."""
        if not self._refresh_token:
            raise SupersetAPIError("No refresh token available")
        url = f"{self.base_url}/api/v1/security/refresh"
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, json={"refresh_token": self._refresh_token})
        if r.status_code != 200:
            raise SupersetAPIError(
                f"Refresh failed: {r.text}",
                status_code=r.status_code,
                body=r.text,
            )
        data = r.json()
        self._access_token = data.get("access_token")
        if not self._access_token:
            raise SupersetAPIError("Refresh response missing access_token")

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            r = client.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
            )
        if r.status_code in (401, 403) and not self._uses_cookie():
            self._obtain_token()
            with httpx.Client(timeout=self.timeout) as client:
                r = client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                    params=params,
                )
        if r.status_code >= 400:
            raise SupersetAPIError(
                f"Request failed: {r.text}",
                status_code=r.status_code,
                body=r.text,
            )
        if not r.content:
            return {}
        return r.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any]) -> dict[str, Any] | list[Any]:
        return self._request("POST", path, json=json)

    def put(self, path: str, json: dict[str, Any]) -> dict[str, Any] | list[Any]:
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> dict[str, Any] | list[Any]:
        return self._request("DELETE", path)

    # --- Databases ---
    def list_databases(self) -> list[dict[str, Any]]:
        data = self.get("/api/v1/database/")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, list) else []

    # --- Datasets ---
    def list_datasets(
        self,
        database_id: int | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if q:
            params["q"] = {"search": q}
        if database_id is not None:
            params.setdefault("q", {})["filters"] = [
                {"col": "database_id", "opr": "eq", "value": database_id}
            ]
        data = self.get("/api/v1/dataset/", params=params if params else None)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, list) else []

    def list_all_datasets(self, page_size: int = 100) -> list[dict[str, Any]]:
        """List all datasets across all pages using RISON-encoded pagination."""
        all_results: list[dict[str, Any]] = []
        page = 0
        while True:
            q_obj: dict[str, Any] = {"page": page, "page_size": page_size}
            params = {"q": _rison_dumps(q_obj)}
            data = self.get("/api/v1/dataset/", params=params)
            if isinstance(data, dict) and "result" in data:
                result = data["result"]
            elif isinstance(data, list):
                result = data
            else:
                break
            if not result:
                break
            all_results.extend(result)
            if len(result) < page_size:
                break
            page += 1
        return all_results

    def get_dataset(self, dataset_id: int) -> dict[str, Any]:
        data = self.get(f"/api/v1/dataset/{dataset_id}")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    # --- Dashboards ---
    def list_dashboards(self, q: str | None = None) -> list[dict[str, Any]]:
        params = {}
        if q:
            params["q"] = {"search": q}
        data = self.get("/api/v1/dashboard/", params=params if params else None)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, list) else []

    def get_dashboard(self, id_or_slug: int | str) -> dict[str, Any]:
        data = self.get(f"/api/v1/dashboard/{id_or_slug}")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def create_dashboard(
        self,
        dashboard_title: str,
        slug: str | None = None,
        json_metadata: dict[str, Any] | None = None,
        position_json: dict[str, Any] | None = None,
        published: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "dashboard_title": dashboard_title,
            "published": published,
        }
        if slug:
            payload["slug"] = slug
        if json_metadata is not None:
            payload["json_metadata"] = json_metadata
        if position_json is not None:
            payload["position_json"] = position_json
        data = self.post("/api/v1/dashboard/", json=payload)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def update_dashboard(
        self,
        pk: int,
        dashboard_title: str | None = None,
        slug: str | None = None,
        json_metadata: dict[str, Any] | None = None,
        position_json: dict[str, Any] | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if dashboard_title is not None:
            payload["dashboard_title"] = dashboard_title
        if slug is not None:
            payload["slug"] = slug
        if json_metadata is not None:
            payload["json_metadata"] = json_metadata
        if position_json is not None:
            payload["position_json"] = position_json
        if published is not None:
            payload["published"] = published
        data = self.put(f"/api/v1/dashboard/{pk}", json=payload)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def delete_dashboard(self, pk: int) -> dict[str, Any]:
        """Delete a dashboard by id."""
        data = self.delete(f"/api/v1/dashboard/{pk}")
        return data if isinstance(data, dict) else {"message": "deleted"}

    def update_dashboard_filters(
        self,
        pk: int,
        native_filter_configuration: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Update native (dashboard-level) filters. Replaces existing filter config."""
        data = self.put(
            f"/api/v1/dashboard/{pk}/filters",
            json={"native_filter_configuration": native_filter_configuration},
        )
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def get_dashboard_charts(self, id_or_slug: int | str) -> list[dict[str, Any]]:
        data = self.get(f"/api/v1/dashboard/{id_or_slug}/charts")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, list) else []

    def add_chart_to_dashboard(
        self,
        dashboard_pk: int,
        chart_id: int,
        width: int = 4,
        height: int = 50,
        x: int = 0,
        y: int = 0,
    ) -> dict[str, Any]:
        """
        Add a chart to a dashboard by updating position_json.
        Fetches the chart to get its uuid; Superset uses 'CHART-<uuid>' as the key.
        """
        chart = self.get_chart(chart_id)
        chart_uuid = chart.get("uuid") or str(chart_id)
        dash = self.get_dashboard(dashboard_pk)
        position_json = dash.get("position_json") or {}
        if not isinstance(position_json, dict):
            position_json = {}
        chart_key = f"CHART-{chart_uuid}" if not str(chart_uuid).startswith("CHART-") else str(chart_uuid)
        position_json[chart_key] = {
            "id": chart_id,
            "type": "CHART",
            "meta": {"chartId": chart_id, "uuid": str(chart_uuid)},
            "width": width,
            "height": height,
            "x": x,
            "y": y,
        }
        return self.update_dashboard(
            dashboard_pk,
            position_json=position_json,
        )

    # --- Charts ---
    def list_charts(self, q: str | None = None) -> list[dict[str, Any]]:
        params = {}
        if q:
            params["q"] = {"search": q}
        data = self.get("/api/v1/chart/", params=params if params else None)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, list) else []

    def get_chart(self, pk: int) -> dict[str, Any]:
        data = self.get(f"/api/v1/chart/{pk}")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def create_chart(
        self,
        dataset_id: int,
        viz_type: str,
        slice_name: str,
        params: dict[str, Any],
        description: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "datasource_id": dataset_id,
            "datasource_type": "dataset",
            "viz_type": viz_type,
            "slice_name": slice_name,
            "params": params,
        }
        if description:
            payload["description"] = description
        data = self.post("/api/v1/chart/", json=payload)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def update_chart(
        self,
        pk: int,
        slice_name: str | None = None,
        params: dict[str, Any] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if slice_name is not None:
            payload["slice_name"] = slice_name
        if params is not None:
            payload["params"] = params
        if description is not None:
            payload["description"] = description
        data = self.put(f"/api/v1/chart/{pk}", json=payload)
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data if isinstance(data, dict) else {}

    def delete_chart(self, pk: int) -> dict[str, Any]:
        """Delete a chart by id."""
        data = self.delete(f"/api/v1/chart/{pk}")
        return data if isinstance(data, dict) else {"message": "deleted"}
