"""Cross-platform filesystem directory management utilities."""

import stat
from pathlib import Path

from pqc_inventory.infrastructure.filesystem.path_safety import (
    validate_path,
)


def directory_exists(path: str | Path) -> bool:
    """Determine whether a valid directory exists.

    Symbolic links and Windows reparse points are rejected.
    Missing directories return False.
    """

    directory = validate_path(path)

    try:
        details = directory.lstat()
    except FileNotFoundError:
        return False

    return stat.S_ISDIR(details.st_mode)


def ensure_directory(path: str | Path) -> Path:
    """Create a directory and missing parent directories when necessary.

    Existing directories are accepted. Existing files, symbolic links
    and prohibited filesystem redirections are rejected.

    Returns:
        The absolute path of the validated directory.
    """

    directory = validate_path(path)

    try:
        details = directory.lstat()

    except FileNotFoundError:
        directory.mkdir(parents=True, exist_ok=True)

    else:
        if not stat.S_ISDIR(details.st_mode):
            raise NotADirectoryError(
                f"The specified path is not a directory: {directory}"
            )

    # Inspect the path again after creation.
    directory = validate_path(directory)

    try:
        details = directory.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Directory creation could not be verified: {directory}"
        ) from error

    if not stat.S_ISDIR(details.st_mode):
        raise NotADirectoryError(f"The resulting path is not a directory: {directory}")

    return directory
