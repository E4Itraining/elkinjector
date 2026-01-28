"""Tests for elkinjector.cli module."""

from __future__ import annotations

import os
import tempfile

from click.testing import CliRunner

from elkinjector.cli import main


class TestCli:
    """Tests for the CLI interface."""

    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ElkInjector" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_inject_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["inject", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--batch-size" in result.output
        assert "--continuous" in result.output

    def test_check_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["check", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output

    def test_clean_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["clean", "--help"])
        assert result.exit_code == 0
        assert "--prefix" in result.output
        assert "--force" in result.output

    def test_init_config_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["init-config", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output

    def test_show_placeholders_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["show-placeholders", "--help"])
        assert result.exit_code == 0

    def test_show_placeholders(self):
        runner = CliRunner()
        result = runner.invoke(main, ["show-placeholders"])
        assert result.exit_code == 0
        assert "timestamp" in result.output
        assert "uuid" in result.output
        assert "email" in result.output

    def test_init_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_config.yaml")
            result = runner.invoke(main, ["init-config", "-o", output_path])
            assert result.exit_code == 0
            assert os.path.exists(output_path)
            assert "Configuration file created" in result.output
