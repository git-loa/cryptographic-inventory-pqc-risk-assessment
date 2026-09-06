"""
Model Tester Module
"""

from __future__ import annotations

import time
import traceback
from typing import Callable, Any, Optional


class ModelTester:
    """
    A reusable testing harness for any module or function.

    Features:
    - Timing for each test
    - PASS/FAIL tracking
    - Exception capture with tracebacks
    - Optional expected-value comparison
    - Clean summary reporting
    - Works across all projects (TLS, PQC, math, tooling, etc.)
    """

    def __init__(self, name: str):
        self.name = name
        self.results: list[dict[str, Any]] = []

    def run_test(
        self,
        test_name: str,
        func: Callable[..., Any],
        *args,
        expected: Optional[Any] = None,
        **kwargs,
    ) -> None:
        """
        Run a single test case with timing and structured reporting.

        Parameters
        ----------
        test_name : str
            Name of the test case.
        func : Callable
            Function to test.
        expected : Any, optional
            Expected output. If None, PASS means no exception.
        *args, **kwargs :
            Arguments passed to the function.
        """
        start = time.perf_counter()

        try:
            output = func(*args, **kwargs)
            duration = round(time.perf_counter() - start, 4)

            passed = expected is None or output == expected

            self.results.append(
                {
                    "test": test_name,
                    "passed": passed,
                    "duration": duration,
                    "output": output,
                    "expected": expected,
                }
            )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            duration = round(time.perf_counter() - start, 4)
            self.results.append(
                {
                    "test": test_name,
                    "passed": False,
                    "duration": duration,
                    "error": str(exc),
                    "trace": traceback.format_exc(),
                }
            )

    def summary(self) -> None:
        """
        Print a clean summary of all test results.
        """
        print(f"\n=== Test Summary: {self.name} ===")
        for r in self.results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"- {r['test']}: {status} ({r['duration']}s)")
        print("====================================\n")
