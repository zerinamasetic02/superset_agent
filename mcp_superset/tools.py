"""
MCP tools for Superset: dashboards, charts, datasets, filters.
The AI uses these to build dashboards from user instructions (e.g. Snowflake views + filters).
"""
from __future__ import annotations

import json
from typing import Any

from mcp_superset.client import SupersetClient


def _result(msg: str, data: Any = None) -> str:
    out = msg
    if data is not None:
        out += "\n\n" + json.dumps(data, indent=2, default=str)
    return out


def register_tools(server, client: SupersetClient):
    """Register all Superset MCP tools on the given FastMCP server."""

    @server.tool()
    def superset_list_databases() -> str:
        """List all databases configured in Superset (e.g. Snowflake). Use to find database_id for listing datasets."""
        try:
            result = client.list_databases()
            return _result("Databases:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_list_datasets(database_id: int | None = None, search: str | None = None) -> str:
        """List datasets (tables/views) in Superset. Optionally filter by database_id or search by name. Use to find dataset_id for creating charts."""
        try:
            result = client.list_datasets(database_id=database_id, q=search)
            return _result("Datasets:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_list_all_datasets(page_size: int = 100) -> str:
        """List all datasets in Superset across all pages. Use when you need the full list (e.g. to find a dataset by name like vw_bioverse_performance_report)."""
        try:
            result = client.list_all_datasets(page_size=page_size)
            return _result(f"Datasets (total {len(result)}):", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_get_dataset(dataset_id: int) -> str:
        """Get a dataset by id, including columns and metrics. Use to see available columns before creating charts."""
        try:
            result = client.get_dataset(dataset_id)
            return _result("Dataset:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_list_dashboards(search: str | None = None) -> str:
        """List dashboards. Optionally search by title."""
        try:
            result = client.list_dashboards(q=search)
            return _result("Dashboards:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_get_dashboard(id_or_slug: str) -> str:
        """Get a dashboard by id or slug. Returns full detail including position_json and json_metadata (filters)."""
        try:
            pid = int(id_or_slug) if id_or_slug.isdigit() else id_or_slug
            result = client.get_dashboard(pid)
            return _result("Dashboard:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_create_dashboard(
        dashboard_title: str,
        slug: str | None = None,
        published: bool = False,
    ) -> str:
        """Create a new empty dashboard. Returns the new dashboard with id. Then add charts and filters."""
        try:
            result = client.create_dashboard(
                dashboard_title=dashboard_title,
                slug=slug,
                published=published,
            )
            return _result("Dashboard created:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_update_dashboard(
        dashboard_id: int,
        dashboard_title: str | None = None,
        slug: str | None = None,
        published: bool | None = None,
    ) -> str:
        """Update an existing dashboard. Pass only the fields you want to change (e.g. title, slug, published)."""
        try:
            result = client.update_dashboard(
                pk=dashboard_id,
                dashboard_title=dashboard_title,
                slug=slug,
                published=published,
            )
            return _result("Dashboard updated:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_delete_dashboard(dashboard_id: int) -> str:
        """Delete a dashboard by id. This does not delete the charts on it; they remain in Superset."""
        try:
            result = client.delete_dashboard(dashboard_id)
            return _result("Dashboard deleted.", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_update_dashboard_filters(
        dashboard_id: int,
        native_filter_configuration: str,
    ) -> str:
        """Update native (dashboard-level) filters. Pass native_filter_configuration as a JSON string: list of filter objects with id, name, filterType, targets, defaultDataMask, scope, etc. Replaces all existing native filters."""
        try:
            config = json.loads(native_filter_configuration)
            if not isinstance(config, list):
                return "Error: native_filter_configuration must be a JSON array of filter objects."
            result = client.update_dashboard_filters(dashboard_id, config)
            return _result("Filters updated:", result)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_add_chart_to_dashboard(
        dashboard_id: int,
        chart_id: int,
        width: int = 4,
        height: int = 50,
        x: int = 0,
        y: int = 0,
    ) -> str:
        """Add an existing chart to a dashboard at the given grid position (x, y, width, height)."""
        try:
            result = client.add_chart_to_dashboard(
                dashboard_pk=dashboard_id,
                chart_id=chart_id,
                width=width,
                height=height,
                x=x,
                y=y,
            )
            return _result("Chart added to dashboard:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_list_charts(search: str | None = None) -> str:
        """List charts. Optionally search by name."""
        try:
            result = client.list_charts(q=search)
            return _result("Charts:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_get_chart(chart_id: int) -> str:
        """Get a chart by id. Returns viz_type, params, datasource, etc."""
        try:
            result = client.get_chart(chart_id)
            return _result("Chart:", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_create_chart(
        dataset_id: int,
        viz_type: str,
        slice_name: str,
        params: str,
        description: str | None = None,
    ) -> str:
        """Create a new chart. params must be a JSON string: object with keys like metrics, groupby, order_desc, row_limit, time_range, etc. depending on viz_type (e.g. table, big_number, line, bar, pie)."""
        try:
            params_obj = json.loads(params)
            if not isinstance(params_obj, dict):
                return "Error: params must be a JSON object."
            result = client.create_chart(
                dataset_id=dataset_id,
                viz_type=viz_type,
                slice_name=slice_name,
                params=params_obj,
                description=description,
            )
            return _result("Chart created:", result)
        except json.JSONDecodeError as e:
            return f"Invalid JSON in params: {e}"
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_update_chart(
        chart_id: int,
        slice_name: str | None = None,
        params: str | None = None,
        description: str | None = None,
    ) -> str:
        """Update an existing chart. Pass only the fields you want to change. params must be a JSON string if provided (same shape as for create_chart)."""
        try:
            params_obj = json.loads(params) if params else None
            if params is not None and not isinstance(params_obj, dict):
                return "Error: params must be a JSON object."
            result = client.update_chart(
                pk=chart_id,
                slice_name=slice_name,
                params=params_obj,
                description=description,
            )
            return _result("Chart updated:", result)
        except json.JSONDecodeError as e:
            return f"Invalid JSON in params: {e}"
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_delete_chart(chart_id: int) -> str:
        """Delete a chart by id. Removing it from a dashboard does not delete the chart; use this to delete it from Superset."""
        try:
            result = client.delete_chart(chart_id)
            return _result("Chart deleted.", result)
        except Exception as e:
            return f"Error: {e}"

    @server.tool()
    def superset_get_dashboard_charts(dashboard_id_or_slug: str) -> str:
        """Get all charts that belong to a dashboard."""
        try:
            pid = int(dashboard_id_or_slug) if dashboard_id_or_slug.isdigit() else dashboard_id_or_slug
            result = client.get_dashboard_charts(pid)
            return _result("Dashboard charts:", result)
        except Exception as e:
            return f"Error: {e}"
