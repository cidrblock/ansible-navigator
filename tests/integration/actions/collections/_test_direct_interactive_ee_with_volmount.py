"""Tests for collections from CLI, interactive, with an EE.
"""
import pytest

from ..._interactions import Command
from ..._interactions import UiTestStep
from ..._interactions import add_indices
from ..._interactions import step_id_padded
from .base import BaseClass
from .base import base_steps


CLI = Command(
    precommand="cd /tmp &&",
    raw_append=(
        "--eev $ANSIBLE_COLLECTIONS_PATH/collections:/tmp/collections_to_volmount:Z"
        " --senv ANSIBLE_COLLECTIONS_PATH=/tmp/collections_to_volmount"
    ),
    subcommand="collections",
    execution_environment=True,
).join()


initial_steps = (UiTestStep(user_input=CLI, comment="ansible-navigator collections top window"),)

steps = add_indices(initial_steps + base_steps)


@pytest.mark.parametrize("step", steps, ids=step_id_padded)
class Test(BaseClass):
    """Run the tests for ``collections`` from CLI, interactive, with an EE."""

    update_fixtures = False
