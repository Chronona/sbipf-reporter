"""Tests for reporter module."""

from pathlib import Path

from sbipf_reporter.parser import parse_sbi_csv
from sbipf_reporter.reporter import OutputFormat, format_as_csv, format_as_markdown


def test_format_as_csv(tmp_path: Path) -> None:
    """Test CSV output."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    output_path = tmp_path / "output.csv"
    format_as_csv(holdings, output_path)

    content = output_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    assert lines[0] == "コード,銘柄名,口座,買付日,数量,取得単価,現在値,評価額,損益,損益率"
    assert len(lines) == 18  # header + 16 data + empty


def test_format_as_markdown(tmp_path: Path) -> None:
    """Test Markdown output."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    output_path = tmp_path / "output.md"
    format_as_markdown(holdings, output_path)

    content = output_path.read_text(encoding="utf-8")

    assert "# SBI証券ポートフォリオ" in content
    assert "| コード | 銘柄名 |" in content
    assert "**合計**: 保有数 16件" in content


def test_csv_output_contains_correct_data(tmp_path: Path) -> None:
    """Test that CSV contains correct values."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    output_path = tmp_path / "output.csv"
    format_as_csv(holdings, output_path)

    content = output_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # First data row: 6758 ソニー
    first_row = lines[1]
    assert "6758" in first_row
    assert "ソニー" in first_row
    assert "特定" in first_row
    assert "1950.0" in first_row  # profit


def test_markdown_output_contains_correct_data(tmp_path: Path) -> None:
    """Test that Markdown contains correct values."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    output_path = tmp_path / "output.md"
    format_as_markdown(holdings, output_path)

    content = output_path.read_text(encoding="utf-8")

    assert "6758" in content
    assert "ソニー" in content
    assert "+3.42%" in content  # total profit rate
