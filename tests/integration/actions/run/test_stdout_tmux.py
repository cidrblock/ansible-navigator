"""Tests for run from CLI, stdout."""

import pytest

from tests.integration._interactions import Command
from tests.integration._interactions import SearchFor
from tests.integration._interactions import UiTestStep
from tests.integration._interactions import add_indices

from .base import BaseClass
from .base import inventory_path
from .base import playbook_path
from .base import run_fixture_dir


class StdoutCommand(Command):
    """A stdout command."""

    subcommand = "run"
    preclear = True


class ShellCommand(UiTestStep):
    """A shell command."""

    search_within_response = SearchFor.PROMPT


stdout_tests = (
    ShellCommand(
        comment="run playbook with ee",
        user_input=StdoutCommand(
            cmdline=f"{playbook_path} -i {inventory_path} --pae false",
            mode="stdout",
            execution_environment=True,
        ).join(),
        present=["TASK [debug print play-3 task-2]", "ok=6", "failed=0"],
    ),
    ShellCommand(
        comment="run playbook without ee",
        user_input=StdoutCommand(
            cmdline=f"{playbook_path} -i {inventory_path} --pae false",
            mode="stdout",
            execution_environment=False,
        ).join(),
        present=["TASK [debug print play-3 task-2]", "ok=6", "failed=0"],
    ),
    ShellCommand(
        comment="playbook help with ee",
        user_input=StdoutCommand(
            cmdline="--help-playbook",
            mode="stdout",
            execution_environment=True,
        ).join(),
        present=["usage: ansible-playbook [-h]"],
    ),
    ShellCommand(
        comment="playbook help without ee",
        user_input=StdoutCommand(
            cmdline="--help-playbook",
            mode="stdout",
            execution_environment=False,
        ).join(),
        present=["usage: ansible-playbook [-h]"],
    ),
    ShellCommand(
        comment="run help-playbook with interactive with ee",
        user_input=StdoutCommand(
            cmdline="--help-playbook",
            mode="interactive",
            execution_environment=True,
        ).join(),
        present=["usage: ansible-playbook [-h]"],
    ),
    ShellCommand(
        comment="run help-playbook with interactive without ee",
        user_input=StdoutCommand(
            cmdline="--help-playbook",
            mode="interactive",
            execution_environment=False,
        ).join(),
        present=["usage: ansible-playbook [-h]"],
    ),
    ShellCommand(
        comment="run playbook with inventory from ansible.cfg without ee",
        user_input=StdoutCommand(
            cmdline="site.yml",
            execution_environment=False,
            mode="stdout",
            precommand=f"cd {run_fixture_dir}/using_ansible_cfg && ",
        ).join(),
        present=["from.ansible.cfg", "ok=1"],
    ),
    ShellCommand(
        comment="run playbook with inventory from ansible.cfg with ee",
        user_input=StdoutCommand(
            cmdline="site.yml",
            execution_environment=True,
            mode="stdout",
            precommand=f"cd {run_fixture_dir}/using_ansible_cfg && ",
        ).join(),
        present=["from.ansible.cfg", "ok=1"],
    ),
    UiTestStep(
        comment="run playbook with enable-prompts and show prompting",
        user_input=StdoutCommand(
            cmdline=f"{playbook_path} -k --enable-prompts",
            execution_environment=True,
        ).join(),
        present=["password:"],
        search_within_response="SSH password:",
    ),
    ShellCommand(
        comment="run playbook with enable-prompts",
        user_input=StdoutCommand(
            cmdline=f"{playbook_path} -i {inventory_path} --enable-prompts",
            mode="stdout",
            execution_environment=True,
        ).join(),
        present=["TASK [debug print play-3 task-2]", "ok=6", "failed=0"],
    ),
)

steps = add_indices(stdout_tests)


def step_id(value: ShellCommand) -> str:
    """Return the test id from the test step object.

    Args:
        value: The parameterized value from which the id will be
            generated

    Returns:
        A formatted id for the test
    """
    return f"{value.step_index}"


@pytest.mark.parametrize("step", steps, ids=step_id)
class Test(BaseClass):
    """Run the tests for run from CLI, stdout."""

    UPDATE_FIXTURES = False
