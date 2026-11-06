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


def validate_output_path(
    *,
    output_path: str | Path,
    allowed_extensions: set[str] | None = None,
) -> Path:
    """Validate and normalize a generic output file path."""

    raw_path = str(output_path)

    if not raw_path or not raw_path.strip():
        raise ValueError("The output path cannot be empty.")

    if "\x00" in raw_path:
        raise ValueError("The output path cannot contain null bytes.")

    path = Path(raw_path).expanduser()

    if allowed_extensions is not None:
        if not allowed_extensions:
            raise ValueError("The allowed extensions set cannot be empty.")

        if any(
            not extension.startswith(".")
            or extension == "."
            or "/" in extension
            or "\\" in extension
            or extension != extension.strip()
            for extension in allowed_extensions
        ):
            raise ValueError(
                "Each allowed extension must be a valid extension "
                "beginning with a period."
            )

        normalized_extensions = {extension.lower() for extension in allowed_extensions}

        if path.suffix.lower() not in normalized_extensions:
            raise ValueError(
                "The output file must use one of these extensions: "
                f"{', '.join(sorted(normalized_extensions))}."
            )

    if path.is_symlink():
        raise ValueError(f"The output path cannot be a symbolic link: {path}")

    if path.exists() and not path.is_file():
        raise ValueError(
            f"The output destination exists but is not a regular file: {path}"
        )

    if path.parent.exists() and not path.parent.is_dir():
        raise ValueError(
            f"The parent path exists but is not a directory: {path.parent}"
        )

    return path


def resolve_output_path(
    *,
    output_path: str | Path,
    allowed_extensions: set[str] | None = None,
) -> Path | None:
    """Resolve an output destination and prevent accidental overwrites.

    Validates the proposed destination and interacts with the user when
    the path is invalid or the output file already exists. The user may
    approve overwriting an existing file, choose another destination,
    or cancel the operation.

    Args:
        output_path: The proposed output file destination.
        allowed_extensions: Permitted file extensions, if restricted.

    Returns:
        The approved output path, or None if the user cancels.

    Raises:
        EOFError: If standard input closes while awaiting user input.
        KeyboardInterrupt: If the user interrupts the operation.
    """
    while True:
        try:
            path = validate_output_path(
                output_path=output_path,
                allowed_extensions=allowed_extensions,
            )
        except ValueError as exc:
            print(f"Invalid output path: {exc}", file=sys.stderr)

            output_path = input(
                "Enter a valid output path, or press Enter to cancel: "
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
            print("Operation cancelled.")
            return None

        else:
            print("Invalid choice. Enter 1, 2, or 3.")
