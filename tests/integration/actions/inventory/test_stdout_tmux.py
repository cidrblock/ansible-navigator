"""Tests for inventory from CLI, stdout."""

import pytest

from tests.integration._interactions import Command
from tests.integration._interactions import SearchFor
from tests.integration._interactions import UiTestStep
from tests.integration._interactions import add_indices

from .base import ANSIBLE_INVENTORY_FIXTURE_DIR
from .base import BaseClass


class StdoutCommand(Command):
    """A stdout command."""

    subcommand = "inventory"
    preclear = True


class ShellCommand(UiTestStep):
    """A shell command."""

    search_within_response = SearchFor.PROMPT


stdout_tests = (
    ShellCommand(
        comment="inventory list with ee",
        user_input=StdoutCommand(
            cmdline=f"--list -i {ANSIBLE_INVENTORY_FIXTURE_DIR}",
            mode="stdout",
            execution_environment=True,
        ).join(),
        present=["_meta", "group03"],
    ),
    ShellCommand(
        comment="inventory list without ee",
        user_input=StdoutCommand(
            cmdline=f"--list -i {ANSIBLE_INVENTORY_FIXTURE_DIR}",
            mode="stdout",
            execution_environment=False,
        ).join(),
        present=["_meta", "group03"],
    ),
    ShellCommand(
        comment="inventory help with ee",
        user_input=StdoutCommand(
            cmdline="--help-inventory",
            mode="stdout",
            execution_environment=True,
        ).join(),
        present=["usage: ansible-inventory [-h]"],
    ),
    ShellCommand(
        comment="inventory help without ee",
        user_input=StdoutCommand(
            cmdline="--help-inventory",
            mode="stdout",
            execution_environment=False,
        ).join(),
        present=["usage: ansible-inventory [-h]"],
    ),
    ShellCommand(
        comment="inventory help-inventory with interactive with ee",
        user_input=StdoutCommand(
            cmdline="--help-inventory",
            mode="interactive",
            execution_environment=True,
        ).join(),
        present=["usage: ansible-inventory [-h]"],
    ),
    ShellCommand(
        comment="inventory help-inventory with interactive without ee",
        user_input=StdoutCommand(
            cmdline="--help-inventory",
            mode="interactive",
            execution_environment=False,
        ).join(),
        present=["usage: ansible-inventory [-h]"],
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
    """Run the tests for inventory from CLI, stdout."""

    UPDATE_FIXTURES = False
