from pathlib import Path

import pytest

from pqc_inventory.cli import resolve_output_path


def test_accepts_new_json_path(tmp_path: Path) -> None:
    output_path = tmp_path / "evidence.json"

    result = resolve_output_path(str(output_path))

    assert result == output_path
    assert not output_path.exists()


def test_rejects_invalid_extension_until_valid_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid_path = tmp_path / "evidence.txt"
    valid_path = tmp_path / "evidence.json"

    responses = iter([str(valid_path)])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(str(invalid_path))

    assert result == valid_path


def test_requires_confirmation_before_overwriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "evidence.json"
    output_path.write_text('{"existing": true}', encoding="utf-8")

    responses = iter(["1", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(str(output_path))

    assert result == output_path
    assert output_path.read_text(encoding="utf-8") == '{"existing": true}'


def test_declining_overwrite_does_not_approve_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "evidence.json"
    output_path.write_text('{"existing": true}', encoding="utf-8")

    responses = iter(["1", "n", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(str(output_path))

    assert result is None
    assert output_path.read_text(encoding="utf-8") == '{"existing": true}'


def test_allows_user_to_choose_another_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_path = tmp_path / "existing.json"
    new_path = tmp_path / "new.json"

    existing_path.write_text('{"existing": true}', encoding="utf-8")

    responses = iter(["2", str(new_path)])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    result = resolve_output_path(str(existing_path))

    assert result == new_path


def test_cancels_when_user_selects_cancel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "evidence.json"
    output_path.write_text('{"existing": true}', encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda _: "3")

    result = resolve_output_path(str(output_path))

    assert result is None
    assert output_path.read_text(encoding="utf-8") == '{"existing": true}'
