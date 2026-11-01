"""Shared utilities for CLI commands."""

import sys
import argparse
from pathlib import Path


def valid_port(value: str) -> int:
    """Validate and return a TCP port number."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")

    return port


def validate_output_path(output_path: str | Path) -> Path:
    """Validate and normalize a JSON output path.

    Checks that the destination has a JSON file extension, that an
    existing destination is a regular file, and that an existing
    parent path is a directory.

    Args:
        output_path: The proposed destination for the JSON output file.

    Returns:
        The validated output path with the user's home directory expanded.

    Raises:
        ValueError: If the extension is invalid, the destination exists
            but is not a regular file, or the parent path is not a directory.
    """
    path = Path(output_path).expanduser()

    if path.suffix.lower() != ".json":
        raise ValueError("Output file must have a .json extension.")

    if path.exists() and not path.is_file():
        raise ValueError(f"Output path exists but is not a regular file: {path}")

    if path.parent.exists() and not path.parent.is_dir():
        raise ValueError(f"Output directory is not a directory: {path.parent}")

    return path


def resolve_output_path(output_path: str | Path) -> Path | None:
    """Resolve the evidence destination and prevent accidental overwrites.

    Validates the proposed destination and interacts with the user when
    the path is invalid or the output file already exists. The user may
    approve overwriting an existing file, choose another destination,
    or cancel the operation.

    Args:
        output_path: The proposed destination for the evidence JSON file.

    Returns:
        The approved output path, or None if the user cancels the operation.

    Raises:
        EOFError: If standard input closes while awaiting user input.
        KeyboardInterrupt: If the user interrupts the operation.
    """
    while True:
        try:
            path = validate_output_path(output_path)
        except ValueError as exc:
            print(f"Invalid output path: {exc}", file=sys.stderr)

            output_path = input(
                "Enter a valid JSON output path, or press Enter to cancel: "
            ).strip()

            if not output_path:
                return None

            continue

        if not path.exists():
            return path

        print(f"\nOutput file already exists: {path}")
        print("1. Overwrite existing file")
        print("2. Choose another path")
        print("3. Cancel")

        choice = input("Choose an option [1-3]: ").strip()

        if choice == "1":
            confirmation = (
                input(f"Confirm overwrite of '{path}'? [y/N]: ").strip().lower()
            )

            if confirmation == "y":
                return path

            print("Overwrite not confirmed. No file was changed.")

        elif choice == "2":
            new_path = input("Enter the new output path: ").strip()

            if not new_path:
                return None

            output_path = new_path

        elif choice == "3":
            print("Scan cancelled.")
            return None

        else:
            print("Invalid choice. Enter 1, 2, or 3.")
