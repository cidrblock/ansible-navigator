"""Tests for ``settings`` from welcome, interactive, with an EE.
"""
import pytest

from ..._interactions import Command
from ..._interactions import Step
from ..._interactions import add_indices
from ..._interactions import step_id
from .base import BaseClass
from .base import base_steps


CLI = Command(execution_environment=True).join()

initial_steps = (
    Step(user_input=CLI, comment="welcome screen"),
    Step(user_input=":settings", comment="enter settings from welcome screen"),
)

steps = add_indices(initial_steps + base_steps)


@pytest.mark.parametrize("step", steps, ids=step_id)
class Test(BaseClass):
    """Run the tests for ``settings`` from welcome, interactive, with an EE."""

    UPDATE_FIXTURES = True
