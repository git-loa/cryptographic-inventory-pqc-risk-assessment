"""Unit tests for the generic CLI output path resolver."""

from pathlib import Path

import pytest

from pqc_inventory.commands.common import (
    resolve_output_directory,
    resolve_output_path,
    validate_output_directory,
    validate_output_path,
)


def test_accepts_new_json_path(tmp_path: Path) -> None:
    """Accept a new JSON output path without prompting."""
    output_path = tmp_path / "evidence.json"

    result = resolve_output_path(
        output_path=output_path,
        allowed_extensions={".json"},
    )

    assert result == output_path
    assert not output_path.exists()


def test_accepts_new_markdown_path(tmp_path: Path) -> None:
    """Accept a new Markdown output path without prompting."""
    output_path = tmp_path / "assessment_report.md"

    result = resolve_output_path(
        output_path=output_path,
        allowed_extensions={".md"},
    )

    assert result == output_path
    assert not output_path.exists()


def test_rejects_invalid_extension_until_valid_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Continue prompting until a path with an allowed extension is provided."""
    invalid_path = tmp_path / "evidence.txt"
    valid_path = tmp_path / "evidence.json"

    responses = iter([str(valid_path)])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(
        output_path=invalid_path,
        allowed_extensions={".json"},
    )

    assert result == valid_path


def test_requires_confirmation_before_overwriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require explicit confirmation before approving an existing file."""
    output_path = tmp_path / "evidence.json"
    original_content = '{"existing": true}'
    output_path.write_text(original_content, encoding="utf-8")

    responses = iter(["1", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(
        output_path=output_path,
        allowed_extensions={".json"},
    )

    assert result == output_path
    assert output_path.read_text(encoding="utf-8") == original_content


def test_declining_overwrite_does_not_approve_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return None when the user declines overwriting and then cancels."""
    output_path = tmp_path / "evidence.json"
    original_content = '{"existing": true}'
    output_path.write_text(original_content, encoding="utf-8")

    responses = iter(["1", "n", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(
        output_path=output_path,
        allowed_extensions={".json"},
    )

    assert result is None
    assert output_path.read_text(encoding="utf-8") == original_content


def test_allows_user_to_choose_another_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Allow the user to select another valid output destination."""
    existing_path = tmp_path / "existing.json"
    new_path = tmp_path / "new.json"

    existing_path.write_text('{"existing": true}', encoding="utf-8")

    responses = iter(["2", str(new_path)])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(
        output_path=existing_path,
        allowed_extensions={".json"},
    )

    assert result == new_path


def test_cancels_when_user_selects_cancel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return None when the user cancels the operation."""
    output_path = tmp_path / "evidence.json"
    original_content = '{"existing": true}'
    output_path.write_text(original_content, encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda _: "3")

    result = resolve_output_path(
        output_path=output_path,
        allowed_extensions={".json"},
    )

    assert result is None
    assert output_path.read_text(encoding="utf-8") == original_content


def test_accepts_new_output_directory(tmp_path: Path) -> None:
    """Accept a new output directory without creating it."""

    output_directory = tmp_path / "reports"

    result = validate_output_directory(
        output_directory=output_directory,
    )

    assert result == output_directory
    assert not output_directory.exists()


def test_accepts_existing_output_directory(tmp_path: Path) -> None:
    """Accept an existing directory."""

    output_directory = tmp_path / "reports"
    output_directory.mkdir()

    result = validate_output_directory(
        output_directory=output_directory,
    )

    assert result == output_directory


def test_rejects_file_as_output_directory(tmp_path: Path) -> None:
    """Reject an existing file as an output directory."""

    output_file = tmp_path / "report.md"
    output_file.write_text("Report", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        validate_output_directory(
            output_directory=output_file,
        )


def test_resolves_invalid_directory_until_valid_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prompt for a replacement after receiving an invalid directory."""

    invalid_directory = tmp_path / "report.md"
    invalid_directory.write_text("Report", encoding="utf-8")

    valid_directory = tmp_path / "reports"

    responses = iter([str(valid_directory)])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_directory(
        output_directory=invalid_directory,
    )

    assert result == valid_directory


def test_cancels_invalid_output_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return None when the user cancels directory selection."""

    invalid_directory = tmp_path / "report.md"
    invalid_directory.write_text("Report", encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda _: "")

    result = resolve_output_directory(
        output_directory=invalid_directory,
    )

    assert result is None


def test_rejects_symlink_in_output_path_parent(
    tmp_path: Path,
) -> None:
    """Reject an output path containing a symbolic-link parent."""

    target_directory = tmp_path / "actual_reports"
    target_directory.mkdir()

    symlink_directory = tmp_path / "reports"

    try:
        symlink_directory.symlink_to(
            target_directory,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symbolic links are unavailable: {exc}")

    output_path = symlink_directory / "assessment_report.md"

    with pytest.raises(ValueError, match="symbolic links"):
        validate_output_path(output_path=output_path)


def test_rejects_symlink_in_output_directory_parent(
    tmp_path: Path,
) -> None:
    """Reject an output directory containing a symbolic-link ancestor."""

    target_directory = tmp_path / "actual_reports"
    target_directory.mkdir()

    symlink_directory = tmp_path / "reports"

    try:
        symlink_directory.symlink_to(
            target_directory,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symbolic links are unavailable: {exc}")

    output_directory = symlink_directory / "generated"

    with pytest.raises(ValueError, match="symbolic links"):
        validate_output_directory(
            output_directory=output_directory,
        )
