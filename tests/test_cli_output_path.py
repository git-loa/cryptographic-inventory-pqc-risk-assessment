"""Unit tests for the generic CLI output path resolver."""

from pathlib import Path

import pytest

from pqc_inventory.commands.common import resolve_output_path


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
