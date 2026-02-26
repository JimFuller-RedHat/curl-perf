"""Tool adapter registry."""

from curl_perf.tools.base import ToolAdapter
from curl_perf.tools.curl import CurlAdapter
from curl_perf.tools.httpie import HTTPieAdapter
from curl_perf.tools.py_requests import PyRequestsAdapter
from curl_perf.tools.wget import WgetAdapter
from curl_perf.tools.xh import XhAdapter

ALL_ADAPTERS: list[type[ToolAdapter]] = [
    CurlAdapter, HTTPieAdapter, PyRequestsAdapter, WgetAdapter, XhAdapter,
]


def get_available_tools() -> list[ToolAdapter]:
    return [cls() for cls in ALL_ADAPTERS if cls().is_available()]


def get_tool(name: str) -> ToolAdapter | None:
    for cls in ALL_ADAPTERS:
        adapter = cls()
        if adapter.name == name:
            return adapter
    return None
