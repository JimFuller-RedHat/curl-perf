"""Abstract base class for tool adapters."""

from abc import ABC, abstractmethod
from curl_perf.results import TimingResult


class ToolAdapter(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is installed and accessible."""

    @abstractmethod
    def supports_http2(self) -> bool:
        """Check if the tool supports HTTP/2."""

    @abstractmethod
    def run(self, url: str, http_version: str = "2") -> TimingResult:
        """Run a single request and return timing data."""

    @abstractmethod
    def run_concurrent(self, urls: list[str], http_version: str = "2") -> TimingResult:
        """Run concurrent requests and return aggregate timing data."""
