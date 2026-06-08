"""Unit tests for the start/stop reserved CLI commands."""

import subprocess
import sys
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from taggly.cli import _kill, _spawn, _PID_FILE, build_cli
from taggly.registry import discover_commands

RUNNER = CliRunner()
CLI = build_cli(discover_commands())


@pytest.fixture(autouse=True)
def clean_pid():
    """Remove any leftover PID file before and after each test."""
    _PID_FILE.unlink(missing_ok=True)
    yield
    if _PID_FILE.exists():
        try:
            _kill(int(_PID_FILE.read_text().strip()))
        except (OSError, subprocess.CalledProcessError):
            pass
        _PID_FILE.unlink(missing_ok=True)


def _dummy() -> subprocess.Popen:
    """Spawn a long-running dummy process suitable for kill/stop tests."""
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# --- _kill / _spawn helpers ---

def test_kill_terminates_process():
    """_kill terminates a running process within 5 seconds."""
    proc = _dummy()
    _kill(proc.pid)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail("_kill did not terminate the process within 5 seconds")
    assert proc.returncode is not None


def test_spawn_returns_running_process():
    """_spawn returns a Popen handle whose process is alive after creation."""
    proc = _spawn([sys.executable, "-c", "import time; time.sleep(60)"], {})
    assert proc.pid > 0
    assert proc.poll() is None  # still running
    _kill(proc.pid)
    proc.wait(timeout=5)


# --- start command ---

def test_start_creates_pid():
    """start writes .taggly.pid with a valid process id and exits 0."""
    result = RUNNER.invoke(CLI, ["start"])
    assert result.exit_code == 0, result.output
    assert _PID_FILE.exists()
    assert int(_PID_FILE.read_text().strip()) > 0


def test_start_blocked_when_running():
    """start fails when .taggly.pid already exists."""
    _PID_FILE.write_text("1")
    result = RUNNER.invoke(CLI, ["start"])
    assert result.exit_code != 0
    assert "already running" in result.output.lower()


# --- stop command ---

def test_stop_kills_process():
    """stop terminates the process referenced by .taggly.pid and removes the file."""
    proc = _dummy()
    _PID_FILE.write_text(str(proc.pid))

    result = RUNNER.invoke(CLI, ["stop"])

    assert result.exit_code == 0, result.output
    assert not _PID_FILE.exists()
    assert "stopped" in result.output
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail("stop did not terminate the process within 5 seconds")


def test_stop_no_server():
    """stop exits with an error when .taggly.pid is absent."""
    result = RUNNER.invoke(CLI, ["stop"])
    assert result.exit_code != 0
    assert "no running server" in result.output.lower()


def test_stop_stale_pid():
    """stop cleans up .taggly.pid when the referenced process no longer exists."""
    _PID_FILE.write_text("12345")
    with patch("taggly.cli._kill", side_effect=OSError("No such process")):
        result = RUNNER.invoke(CLI, ["stop"])
    assert result.exit_code == 0, result.output
    assert not _PID_FILE.exists()
    assert "not found" in result.output.lower()
