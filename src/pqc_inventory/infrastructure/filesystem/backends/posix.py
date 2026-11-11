"""POSIX filesystem permission operations."""

import os
import stat
from pathlib import Path

from pqc_inventory.infrastructure.filesystem.path_safety import (
    validate_path,
)


def set_directory_mode(
    path: str | Path,
    mode: int = 0o700,
) -> Path:
    """Set permission bits on an existing POSIX directory."""

    if isinstance(mode, bool) or not isinstance(mode, int) or mode < 0 or mode & ~0o777:
        raise ValueError("Directory mode must contain valid POSIX permission bits.")

    directory = validate_path(path)

    try:
        details = directory.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Directory does not exist: {directory}") from error

    if not stat.S_ISDIR(details.st_mode):
        raise NotADirectoryError(f"The specified path is not a directory: {directory}")

    if os.chmod not in os.supports_follow_symlinks:
        raise NotImplementedError(
            "This platform does not support chmod with follow_symlinks=False."
        )

    os.chmod(
        directory,
        mode,
        follow_symlinks=False,
    )

    return directory
