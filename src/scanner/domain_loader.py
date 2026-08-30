"""
Module for loading domain names from a text file.
"""

import re
from pathlib import Path
from src.scanner.utils.logger import get_logger

logger = get_logger(__name__)

# Simple regex for domain validation (not exhaustive, but practical)
DOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


def load_domains(path: str | Path = "config/domains.txt") -> list[str]:
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
            raw_lines = [line.strip() for line in file]
            logger.debug("Raw lines read from %s: %s", file_path, raw_lines)

            # Non-empty domains after stripping whitespace
            domains = [line for line in raw_lines if line]
            logger.debug("Non-empty domains after stripping whitespace: %s", domains)

            # Validate domains using regex
            valid_domains = [domain for domain in domains if DOMAIN_REGEX.match(domain)]
            invalid_domains = [
                domain for domain in domains if not DOMAIN_REGEX.match(domain)
            ]

            if invalid_domains:
                logger.debug("Invalid domains found and ignored: %s", invalid_domains)

            if not valid_domains:
                logger.warning("No valid domains found in %s.", file_path)
            else:
                logger.info(
                    "Loaded %s valid domains from %s.",
                    len(valid_domains),
                    file_path,
                )

            return valid_domains

    except FileNotFoundError:
        logger.warning(
            "Domain list file not found: %s. Returning empty list.", file_path
        )
        return []


if __name__ == "__main__":
    # Example usage
    returned_domains = load_domains("config/domains.txt")
    print(f"Loaded domains: {returned_domains}")
