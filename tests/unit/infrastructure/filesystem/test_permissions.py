"""Tests for cross-platform filesystem permission utilities."""

import os
import stat

import pytest

from pqc_inventory.infrastructure.filesystem.permissions import (
    has_access,
    require_access,
    set_directory_mode,
)
from pqc_inventory.infrastructure.filesystem.backends.posix import (
    set_directory_mode as set_posix_directory_mode,
)

# ---------------------------------------------------------------------------
# Access checks
# ---------------------------------------------------------------------------


def test_has_read_access_to_existing_file(tmp_path):
    """Recognize read access to an existing file."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    assert has_access(file_path, os.R_OK) is True


def test_has_write_access_to_existing_directory(tmp_path):
    """Recognize write access to an existing directory."""

    assert has_access(tmp_path, os.W_OK) is True


def test_has_access_returns_false_for_missing_path(tmp_path):
    """Return False when the requested path does not exist."""

    missing = tmp_path / "missing"

    assert has_access(missing, os.R_OK) is False


@pytest.mark.parametrize("mode", [0, 8, -1, 1])
def test_has_access_rejects_invalid_mode(tmp_path, mode):
    """Reject unsupported access modes."""

    with pytest.raises(ValueError):
        has_access(tmp_path, mode)


def test_has_access_rejects_boolean_mode(tmp_path):
    """Reject Boolean values as access modes."""

    with pytest.raises(TypeError):
        has_access(tmp_path, True)


def test_require_access_returns_validated_path(tmp_path):
    """Return the path when the requested access is available."""

    result = require_access(tmp_path, os.R_OK)

    assert result == tmp_path.absolute()


def test_require_access_rejects_missing_path(tmp_path):
    """Raise PermissionError when access is unavailable."""

    missing = tmp_path / "missing"

    with pytest.raises(PermissionError):
        require_access(missing, os.W_OK)


def test_has_access_rejects_symbolic_link(tmp_path):
    """Reject symbolic links during access checks."""

    target = tmp_path / "target"
    target.mkdir()

    link = tmp_path / "link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is not permitted.")

    with pytest.raises(ValueError, match="Symbolic links"):
        has_access(link, os.R_OK)


# ---------------------------------------------------------------------------
# POSIX backend
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX permission modes are not supported on Windows.",
)
def test_set_directory_mode(tmp_path):
    """Apply owner-only permissions to an existing directory."""

    directory = tmp_path / "private"
    directory.mkdir()

    result = set_directory_mode(directory, 0o700)

    assert result == directory.absolute()

    actual_mode = stat.S_IMODE(directory.stat().st_mode)

    assert actual_mode == 0o700


@pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX permission modes are not supported on Windows.",
)
@pytest.mark.parametrize(
    "mode",
    [-1, 0o1000, 0o7777, True],
)
def test_posix_backend_rejects_invalid_modes(tmp_path, mode):
    """Reject invalid POSIX permission modes."""

    with pytest.raises(ValueError):
        set_posix_directory_mode(tmp_path, mode)


@pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX permission modes are not supported on Windows.",
)
def test_posix_backend_rejects_missing_directory(tmp_path):
    """Reject nonexistent directories."""

    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        set_posix_directory_mode(missing)


@pytest.mark.skipif(
    os.name != "posix",
    reason="POSIX permission modes are not supported on Windows.",
)
def test_posix_backend_rejects_regular_file(tmp_path):
    """Reject regular files supplied as directories."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        set_posix_directory_mode(file_path)


# ---------------------------------------------------------------------------
# Windows backend
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows-specific permission backend.",
)
def test_windows_backend_rejects_posix_modes(tmp_path):
    """Reject POSIX permission-mode operations on Windows."""

    with pytest.raises(NotImplementedError, match="Windows ACL"):
        set_directory_mode(tmp_path, 0o700)
