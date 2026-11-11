"""Cross-platform filesystem permission interfaces."""

import os
from pathlib import Path

from pqc_inventory.infrastructure.filesystem.backends import (
    posix,
    windows,
)
from pqc_inventory.infrastructure.filesystem.path_safety import (
    validate_path,
)

_PERMISSION_BACKENDS = {
    "posix": posix,
    "nt": windows,
}


def _get_permission_backend():
    """Select the filesystem permission backend for the current OS."""

    backend = _PERMISSION_BACKENDS.get(os.name)

    if backend is None:
        raise NotImplementedError(f"Unsupported operating system: {os.name}")

    return backend


def has_access(path: str | Path, mode: int) -> bool:
    """Check whether the current process has the requested access."""

    if isinstance(mode, bool) or not isinstance(mode, int):
        raise TypeError("Access mode must be an integer.")

    allowed_modes = os.R_OK | os.W_OK

    if mode == 0 or mode & ~allowed_modes:
        raise ValueError("Access mode must contain os.R_OK, os.W_OK, or both.")

    candidate = validate_path(path)

    try:
        candidate.lstat()
    except FileNotFoundError:
        return False

    return os.access(candidate, mode)


def require_access(path: str | Path, mode: int) -> Path:
    """Require the current process to have the requested filesystem access."""

    candidate = validate_path(path)

    if not has_access(candidate, mode):
        raise PermissionError(f"Insufficient filesystem permissions for: {candidate}")

    return candidate


def set_directory_mode(
    path: str | Path,
    mode: int = 0o700,
) -> Path:
    """Delegate directory permission changes to the OS-specific backend."""

    backend = _get_permission_backend()

    return backend.set_directory_mode(path, mode)
