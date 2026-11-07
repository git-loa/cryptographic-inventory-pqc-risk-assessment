"""Filesystem path safety utilities."""

from pathlib import Path


def contains_symlink(path: str | Path) -> bool:
    """Return whether a path or any of its ancestors is a symbolic link."""
    candidate = Path(path)

    return any(component.is_symlink() for component in (candidate, *candidate.parents))
