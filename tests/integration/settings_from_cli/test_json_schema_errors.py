"""Check exit messages for json schema validation."""

from __future__ import annotations

import os
import shlex
import subprocess

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests.defaults import FIXTURES_DIR
from tests.defaults import BaseScenario
from tests.defaults import id_func


TEST_FIXTURE_DIR = Path(FIXTURES_DIR) / "unit" / "configuration_subsystem"


@dataclass
class Scenario(BaseScenario):
    """Data for the tests."""

    comment: str
    """The comment for the test"""
    settings_file: Path
    """The settings file path"""
    messages: tuple[str, ...]
    """Messages expected to be found"""

    command: tuple[str, ...] = ("ansible-navigator", "-m", "stdout")
    """The command to run"""

    def __str__(self) -> str:
        """Provide a test id.

        Returns:
            The test id
        """
        return self.comment


test_data = (
    Scenario(
        comment="Empty settings file",
        messages=("Settings file cannot be empty",),
        settings_file=TEST_FIXTURE_DIR / "ansible-navigator_broken.yml",
    ),
    Scenario(
        comment="Unrecognized key",
        messages=("'unknown' was unexpected",),
        settings_file=TEST_FIXTURE_DIR / "ansible-navigator_unknown_key.yml",
    ),
    Scenario(
        comment="Unrecognized app",
        messages=("'non_app' is not one of ['builder',",),
        settings_file=TEST_FIXTURE_DIR / "ansible-navigator_no_app.yml",
    ),
    Scenario(
        comment="EE enabled is not a bool",
        messages=("5 is not one of [True, False]",),
        settings_file=TEST_FIXTURE_DIR / "ansible-navigator_not_bool.yml",
    ),
)


@pytest.mark.parametrize("data", test_data, ids=id_func)
def test(data: Scenario, subtests: Any, tmp_path: Path) -> None:
    """Test for json schema errors.

    Args:
        data: The test data
        tmp_path: The temporary path fixture
        subtests: The pytest subtest fixture

    Raises:
        AssertionError: When tests fails
    """
    assert data.settings_file.exists()
    venv_path = os.environ.get("VIRTUAL_ENV")
    venv_prefix = ""
    if venv_path is not None:
        venv = str(Path(venv_path, "bin", "activate"))
        venv_prefix = f"source {venv} && "
    log_file = tmp_path / "log.txt"

    command = list(data.command) + ["--lf", str(log_file)]

    bash_wrapped = f"/bin/bash -c '{venv_prefix!s}{shlex.join(split_command=command)}'"
    # Some os.environ are required in order to make it work, likely HOME and PATH at least.
    env = os.environ | {"ANSIBLE_NAVIGATOR_CONFIG": str(data.settings_file), "NO_COLOR": "true"}
    proc_out = subprocess.run(
        bash_wrapped,
        check=False,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
    )
    long_stderr = "".join(
        [line.strip(" ").replace("\n", " ") for line in proc_out.stderr.splitlines(keepends=True)],
    )
    for value in data.messages:
        with subtests.test(msg=value, value=value):
            assert value in long_stderr
