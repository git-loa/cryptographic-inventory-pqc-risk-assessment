"""
Run Scan Orchestrator
Connects domain loader + TLS scanner
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prettytable import PrettyTable

from scanner.domain_loader import load_domains
from scanner.tls_scanner import scan_domain


def run_scan(domains_path: str | Path = "config/domains.txt") -> list[dict[str, Any]]:
    """
    Load domains and run TLS scans on each one.
    """
    domains = load_domains(domains_path)
    scanned_domains_results: list[dict[str, Any]] = []

    for domain in domains:
        scan_result = scan_domain(domain)
        scanned_domains_results.append(scan_result)

    return scanned_domains_results


def print_results_verbose(results_param: list[dict[str, Any]]) -> None:
    """
    Verbose, detailed per-domain output.
    """
    for item in results_param:
        print("-" * 60)
        print(f"Domain: {item['domain']}")
        print(f"Port: {item['port']}")

        if "error" in item:
            print(f"Error: {item['error']}")
            continue

        print(f"TLS Version: {item['tls_version']}")
        print(f"Cipher Suite: {item['cipher_suite']}")
        print(f"Cipher Strength: {item['cipher_strength']}")
        print(f"Key Size: {item['key_size']}")
        print(f"Valid From: {item['not_before']}")
        print(f"Valid Until: {item['not_after']}")
        print(f"Issuer: {item['certificate_issuer']}")
        print(f"Subject: {item['certificate_subject']}")

    print("-" * 60)


def print_results_table(results_param: list[dict[str, Any]]) -> None:
    """
    PrettyTable summary output.
    """
    table = PrettyTable()
    table.field_names = [
        "Domain",
        "TLS Version",
        "Cipher Suite",
        "Key Size",
        "Valid Until",
        "Error",
    ]

    for item in results_param:
        if "error" in item:
            table.add_row(
                [
                    item["domain"],
                    "-",
                    "-",
                    "-",
                    "-",
                    item["error"],
                ]
            )
        else:
            table.add_row(
                [
                    item["domain"],
                    item["tls_version"],
                    item["cipher_suite"],
                    item["key_size"],
                    item["not_after"],
                    "",
                ]
            )

    print(table)


if __name__ == "__main__":
    results_to_print = run_scan()

    print("\n=== SUMMARY TABLE ===\n")
    print_results_table(results_to_print)

    print("\n=== VERBOSE DETAILS ===\n")
    print_results_verbose(results_to_print)
