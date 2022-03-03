"""check return codes from mode ``stdout``
"""
import os
import subprocess

from pathlib import Path
from typing import List
from typing import NamedTuple
from typing import Tuple

import pytest

from ansible_navigator.utils.functions import shlex_join
from ..defaults import DEFAULT_CONTAINER_IMAGE
from ..defaults import FIXTURES_DIR


PLAYBOOK = os.path.join(FIXTURES_DIR, "integration", "stdout_exit_codes", "site.yml")


@pytest.fixture(name="params")
def fixture_params(request):
    """generate parameters"""
    return {
        "execution_environment": request.param,
        "execution_environment_image": DEFAULT_CONTAINER_IMAGE,
    }


def id_ee(value):
    """generate id"""
    return f"execution_environment={value}"


def id_test_data(value):
    """generate id"""
    return f"action={value.action_name} return={value.return_code}"


class StdoutTest(NamedTuple):
    """Definition of a stdout test."""

    #: The name of the action
    action_name: str
    #: Parameters for the action
    action_params: Tuple[Tuple, ...]
    #: Text to search for
    present: str
    #: Expected return code
    return_code: int
    #: Expected return message
    message: str = ""


fixture_test_data = (
    StdoutTest(
        action_name="config",
        action_params=(("cmdline", ["--help"]),),
        present="usage: ansible-config",
        return_code=0,
    ),
    StdoutTest(
        action_name="config",
        action_params=(("cmdline", ["foo"]),),
        present="invalid choice: 'foo'",
        return_code=2,
    ),
    StdoutTest(
        action_name="doc",
        action_params=(("cmdline", ["--help"]),),
        present="usage: ansible-doc",
        return_code=0,
    ),
    StdoutTest(
        action_name="doc",
        action_params=(("cmdline", ["--json"]),),
        present="Incorrect options passed",
        return_code=5,
    ),
    StdoutTest(
        action_name="inventory",
        action_params=(("cmdline", ["--help"]),),
        present="usage: ansible-inventory",
        return_code=0,
    ),
    StdoutTest(
        action_name="inventory",
        action_params=(("cmdline", ["foo"]),),
        present="No action selected",
        return_code=1,
    ),
    StdoutTest(
        action_name="run",
        action_params=(("playbook", PLAYBOOK), ("playbook_artifact_enable", False)),
        present="success",
        return_code=0,
    ),
    StdoutTest(
        action_name="run",
        action_params=(("playbook", "foo"), ("playbook_artifact_enable", False)),
        present="foo could not be found",
        return_code=1,
    ),
)


@pytest.mark.parametrize("params", (True, False), indirect=["params"], ids=id_ee)
@pytest.mark.parametrize("test_data", fixture_test_data, ids=id_test_data)
def test(action_run_stdout, params, test_data):
    """test for a return code"""
    action_runner = action_run_stdout(action_name=test_data.action_name, **params)
    run_stdout_return, stdout, stderr = action_runner.run_action_stdout(
        **dict(test_data.action_params),
    )
    assert run_stdout_return.return_code == test_data.return_code
    if test_data.return_code == 0:
        assert test_data.present in stdout
        assert test_data.message in run_stdout_return.message
    else:
        std_stream = stdout if params["execution_environment"] else stderr
        assert test_data.present in std_stream
        assert test_data.message in run_stdout_return.message


class StdoutCliTest(NamedTuple):
    """Definition of a stdout cli test."""

    comment: str
    """Description of the test"""
    execution_environment: bool
    """Run in an execution environment"""
    params: List[str]
    """Parameters for the subcommand"""
    playbook_artifact_enable: bool
    """Enable playbook artifact creation"""
    return_code: int
    """Expected return code"""
    stderr_find: List
    """Substring to search for in stderr"""
    stdout_find: List
    """Substring to search for in stdout"""
    subcommand: str
    """The name of the subcommand"""
    mode: str = "stdout"
    """The mode to run in"""

    def __str__(self) -> str:
        """Provide a test id."""
        return self.comment

    @property
    def command(self) -> List[str]:
        """Provide the constructed command"""
        return ["ansible-navigator", self.subcommand] + self.params + ["--mode", self.mode]


# Intentionally not using parametrize so the behavior can be documented
StdoutCliTests = (
    StdoutCliTest(
        comment="run pass/ee/pae",
        execution_environment=True,
        subcommand="run",
        params=[PLAYBOOK],
        playbook_artifact_enable=True,
        return_code=0,
        stderr_find=[],
        stdout_find=["ok=1"],
    ),
    StdoutCliTest(
        comment="run pass/ee/no pae",
        execution_environment=True,
        subcommand="run",
        params=[PLAYBOOK],
        playbook_artifact_enable=False,
        return_code=0,
        stderr_find=[],
        stdout_find=["ok=1"],
    ),
    StdoutCliTest(
        comment="run pass/no ee/pae",
        execution_environment=False,
        subcommand="run",
        params=[PLAYBOOK],
        playbook_artifact_enable=True,
        return_code=0,
        stderr_find=[],
        stdout_find=["ok=1"],
    ),
    StdoutCliTest(
        comment="run pass/no ee/no pae",
        execution_environment=False,
        subcommand="run",
        params=[PLAYBOOK],
        playbook_artifact_enable=False,
        return_code=0,
        stderr_find=[],
        stdout_find=["ok=1"],
    ),
    StdoutCliTest(
        comment="run fail/ee/pae",
        execution_environment=True,
        subcommand="run",
        params=["no_such_playbook.yaml"],
        playbook_artifact_enable=True,
        return_code=1,
        stderr_find=["review the log"],  # navigator writes to stderr
        stdout_find=["could not be found"],  # ee/pae only produces stdout
    ),
    StdoutCliTest(
        comment="run fail/ee/no pae",
        execution_environment=True,
        subcommand="run",
        params=["no_such_playbook.yaml"],
        playbook_artifact_enable=False,
        return_code=1,
        stderr_find=["review the log"],  # navigator writes to stderr
        stdout_find=["could not be found"],  # ee only produces stdout
    ),
    StdoutCliTest(
        comment="run fail/no ee/pae",
        execution_environment=False,
        subcommand="run",
        params=["no_such_playbook.yaml"],
        playbook_artifact_enable=True,
        return_code=1,
        stderr_find=["review the log"],  # navigator writes to stderr
        stdout_find=["could not be found"],  # pae produces stdout
    ),
    StdoutCliTest(
        comment="run fail/no ee/no pae",
        execution_environment=False,
        subcommand="run",
        params=["no_such_playbook.yaml"],
        playbook_artifact_enable=False,
        return_code=1,
        stderr_find=["review the log", "could not be found"],  # ansible/navigator write to stderr
        stdout_find=[],
    ),
)


@pytest.mark.parametrize(argnames="data", argvalues=StdoutCliTests, ids=str)
def test_run_through_cli(
    tmp_path: Path,
    data: StdoutCliTest,
) -> None:
    """Test for a return code from run through a shell.

    :param data: The test data
    :raises AssertionError: When no virtual environment found
    """
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path is None:
        raise AssertionError(
            "VIRTUAL_ENV environment variable was not set but tox should have set it.",
        )
    venv = Path(venv_path, "bin", "activate")
    log_file = str(Path(tmp_path, "log.txt"))
    artifact_file = str(Path(tmp_path, "artifact.json"))

    command = data.command + [
        "--lf",
        log_file,
        "--pae",
        str(data.playbook_artifact_enable),
        "--pas",
        artifact_file,
        "--ee",
        str(data.execution_environment),
    ]
    bash_wrapped = f"/bin/bash -c 'source {venv!s} && {shlex_join(command)}'"
    proc_out = subprocess.run(
        bash_wrapped,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        universal_newlines=True,
        shell=True,
    )
    assert all(find in proc_out.stdout for find in data.stdout_find)
    assert all(find in proc_out.stderr for find in data.stderr_find)
    assert data.return_code == proc_out.returncode
