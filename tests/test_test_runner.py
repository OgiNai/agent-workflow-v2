"""Integration tests for the generated candidate pytest runner."""

import pytest

from apps.tools.test_runner import run_pytest_for_code


@pytest.mark.anyio
async def test_run_pytest_for_code_passes() -> None:
    code = """
def add(a: int, b: int) -> int:
    return a + b
"""

    tests = """
from solution import add


def test_add():
    assert add(1, 2) == 3


def test_add_negative_numbers():
    assert add(-1, -2) == -3
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.tests_total == 2
    assert result.tests_passed == 2
    assert result.tests_failed == 0
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 0
    assert len(result.tests) == 2
    assert all(test.outcome == "passed" for test in result.tests)


@pytest.mark.anyio
async def test_run_pytest_for_code_fails() -> None:
    code = """
def add(a: int, b: int) -> int:
    return a - b
"""

    tests = """
from solution import add


def test_add():
    assert add(1, 2) == 3


def test_add_negative_numbers():
    assert add(-1, -2) == -3
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "failed"
    assert result.exit_code != 0
    assert result.tests_total == 2
    assert result.tests_passed == 0
    assert result.tests_failed == 2
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 0
    assert len(result.tests) == 2

    assert all(test.outcome == "failed" for test in result.tests)
    assert all(test.failure_message is not None for test in result.tests)


@pytest.mark.anyio
async def test_run_pytest_for_code_handles_skipped_test() -> None:
    code = """
def add(a: int, b: int) -> int:
    return a + b
"""

    tests = """
import pytest

from solution import add


def test_add():
    assert add(1, 2) == 3


@pytest.mark.skip(reason="Demonstrating skipped candidate test")
def test_skipped():
    assert add(1, 2) == 999
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.tests_total == 2
    assert result.tests_passed == 1
    assert result.tests_failed == 0
    assert result.tests_skipped == 1
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 0

    outcomes = {test.nodeid: test.outcome for test in result.tests}

    assert outcomes["test_solution.py::test_add"] == "passed"
    assert outcomes["test_solution.py::test_skipped"] == "skipped"


@pytest.mark.anyio
async def test_run_pytest_for_code_handles_xfailed_test() -> None:
    code = """
def add(a: int, b: int) -> int:
    return a - b
"""

    tests = """
import pytest

from solution import add


@pytest.mark.xfail(reason="Known incorrect candidate implementation")
def test_expected_failure():
    assert add(1, 2) == 3
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.tests_total == 1
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 1
    assert result.tests_xpassed == 0

    assert len(result.tests) == 1
    assert result.tests[0].outcome == "xfailed"


@pytest.mark.anyio
async def test_run_pytest_for_code_handles_xpassed_test() -> None:
    code = """
def add(a: int, b: int) -> int:
    return a + b
"""

    tests = """
import pytest

from solution import add


@pytest.mark.xfail(reason="Expected to fail, but candidate is correct")
def test_unexpected_pass():
    assert add(1, 2) == 3
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.tests_total == 1
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 1

    assert len(result.tests) == 1
    assert result.tests[0].outcome == "xpassed"


@pytest.mark.anyio
async def test_run_pytest_for_code_handles_syntax_error() -> None:
    code = """
def add(a: int, b: int) -> int
    return a + b
"""

    tests = """
from solution import add


def test_add():
    assert add(1, 2) == 3
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "failed"
    assert result.exit_code != 0
    assert result.tests_total == 0
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 0
    assert result.tests == []

    assert "SyntaxError" in result.stdout


@pytest.mark.anyio
async def test_run_pytest_for_code_times_out() -> None:
    code = """
def infinite_loop():
    while True:
        pass
"""

    tests = """
from solution import infinite_loop


def test_infinite_loop():
    infinite_loop()
"""

    result = await run_pytest_for_code(
        code,
        tests,
        timeout_seconds=1,
    )

    assert result.status == "timeout"
    assert result.tests_total == 0
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 0
    assert result.tests == []
