"""Tests for ``settings`` from CLI, stdout."""
import pytest

from ..._interactions import Command
from ..._interactions import SearchFor
from ..._interactions import Step
from ..._interactions import add_indices
from .base import BaseClass


class StdoutCommand(Command):
    """stdout command"""

    subcommand = "settings"
    preclear = True


class ShellCommand(Step):
    """a shell command"""

    search_within_response = SearchFor.PROMPT


stdout_tests = (
    ShellCommand(
        comment="print settings to stdout with ee",
        user_input=StdoutCommand(
            cmdline="settings",
            mode="stdout",
            execution_environment=True,
        ).join(),
        look_fors=["name: set_environment_variable"],
    ),
    ShellCommand(
        comment="print settings to stdout with no ee",
        user_input=StdoutCommand(
            cmdline="settings",
            mode="stdout",
            execution_environment=False,
        ).join(),
        look_fors=["name: set_environment_variable"],
    ),
    ShellCommand(  # needs work
        comment="print settings to stdout with no ee",
        user_input=StdoutCommand(
            cmdline="settings",
            mode="interactive",
            execution_environment=True,
        ).join(),
        look_fors=["name: set_environment_variable"],
    ),
    ShellCommand(  # needs work
        comment="print settings to stdout with no ee",
        user_input=StdoutCommand(
            cmdline="settings",
            mode="interactive",
            execution_environment=False,
        ).join(),
        look_fors=["name: set_environment_variable"],
    ),
)

steps = add_indices(stdout_tests)


def step_id(value):
    """return the test id from the test step object"""
    return f"{value.comment}  {value.user_input}"


@pytest.mark.parametrize("step", steps, ids=step_id)
class Test(BaseClass):
    """Run the tests for ``config`` from CLI, mode stdout."""

    UPDATE_FIXTURES = True
