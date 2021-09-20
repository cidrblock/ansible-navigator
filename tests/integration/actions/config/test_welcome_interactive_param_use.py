""" config from welcome interactive w ee
"""
import pytest

from .base import BaseClass

from ..._interactions import add_indicies
from ..._interactions import Command
from ..._interactions import Step
from ..._interactions import step_id

CLI = Command(execution_environment=False).join()

steps = (
    Step(user_input=CLI, comment="welcome screen"),
    Step(
        user_input=":config --ee False",
        comment="enter config from welcome screen",
        mask=False,
        look_fors=["/home/user/.ansible/plugins/become"],
    ),
    Step(user_input=":back", comment="return to welcome screen"),
    Step(
        user_input=":config --ee True",
        comment="enter config from welcome screen",
        mask=False,
        look_fors=["/home/runner/.ansible/plugins/become"],
    ),
)

steps = add_indicies(steps)


@pytest.mark.parametrize("step", steps, ids=step_id)
class Test(BaseClass):
    """run the tests"""

    UPDATE_FIXTURES = False
