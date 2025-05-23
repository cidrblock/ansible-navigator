"""Tests for the playbook artifact save as post processor."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import pytest

from ansible_navigator.configuration_subsystem import Constants as C
from ansible_navigator.configuration_subsystem import NavigatorConfiguration
from ansible_navigator.configuration_subsystem.navigator_post_processor import (
    NavigatorPostProcessor,
)
from tests.defaults import BaseScenario
from tests.defaults import id_func


@dataclass
class Scenario(BaseScenario):
    """Data structure for PAS post processor tests."""

    name: str
    current: str | None = None
    expected: str | None = None
    exit_message_substr: str = ""

    def __post_init__(self) -> None:
        """Set the expected if errors are expected."""
        if self.expected is None:
            self.expected = self.current

    def __str__(self) -> str:
        """Provide a test id.

        Returns:
            The test id
        """
        return f"{self.current}"


test_data = (
    Scenario(
        name="0",
        expected="{playbook_dir}/{playbook_name}-artifact-{time_stamp}.json",
    ),
    Scenario(
        name="1",
        current="/tmp/artifact.json",
    ),
    Scenario(
        name="2",
        current="{playbook_dir}/{playbook_name}-artifact-{ts_utc}.json",
        exit_message_substr=(
            "The playbook artifact file name"
            " '{playbook_dir}/{playbook_name}-artifact-{ts_utc}.json', set by command line,"
            " has unrecognized variables: 'ts_utc'"
        ),
    ),
    Scenario(
        name="3",
        current="{name}.json",
        exit_message_substr=(
            "The playbook artifact file name"
            " '{name}.json', set by command line,"
            " has unrecognized variables: 'name'"
        ),
    ),
)


@pytest.mark.parametrize(argnames="data", argvalues=test_data, ids=id_func)
def test_pas(data: Scenario) -> None:
    """Test the PAS post processor.

    Args:
        data: The test data
    """
    settings = deepcopy(NavigatorConfiguration)
    entry = settings.entry("playbook_artifact_save_as")

    if data.current is None:
        entry.value.current = entry.value.default
    else:
        entry.value.current = data.current
    entry.value.source = C.USER_CLI

    _messages, exit_messages = NavigatorPostProcessor().playbook_artifact_save_as(
        entry=entry,
        config=settings,
    )
    assert entry.value.current == data.expected

    if data.exit_message_substr:
        assert data.exit_message_substr in exit_messages[0].message
