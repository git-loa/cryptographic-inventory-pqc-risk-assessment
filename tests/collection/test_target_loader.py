from pathlib import Path

import pytest

from pqc_inventory.collection.target_loader import load_targets


def test_load_targets_accepts_domains_and_ip_addresses(
    tmp_path: Path,
) -> None:
    target_file = tmp_path / "targets.txt"
    target_file.write_text(
        "example.com\n" "192.168.1.10\n" "2001:db8::1\n",
        encoding="utf-8",
    )

    targets = load_targets(target_file)

    assert targets == [
        "example.com",
        "192.168.1.10",
        "2001:db8::1",
    ]


def test_load_targets_ignores_blank_lines_and_comments(
    tmp_path: Path,
) -> None:
    target_file = tmp_path / "targets.txt"
    target_file.write_text(
        "# Production targets\n"
        "\n"
        "example.com\n"
        "   \n"
        "# Another comment\n"
        "192.168.1.10\n",
        encoding="utf-8",
    )

    targets = load_targets(target_file)

    assert targets == ["example.com", "192.168.1.10"]


def test_load_targets_preserves_order_and_duplicates(
    tmp_path: Path,
) -> None:
    target_file = tmp_path / "targets.txt"
    target_file.write_text(
        "example.com\n" "cloudflare.com\n" "example.com\n",
        encoding="utf-8",
    )

    targets = load_targets(target_file)

    assert targets == [
        "example.com",
        "cloudflare.com",
        "example.com",
    ]


def test_load_targets_reports_invalid_target_and_line_number(
    tmp_path: Path,
) -> None:
    target_file = tmp_path / "targets.txt"
    target_file.write_text(
        "example.com\n" "\n" "invalid_target!\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 3"):
        load_targets(target_file)


def test_load_targets_rejects_empty_file(tmp_path: Path) -> None:
    target_file = tmp_path / "targets.txt"
    target_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="No valid targets"):
        load_targets(target_file)


def test_load_targets_rejects_missing_file(tmp_path: Path) -> None:
    target_file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        load_targets(target_file)
