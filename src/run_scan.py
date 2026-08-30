"""
Run Scan Orchestrator
Connects domain loader + TLS scanner

This module orchestrates the TLS scanning process. It loads domains
from a configuration file, executes TLS scans for each domain, and
saves the results to JSON for downstream PQC scoring and reporting.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from src.scanner.utils.logger import get_logger
from src.scanner.domain_loader import load_domains
from src.scanner.tls_scanner import scan_domain
from src.scanner.models import TLSScanResult
from src.scanner.json_io import save_tls_results

logger = get_logger(__name__)


def run_scan(domains_path: str | Path = "config/domains.txt") -> list[TLSScanResult]:
    """
    Load domains and run TLS scans on each one.
    """
    logger.info("Starting TLS scan orchestrator using domain file: %s", domains_path)

    domains = load_domains(domains_path)
    logger.info("Loaded %d domains for scanning.", len(domains))
    logger.debug("Domains to scan: %s", domains)

    scanned_domains_results: list[TLSScanResult] = []

    for domain in domains:
        start_time = time.perf_counter()

        logger.info("Scanning domain: %s", domain)
        scan_result = scan_domain(domain)

        elapsed_time = time.perf_counter() - start_time
        scan_result["scan_duration"] = round(elapsed_time, 2)

        scanned_domains_results.append(scan_result)

        if "error" in scan_result:
            logger.warning("Scan error for domain %s: %s", domain, scan_result["error"])
        else:
            logger.info(
                "Scan successful for domain %s: TLS Version: %s, Cipher Suite: %s",
                domain,
                scan_result.get("tls_version"),
                scan_result.get("cipher_suite"),
            )

        logger.debug("Scan result for domain %s: %s", domain, scan_result)

    logger.info("Completed TLS scans for %d domains.", len(scanned_domains_results))
    return scanned_domains_results


def main() -> None:
    """
    CLI entrypoint for TLS scanning.
    Loads domains, runs scans, and saves results to JSON.

    This module is invoked by the pipeline as:
        python -m src.run_scan --domains config/domains.txt
    """
    parser = argparse.ArgumentParser(description="TLS Scanner")
    parser.add_argument(
        "--domains",
        default="config/domains.txt",
        help="Path to the domain list file",
    )
    args = parser.parse_args()

    tls_scan_results = run_scan(args.domains)
    save_tls_results(tls_scan_results)

    logger.info("Saved TLS results to data/processed/tls_results.json")


if __name__ == "__main__":
    main()
