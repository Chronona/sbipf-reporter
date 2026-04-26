"""Tests for sbipf_reporter package."""

from sbipf_reporter import __version__


def test_version() -> None:
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_failing_test() -> None:
    """This test is expected to fail to verify CI is working."""
    assert False, "This test is intentionally failing to verify CI pipeline"
