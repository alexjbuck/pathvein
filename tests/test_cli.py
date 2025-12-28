"""Tests for CLI functionality."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pathvein.cli import cli
from pathvein.pattern import FileStructurePattern

runner = CliRunner()


@pytest.fixture
def temp_pattern_file(tmp_path):
    """Create a temporary pattern file for testing."""
    pattern = FileStructurePattern(
        directory_name="test_*",
        files=["data.csv"],
        optional_files=["notes.txt"]
    )
    pattern_file = tmp_path / "pattern.json"
    pattern_file.write_text(pattern.to_json())
    return pattern_file


@pytest.fixture
def temp_source_dir(tmp_path):
    """Create a temporary source directory with test structure."""
    source = tmp_path / "source"
    source.mkdir()

    # Create matching directory
    match_dir = source / "test_001"
    match_dir.mkdir()
    (match_dir / "data.csv").write_text("test,data\n")
    (match_dir / "notes.txt").write_text("notes\n")

    # Create another matching directory
    match_dir2 = source / "test_002"
    match_dir2.mkdir()
    (match_dir2 / "data.csv").write_text("more,data\n")

    # Create non-matching directory
    no_match = source / "other"
    no_match.mkdir()
    (no_match / "random.txt").write_text("random\n")

    return source


class TestCLIScan:
    """Tests for the scan command."""

    def test_scan_finds_matches(self, temp_source_dir, temp_pattern_file):
        """Test that scan command finds matching directories."""
        result = runner.invoke(
            cli,
            ["scan", str(temp_source_dir), "--pattern", str(temp_pattern_file)]
        )

        assert result.exit_code == 0
        assert "test_001" in result.stdout
        assert "test_002" in result.stdout
        assert "other" not in result.stdout

    def test_scan_no_matches(self, tmp_path, temp_pattern_file):
        """Test scan with no matching directories."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(
            cli,
            ["scan", str(empty_dir), "--pattern", str(temp_pattern_file)]
        )

        assert result.exit_code == 0
        assert result.stdout.strip() == ""

    def test_scan_missing_pattern_file(self, temp_source_dir, tmp_path):
        """Test scan with non-existent pattern file."""
        missing_file = tmp_path / "missing.json"

        result = runner.invoke(
            cli,
            ["scan", str(temp_source_dir), "--pattern", str(missing_file)]
        )

        assert result.exit_code != 0

    def test_scan_invalid_pattern_json(self, temp_source_dir, tmp_path):
        """Test scan with invalid JSON pattern file."""
        bad_pattern = tmp_path / "bad.json"
        bad_pattern.write_text("not valid json {")

        result = runner.invoke(
            cli,
            ["scan", str(temp_source_dir), "--pattern", str(bad_pattern)]
        )

        assert result.exit_code != 0

    def test_scan_multiple_patterns(self, temp_source_dir, tmp_path):
        """Test scan with multiple pattern files."""
        # Create first pattern
        pattern1 = FileStructurePattern(
            directory_name="test_*",
            files=["data.csv"]
        )
        pattern_file1 = tmp_path / "pattern1.json"
        pattern_file1.write_text(pattern1.to_json())

        # Create second pattern
        pattern2 = FileStructurePattern(
            directory_name="other",
            files=["random.txt"]
        )
        pattern_file2 = tmp_path / "pattern2.json"
        pattern_file2.write_text(pattern2.to_json())

        result = runner.invoke(
            cli,
            [
                "scan",
                str(temp_source_dir),
                "--pattern", str(pattern_file1),
                "--pattern", str(pattern_file2)
            ]
        )

        assert result.exit_code == 0
        assert "test_001" in result.stdout or "test_002" in result.stdout
        assert "other" in result.stdout

    def test_scan_verbosity_flag(self, temp_source_dir, temp_pattern_file):
        """Test scan with verbosity flags."""
        result = runner.invoke(
            cli,
            ["scan", str(temp_source_dir), "--pattern", str(temp_pattern_file), "-v"]
        )

        assert result.exit_code == 0

    def test_scan_multiple_verbosity(self, temp_source_dir, temp_pattern_file):
        """Test scan with multiple verbosity flags."""
        result = runner.invoke(
            cli,
            ["scan", str(temp_source_dir), "--pattern", str(temp_pattern_file), "-vvv"]
        )

        assert result.exit_code == 0


class TestCLIShuffle:
    """Tests for the shuffle command."""

    def test_shuffle_copies_matches(self, temp_source_dir, temp_pattern_file, tmp_path):
        """Test that shuffle command copies matching directories."""
        dest = tmp_path / "dest"

        result = runner.invoke(
            cli,
            [
                "shuffle",
                str(temp_source_dir),
                str(dest),
                "--pattern", str(temp_pattern_file)
            ]
        )

        assert result.exit_code == 0
        assert (dest / "test_001").exists()
        assert (dest / "test_001" / "data.csv").exists()
        assert (dest / "test_002").exists()
        assert (dest / "test_002" / "data.csv").exists()
        assert not (dest / "other").exists()

    def test_shuffle_shows_operations(self, temp_source_dir, temp_pattern_file, tmp_path):
        """Test that shuffle shows what it's doing."""
        dest = tmp_path / "dest"

        result = runner.invoke(
            cli,
            [
                "shuffle",
                str(temp_source_dir),
                str(dest),
                "--pattern", str(temp_pattern_file)
            ]
        )

        assert result.exit_code == 0
        assert "test_001" in result.stdout
        assert "test_002" in result.stdout
        assert "->" in result.stdout
        assert "Copied" in result.stdout

    def test_shuffle_overwrite_flag(self, temp_source_dir, temp_pattern_file, tmp_path):
        """Test shuffle with overwrite flag."""
        dest = tmp_path / "dest"
        dest.mkdir()
        existing = dest / "test_001"
        existing.mkdir()

        # First try without overwrite (should fail or skip)
        result = runner.invoke(
            cli,
            [
                "shuffle",
                str(temp_source_dir),
                str(dest),
                "--pattern", str(temp_pattern_file)
            ]
        )

        # The command should complete even if some copies fail
        assert result.exit_code == 0

    def test_shuffle_dryrun(self, temp_source_dir, temp_pattern_file, tmp_path):
        """Test shuffle with dryrun flag."""
        dest = tmp_path / "dest"

        result = runner.invoke(
            cli,
            [
                "shuffle",
                str(temp_source_dir),
                str(dest),
                "--pattern", str(temp_pattern_file),
                "--dryrun"
            ]
        )

        assert result.exit_code == 0
        # Destination should not be created in dryrun mode
        assert not dest.exists() or not (dest / "test_001").exists()

    def test_shuffle_verbosity(self, temp_source_dir, temp_pattern_file, tmp_path):
        """Test shuffle with verbosity flags."""
        dest = tmp_path / "dest"

        result = runner.invoke(
            cli,
            [
                "shuffle",
                str(temp_source_dir),
                str(dest),
                "--pattern", str(temp_pattern_file),
                "-vv"
            ]
        )

        assert result.exit_code == 0

    def test_shuffle_no_matches(self, tmp_path, temp_pattern_file):
        """Test shuffle with no matching directories."""
        empty_source = tmp_path / "empty_source"
        empty_source.mkdir()
        dest = tmp_path / "dest"

        result = runner.invoke(
            cli,
            [
                "shuffle",
                str(empty_source),
                str(dest),
                "--pattern", str(temp_pattern_file)
            ]
        )

        assert result.exit_code == 0
        assert "Copied 0 directories" in result.stdout


class TestCLIHelp:
    """Tests for CLI help and options."""

    def test_help_flag(self):
        """Test that --help flag works."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "scan" in result.stdout
        assert "shuffle" in result.stdout

    def test_scan_help(self):
        """Test scan command help."""
        result = runner.invoke(cli, ["scan", "--help"])

        assert result.exit_code == 0
        assert "scan" in result.stdout.lower()

    def test_shuffle_help(self):
        """Test shuffle command help."""
        result = runner.invoke(cli, ["shuffle", "--help"])

        assert result.exit_code == 0
        assert "shuffle" in result.stdout.lower()
