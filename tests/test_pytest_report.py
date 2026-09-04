"""Tests for structured pytest JSON report parsing."""

from apps.tools.pytest_report import parse_pytest_json_report


def test_parse_passing_tests() -> None:
    report = {
        "summary": {
            "total": 2,
            "passed": 2,
        },
        "tests": [
            {
                "nodeid": "test_solution.py::test_add",
                "outcome": "passed",
                "call": {
                    "duration": 0.0012,
                    "outcome": "passed",
                },
            },
            {
                "nodeid": "test_solution.py::test_subtract",
                "outcome": "passed",
                "call": {
                    "duration": 0.0023,
                    "outcome": "passed",
                },
            },
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=50,
        exit_code=0,
    )

    assert result.status == "passed"
    assert result.tests_total == 2
    assert result.tests_passed == 2
    assert result.tests_failed == 0
    assert result.tests_skipped == 0
    assert result.tests_xfailed == 0
    assert result.tests_xpassed == 0
    assert len(result.tests) == 2

    assert result.tests[0].nodeid == "test_solution.py::test_add"
    assert result.tests[0].outcome == "passed"
    assert result.tests[0].duration_ms == 1


def test_parse_failed_test_with_failure_details() -> None:
    report = {
        "summary": {
            "total": 1,
            "failed": 1,
        },
        "tests": [
            {
                "nodeid": "test_solution.py::test_add",
                "outcome": "failed",
                "call": {
                    "duration": 0.004,
                    "outcome": "failed",
                    "longrepr": "assert add(1, 2) == 4",
                    "traceback": [
                        {
                            "path": "test_solution.py",
                            "lineno": 10,
                            "message": "assert add(1, 2) == 4",
                        }
                    ],
                },
            }
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=20,
        exit_code=1,
    )

    assert result.status == "failed"
    assert result.tests_total == 1
    assert result.tests_passed == 0
    assert result.tests_failed == 1

    test = result.tests[0]

    assert test.nodeid == "test_solution.py::test_add"
    assert test.outcome == "failed"
    assert test.duration_ms == 4
    assert test.failure_message == "assert add(1, 2) == 4"
    assert test.traceback == ("test_solution.py:10: assert add(1, 2) == 4")


def test_parse_skipped_xfailed_and_xpassed_tests() -> None:
    report = {
        "summary": {
            "total": 3,
            "skipped": 1,
            "xfailed": 1,
            "xpassed": 1,
        },
        "tests": [
            {
                "nodeid": "test_solution.py::test_skip",
                "outcome": "skipped",
                "call": {
                    "duration": 0.001,
                    "outcome": "skipped",
                },
            },
            {
                "nodeid": "test_solution.py::test_expected_failure",
                "outcome": "xfailed",
                "call": {
                    "duration": 0.002,
                    "outcome": "xfailed",
                },
            },
            {
                "nodeid": "test_solution.py::test_unexpected_pass",
                "outcome": "xpassed",
                "call": {
                    "duration": 0.003,
                    "outcome": "xpassed",
                },
            },
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=30,
        exit_code=0,
    )

    assert result.status == "passed"
    assert result.tests_total == 3
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.tests_skipped == 1
    assert result.tests_xfailed == 1
    assert result.tests_xpassed == 1

    assert [test.outcome for test in result.tests] == [
        "skipped",
        "xfailed",
        "xpassed",
    ]


def test_parse_execution_error() -> None:
    report = {
        "summary": {
            "total": 1,
            "error": 1,
        },
        "tests": [
            {
                "nodeid": "test_solution.py::test_broken_fixture",
                "outcome": "error",
                "setup": {
                    "duration": 0.001,
                    "outcome": "failed",
                    "longrepr": "fixture setup failed",
                },
            }
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=15,
        exit_code=1,
    )

    assert result.status == "failed"
    assert result.tests_total == 1
    assert result.tests_failed == 0
    assert result.tests == []


def test_parse_collection_failure_without_tests() -> None:
    report = {
        "summary": {
            "total": 0,
        },
        "tests": [],
        "collectors": [
            {
                "nodeid": "test_solution.py",
                "outcome": "failed",
                "result": [],
                "longrepr": "SyntaxError: invalid syntax",
            }
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=10,
        exit_code=2,
        stdout="no tests collected",
        stderr="SyntaxError: invalid syntax",
    )

    assert result.status == "failed"
    assert result.tests_total == 0
    assert result.tests == []
    assert result.stdout == "no tests collected"
    assert result.stderr == "SyntaxError: invalid syntax"


def test_parse_preserves_stdout_and_stderr() -> None:
    report = {
        "summary": {
            "total": 1,
            "passed": 1,
        },
        "tests": [
            {
                "nodeid": "test_solution.py::test_output",
                "outcome": "passed",
                "call": {
                    "duration": 0.001,
                    "outcome": "passed",
                },
            }
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=25,
        exit_code=0,
        stdout="pytest stdout",
        stderr="pytest stderr",
    )

    assert result.stdout == "pytest stdout"
    assert result.stderr == "pytest stderr"


def test_parse_rejects_missing_summary() -> None:
    report = {
        "tests": [],
    }

    try:
        parse_pytest_json_report(
            report,
            duration_ms=10,
            exit_code=0,
        )
    except TypeError as exc:
        assert str(exc) == "Pytest JSON report is missing a valid summary."
    else:
        raise AssertionError("Expected ValueError")


def test_parse_sums_test_stage_durations() -> None:
    report = {
        "summary": {
            "total": 1,
            "passed": 1,
        },
        "tests": [
            {
                "nodeid": "test_solution.py::test_stages",
                "outcome": "passed",
                "setup": {
                    "duration": 0.001,
                    "outcome": "passed",
                },
                "call": {
                    "duration": 0.002,
                    "outcome": "passed",
                },
                "teardown": {
                    "duration": 0.003,
                    "outcome": "passed",
                },
            }
        ],
    }

    result = parse_pytest_json_report(
        report,
        duration_ms=10,
        exit_code=0,
    )

    assert result.tests[0].duration_ms == 6
