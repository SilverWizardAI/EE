#!/usr/bin/env python
"""
Test Runner for PyQt6 App Template

Runs different test suites based on command-line arguments.

Usage:
    python run_tests.py              # Run unit tests only
    python run_tests.py --all        # Run all tests (unit + integration)
    python run_tests.py --integration  # Run integration tests only
    python run_tests.py --coverage   # Run with coverage report
"""

import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run PyQt6 App Template tests")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (unit + integration)"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only (requires MM proxy running)"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Build pytest arguments
    pytest_args = [str(Path(__file__).parent)]

    if args.integration:
        pytest_args.extend(["-m", "integration"])
    elif not args.all:
        # Default: run unit tests only (exclude integration)
        pytest_args.extend(["-m", "not integration"])

    if args.coverage:
        pytest_args.extend(["--cov=.", "--cov-report=term", "--cov-report=html"])

    if args.verbose:
        pytest_args.append("-vv")

    # Import pytest and run
    try:
        import pytest
    except ImportError:
        print("ERROR: pytest not installed. Install with:")
        print("  uv pip install pytest pytest-qt")
        return 1

    print("=" * 70)
    print("PyQt6 App Template - Test Suite")
    print("=" * 70)

    if args.integration:
        print("Running: Integration tests (requires MM proxy on port 6001)")
    elif args.all:
        print("Running: All tests (unit + integration)")
    else:
        print("Running: Unit tests only")

    print("=" * 70)
    print()

    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
