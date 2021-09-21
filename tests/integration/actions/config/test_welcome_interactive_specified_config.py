""" config from welcome interactive w ee and specified config
"""
import pytest

from .base import CONFIG_FIXTURE
from .base import BaseClass

from ..._interactions import add_indicies
from ..._interactions import Command
from ..._interactions import Step
from ..._interactions import step_id

CLI = Command(execution_environment=False).join()

steps = (
    Step(user_input=CLI, comment="welcome screen"),
    Step(
        user_input=":config",
        comment="enter config from welcome screen (no ee)",
        mask=False,
        look_fors=["YAML_FILENAME_EXTENSIONS", "['.yml', '.yaml', '.json']"],
    ),
    Step(user_input=":back", comment="return to welcome screen"),
    Step(
        user_input=":config -c " + CONFIG_FIXTURE,
        comment="enter config from welcome screen, custom config, (no ee)",
        mask=False,
        look_fors=["YAML_FILENAME_EXTENSIONS", "['.yahmool']"],
    ),
)

steps = add_indicies(steps)


@pytest.mark.parametrize("step", steps, ids=step_id)
class Test(BaseClass):
    """run the tests"""

    PANE_HEIGHT = 300
    UPDATE_FIXTURES = False
