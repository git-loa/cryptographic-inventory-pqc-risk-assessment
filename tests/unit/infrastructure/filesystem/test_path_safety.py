"""Tests for cross-platform filesystem path safety."""

import os
import subprocess
import pytest

from pqc_inventory.infrastructure.filesystem.path_safety import (
    contains_symlink,
    is_reparse_point,
    is_symbolic_link,
    validate_path,
    validate_path_within,
)


def test_existing_regular_file_is_not_symbolic_link(tmp_path):
    """Recognize an ordinary file."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    assert is_symbolic_link(file_path) is False


def test_nonexistent_path_is_not_symbolic_link(tmp_path):
    """Handle paths that do not exist."""

    file_path = tmp_path / "missing.txt"

    assert is_symbolic_link(file_path) is False


def test_existing_directory_is_not_reparse_point(tmp_path):
    """An ordinary directory is not a Windows reparse point."""

    assert is_reparse_point(tmp_path) is False


def test_validate_existing_file(tmp_path):
    """Accept an ordinary file."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    assert validate_path(file_path) == file_path.absolute()


def test_validate_nonexistent_path(tmp_path):
    """Allow prospective paths that do not exist."""

    file_path = tmp_path / "new" / "example.txt"

    assert validate_path(file_path) == file_path.absolute()


def test_validate_path_rejects_symbolic_link(tmp_path):
    """Reject a symbolic link in the requested path."""

    target = tmp_path / "target"
    target.mkdir()

    link = tmp_path / "link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is not permitted.")

    with pytest.raises(ValueError, match="Symbolic links"):
        validate_path(link / "example.txt")


def test_validate_path_within_accepts_child_path(tmp_path):
    """Accept a path inside its approved directory."""

    base = tmp_path / "data"
    base.mkdir()

    result = validate_path_within(
        "evidence.json",
        base,
    )

    assert result == (base / "evidence.json").absolute()


def test_validate_path_within_rejects_outside_path(tmp_path):
    """Reject paths outside the approved directory."""

    base = tmp_path / "data"
    base.mkdir()

    outside = tmp_path / "data-backup" / "evidence.json"

    with pytest.raises(ValueError, match="outside"):
        validate_path_within(outside, base)


def test_validate_path_within_rejects_symbolic_link(tmp_path):
    """Reject symbolic links inside the approved directory."""

    base = tmp_path / "data"
    base.mkdir()

    target = tmp_path / "external"
    target.mkdir()

    link = base / "external_link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is not permitted.")

    with pytest.raises(ValueError, match="Symbolic links"):
        validate_path_within(link / "evidence.json", base)


def test_contains_symlink_returns_false_for_regular_path(tmp_path):
    """Preserve compatibility for ordinary filesystem paths."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    assert contains_symlink(file_path) is False


def test_contains_symlink_detects_symbolic_link(tmp_path):
    """Preserve compatibility for symbolic-link detection."""

    target = tmp_path / "target"
    target.mkdir()

    link = tmp_path / "link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is not permitted.")

    assert contains_symlink(link / "example.txt") is True


@pytest.mark.skipif(
    os.name != "nt",
    reason="Directory junctions are Windows-specific.",
)
def test_directory_junction_is_detected(tmp_path):
    """Detect and reject a Windows directory junction."""

    target = tmp_path / "target"
    target.mkdir()

    junction = tmp_path / "junction"

    result = subprocess.run(
        f'mklink /J "{junction}" "{target}"',
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        pytest.skip(f"Unable to create directory junction: {result.stderr}")

    try:
        assert is_reparse_point(junction) is True

        with pytest.raises(ValueError, match="reparse points"):
            validate_path(junction / "example.txt")

    finally:
        # Remove the junction itself, not its target directory.
        if junction.exists():
            junction.rmdir()
