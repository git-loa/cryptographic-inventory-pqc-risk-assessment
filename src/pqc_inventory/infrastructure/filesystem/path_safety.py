"""Cross-platform filesystem path safety utilities."""

import os
import stat
from collections.abc import Iterator
from pathlib import Path


def is_symbolic_link(path: str | Path) -> bool:
    """Determine whether a filesystem entry is a symbolic link."""

    candidate = Path(path)

    try:
        details = candidate.lstat()
    except FileNotFoundError:
        return False

    return stat.S_ISLNK(details.st_mode)


def is_reparse_point(path: str | Path) -> bool:
    """Determine whether a filesystem entry is a Windows reparse point."""

    if os.name != "nt":
        return False

    candidate = Path(path)

    try:
        details = candidate.lstat()
    except FileNotFoundError:
        return False

    attributes = getattr(details, "st_file_attributes", 0)

    reparse_flag = getattr(
        stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        0,
    )

    return bool(attributes & reparse_flag)


def _iter_path_components(path: Path) -> Iterator[Path]:
    """Yield individual path components without resolving symbolic links."""

    candidate = Path(path).expanduser()

    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate

    current = Path(candidate.anchor)

    for part in candidate.parts[1:]:
        if part == "..":
            current = current.parent
            continue

        current = current / part
        yield current


def validate_path(path: str | Path) -> Path:
    """Validate an existing or prospective filesystem path.

    Reject symbolic links and Windows reparse points in existing
    path components. Missing components are permitted.
    """

    candidate = Path(path).expanduser()

    for component in _iter_path_components(candidate):
        if is_symbolic_link(component) or is_reparse_point(component):
            raise ValueError(
                "Symbolic links and reparse points are not permitted: " f"{component}"
            )

    # Normalize the path without resolving filesystem links.
    return Path(os.path.abspath(candidate))


def validate_path_within(
    path: str | Path,
    base_directory: str | Path,
) -> Path:
    """Validate that a path remains within an approved directory."""

    base = validate_path(base_directory)

    if not base.is_dir():
        raise ValueError(f"The approved base path is not an existing directory: {base}")

    candidate = Path(path).expanduser()

    if not candidate.is_absolute():
        candidate = base / candidate

    candidate = validate_path(candidate)

    try:
        common = Path(os.path.commonpath((str(base), str(candidate))))
    except ValueError as error:
        raise ValueError(
            f"The path is outside the approved directory: {candidate}"
        ) from error

    if os.path.normcase(str(common)) != os.path.normcase(str(base)):
        raise ValueError(f"The path is outside the approved directory: {candidate}")

    return candidate


def contains_symlink(path: str | Path) -> bool:
    """Check whether a path or any existing ancestor is a symbolic link.

    Retained temporarily for compatibility with existing application code.
    """

    return any(
        is_symbolic_link(component) for component in _iter_path_components(Path(path))
    )
