"""Windows filesystem permission operations."""

from pathlib import Path


def set_directory_mode(
    path: str | Path,
    mode: int = 0o700,
) -> Path:
    """Reject POSIX permission-mode operations on Windows.

    Windows directory permissions are managed through access-control
    lists (ACLs), not POSIX permission bits.
    """

    raise NotImplementedError(
        "POSIX permission modes are not supported on Windows. "
        "Windows ACL management requires a dedicated implementation."
    )
