"""Application service for coordinating TLS evidence collection."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from pqc_inventory.collection.models import TLSScanResult
from pqc_inventory.collection.tls_scanner import scan_target

# A scanner accepts one target and returns its structured scan evidence.
Scanner = Callable[..., TLSScanResult]


class ScanService:
    """Coordinate TLS scans without implementing collection logic."""

    def __init__(self, scanner: Scanner | None = None) -> None:
        self._scanner = scanner if scanner is not None else scan_target

    def scan_one(
        self,
        target: str,
        port: int = 443,
        timeout: float = 5.0,
    ) -> TLSScanResult:
        """Collect TLS evidence from one target."""
        return self._scanner(
            target,
            port=port,
            timeout=timeout,
        )

    def scan_many(
        self,
        targets: Iterable[str],
        port: int = 443,
        timeout: float = 5.0,
    ) -> list[TLSScanResult]:
        """Collect TLS evidence from multiple targets in input order."""
        if isinstance(targets, str):
            raise TypeError("targets must be an iterable of target strings.")

        target_list = list(targets)

        if not target_list:
            raise ValueError("At least one target must be provided.")

        return [
            self.scan_one(
                target,
                port=port,
                timeout=timeout,
            )
            for target in target_list
        ]
