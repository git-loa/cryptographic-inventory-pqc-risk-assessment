"""Tests for filesystem directory management."""

import os
import subprocess
import pytest

from pqc_inventory.infrastructure.filesystem.directory_manager import (
    directory_exists,
    ensure_directory,
)


def test_directory_exists_for_existing_directory(tmp_path):
    """Recognize an existing directory."""

    directory = tmp_path / "data"
    directory.mkdir()

    assert directory_exists(directory) is True


def test_directory_exists_returns_false_for_missing_directory(tmp_path):
    """Return False when a directory does not exist."""

    directory = tmp_path / "missing"

    assert directory_exists(directory) is False


def test_directory_exists_rejects_regular_file(tmp_path):
    """Do not classify an ordinary file as a directory."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    assert directory_exists(file_path) is False


def test_ensure_directory_creates_directory(tmp_path):
    """Create a directory that does not exist."""

    directory = tmp_path / "data"

    result = ensure_directory(directory)

    assert result == directory.absolute()
    assert directory.is_dir()


def test_ensure_directory_creates_parent_directories(tmp_path):
    """Create missing parent directories."""

    directory = tmp_path / "data" / "evidence" / "reports"

    result = ensure_directory(directory)

    assert result == directory.absolute()
    assert directory.is_dir()


def test_ensure_directory_accepts_existing_directory(tmp_path):
    """Accept an existing directory without modifying it."""

    directory = tmp_path / "existing"
    directory.mkdir()

    result = ensure_directory(directory)

    assert result == directory.absolute()
    assert directory.is_dir()


def test_ensure_directory_rejects_regular_file(tmp_path):
    """Reject a file supplied as a directory."""

    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        ensure_directory(file_path)


def test_ensure_directory_rejects_symbolic_link(tmp_path):
    """Reject a symbolic link used as a directory."""

    target = tmp_path / "target"
    target.mkdir()

    link = tmp_path / "link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is not permitted.")

    with pytest.raises(ValueError, match="Symbolic links"):
        ensure_directory(link)


def test_ensure_directory_rejects_junction(tmp_path):
    """Reject a Windows directory junction."""

    if os.name != "nt":
        pytest.skip("Directory junctions are Windows-specific.")

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
        pytest.skip("Unable to create directory junction.")

    try:
        with pytest.raises(ValueError, match="reparse points"):
            ensure_directory(junction)
    finally:
        if junction.exists():
            junction.rmdir()


def test_ensure_directory_rejects_symbolic_link_parent(tmp_path):
    """Reject a directory path containing a symbolic-link parent."""

    target = tmp_path / "actual"
    target.mkdir()

    link = tmp_path / "linked"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic link creation is not permitted.")

    directory = link / "logs"

    with pytest.raises(ValueError, match="Symbolic links"):
        ensure_directory(directory)
