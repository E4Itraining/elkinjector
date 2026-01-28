#!/usr/bin/env python3
"""
ElkInjector Test Runner

Run unit tests with various options:

    # Run all tests
    python run_tests.py

    # Run with verbose output
    python run_tests.py -v

    # Run with coverage report
    python run_tests.py --cov

    # Run a specific test file
    python run_tests.py --file tests/test_generators.py

    # Run a specific test class or method
    python run_tests.py --filter TestLogGenerator

    # Run with HTML coverage report
    python run_tests.py --cov --html
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ElkInjector Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose test output",
    )
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Enable coverage report",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report (requires --cov)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Run a specific test file (e.g., tests/test_config.py)",
    )
    parser.add_argument(
        "-k", "--filter",
        type=str,
        default=None,
        help="Filter tests by keyword expression (e.g., TestLogGenerator)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Skip the header output",
    )

    args = parser.parse_args()

    # Ensure we are in the project root
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print(f"Error: tests directory not found at {tests_dir}", file=sys.stderr)
        return 1

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Test target
    if args.file:
        cmd.append(args.file)
    else:
        cmd.append(str(tests_dir))

    # Verbose
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-v")
        cmd.append("--tb=short")

    # Coverage
    if args.cov:
        cmd.extend(["--cov=elkinjector", "--cov-report=term-missing"])
        if args.html:
            cmd.append("--cov-report=html:coverage-report")

    # Filter
    if args.filter:
        cmd.extend(["-k", args.filter])

    # Print header
    if not args.no_header:
        print("=" * 60)
        print("  ElkInjector Test Runner")
        print("=" * 60)
        print(f"  Command: {' '.join(cmd)}")
        print(f"  Python:  {sys.version.split()[0]}")
        print("=" * 60)
        print()

    # Run tests
    result = subprocess.run(cmd, cwd=project_root)

    # Summary
    if not args.no_header:
        print()
        if result.returncode == 0:
            print("All tests passed.")
        else:
            print(f"Tests failed (exit code: {result.returncode}).")

        if args.cov and args.html:
            report_path = project_root / "coverage-report" / "index.html"
            print(f"HTML coverage report: {report_path}")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
