"""
TLS Results Printer

Provides summary and verbose printing functions for saved TLS results.
"""

from prettytable import PrettyTable
from src.scanner.models import TLSScanResult


def print_results_table(results: list[TLSScanResult]) -> None:
    """
    PrettyTable summary output for TLS scan results.
    Parameters
    ----------
    results : list[TLSScanResult]
        List of TLS scan results to print.
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

    for item in results:
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


def print_results_verbose(results: list[TLSScanResult]) -> None:
    """
    Print verbose output for TLS scan results.

    Parameters
    ----------
    results : list[TLSScanResult]
        List of TLS scan results to print.
    """
    for item in results:
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
