#!/usr/bin/env python3
"""
Token Checker - Utility for TCC Token Management

Provides utilities for checking token usage and enforcing thresholds.
Used by TCC to prevent mid-step cycle termination.

Module Size Target: <200 lines (Current: ~150 lines)
"""

import sys
import json
from pathlib import Path
from typing import Tuple, Optional

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))


class TokenChecker:
    """
    Token usage checker for cycle management.

    Helps TCC make decisions about whether to start new steps
    based on current token usage relative to threshold.
    """

    def __init__(self, token_budget: int = 200000, max_token_percent: int = 35):
        """
        Initialize token checker.

        Args:
            token_budget: Maximum tokens available (default: 200K)
            max_token_percent: Maximum percentage before stopping (default: 35%)
        """
        self.token_budget = token_budget
        self.max_token_percent = max_token_percent
        self.threshold_tokens = int((max_token_percent / 100) * token_budget)

    def can_start_step(self, current_tokens: int) -> Tuple[bool, float, str]:
        """
        Check if there's enough token budget to start a new step.

        Args:
            current_tokens: Current token usage

        Returns:
            Tuple of (can_proceed, current_percent, message)
        """
        current_percent = (current_tokens / self.token_budget) * 100

        if current_percent > self.max_token_percent:
            message = (
                f"❌ Token threshold exceeded: {current_percent:.1f}% "
                f"(max: {self.max_token_percent}%) - "
                f"{current_tokens:,}/{self.threshold_tokens:,} tokens"
            )
            return False, current_percent, message
        else:
            remaining_percent = self.max_token_percent - current_percent
            message = (
                f"✅ Token budget OK: {current_percent:.1f}% "
                f"(remaining: {remaining_percent:.1f}%) - "
                f"{current_tokens:,}/{self.threshold_tokens:,} tokens"
            )
            return True, current_percent, message

    def format_status_report(
        self,
        step_number: int,
        current_tokens: int,
        status_ok: bool = True,
        updated_and_pushed: bool = True
    ) -> str:
        """
        Format standardized step completion report.

        Args:
            step_number: Step that was completed
            current_tokens: Current token usage
            status_ok: Whether step completed successfully
            updated_and_pushed: Whether status was updated and changes pushed

        Returns:
            Formatted status string for monitor
        """
        current_percent = (current_tokens / self.token_budget) * 100
        status = "OK" if status_ok else "NOK"
        action = "updated & pushed" if updated_and_pushed else "not committed"

        return f"Step {step_number} completed: Tokens: {current_percent:.1f}%; Status: {status}, {action}"

    def get_cycle_close_message(self, cycle_number: int, current_tokens: int, reason: Optional[str] = None) -> str:
        """
        Generate cycle close message with token information.

        Args:
            cycle_number: Current cycle number
            current_tokens: Current token usage
            reason: Optional custom reason

        Returns:
            Formatted cycle close message
        """
        current_percent = (current_tokens / self.token_budget) * 100

        if reason:
            return f"Cycle {cycle_number} closed: {reason} (tokens: {current_percent:.1f}%)"
        else:
            return f"Cycle {cycle_number} closed: Token threshold exceeded: {current_percent:.1f}%"


# Convenience functions for CLI usage

def check_tokens(current_tokens: int, threshold_percent: int = 35, budget: int = 200000) -> dict:
    """
    CLI-friendly token checking function.

    Args:
        current_tokens: Current token count
        threshold_percent: Maximum percentage (default: 35%)
        budget: Token budget (default: 200K)

    Returns:
        Dict with check results
    """
    checker = TokenChecker(token_budget=budget, max_token_percent=threshold_percent)
    can_proceed, current_percent, message = checker.can_start_step(current_tokens)

    return {
        'can_proceed': can_proceed,
        'current_tokens': current_tokens,
        'current_percent': round(current_percent, 1),
        'threshold_percent': threshold_percent,
        'threshold_tokens': checker.threshold_tokens,
        'message': message
    }


def main():
    """CLI interface for token checking."""
    import argparse

    parser = argparse.ArgumentParser(description="Token Checker - Check if step can start")
    parser.add_argument("tokens", type=int, help="Current token count")
    parser.add_argument("--threshold", type=int, default=35, help="Threshold percentage (default: 35)")
    parser.add_argument("--budget", type=int, default=200000, help="Token budget (default: 200000)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = check_tokens(args.tokens, args.threshold, args.budget)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result['message'])
        if not result['can_proceed']:
            sys.exit(1)  # Exit with error if threshold exceeded

    return 0 if result['can_proceed'] else 1


if __name__ == "__main__":
    sys.exit(main())
