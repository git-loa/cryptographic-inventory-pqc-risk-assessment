"""
Module for loading domain names from a text file.
"""

import re
from pathlib import Path

# Simple regex for domain validation (not exhaustive, but practical)
DOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


def load_domain_from_file(path: str | Path = "config/domains.txt") -> list[str]:
    """
    Load domain names from a text file.

    Handles all cases:
    - File does not exist -> returns empty list
    - File exists but is empty -> returns empty list
    - File exists but has only whitespace -> returns empty list
    - File exists with valid domains -> returns list of domains
    - Invalid domains are ignored (not included in the returned list)

    Parameters
    ----------
    path : str | Path
        Path to the domain list file.

    Returns
    -------
    list[str]
        A list of valid domain names.
    """
    file_path = Path(path)

    try:
        with file_path.open("r", encoding="utf-8") as file:
            domains = [line.strip() for line in file if line.strip()]
            return [domain for domain in domains if DOMAIN_REGEX.match(domain)]
    except FileNotFoundError:
        return []


if __name__ == "__main__":
    # Example usage
    returned_domains = load_domain_from_file("config/domains.txt")
    print(f"Loaded domains: {returned_domains}")
