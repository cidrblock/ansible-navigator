"""Test the ability to produce a dictionary of effective sources."""

from copy import deepcopy
from pathlib import Path

import pytest

from ansible_navigator.configuration_subsystem import Configurator
from ansible_navigator.configuration_subsystem import Constants as C
from ansible_navigator.configuration_subsystem import NavigatorConfiguration
from ansible_navigator.configuration_subsystem import to_sources
from ansible_navigator.configuration_subsystem.definitions import SettingsFileType
from ansible_navigator.initialization import parse_and_update


def test_defaults() -> None:
    """Check the settings file used as a sample against the schema."""
    settings = deepcopy(NavigatorConfiguration)
    settings.internals.initializing = True
    Configurator(params=[], application_configuration=settings).configure()

    sources = to_sources(settings)
    for path, source in sources.items():
        assert source in [C.AUTO.value, C.DEFAULT_CFG.value, C.NOT_SET.value, C.NONE.value], (
            path,
            source,
        )


def test_cli() -> None:
    """Test the source of effective settings given some cli parameters."""
    settings = deepcopy(NavigatorConfiguration)
    settings.internals.initializing = True

    params = ["images", "--ll", "debug", "--la", "false"]
    _messages, _exit_messages = parse_and_update(params=params, args=settings)
    sources = to_sources(settings)

    assert sources.pop("ansible-navigator.app") == C.USER_CLI.value
    assert sources.pop("ansible-navigator.logging.level") == C.USER_CLI.value
    assert sources.pop("ansible-navigator.logging.append") == C.USER_CLI.value
    for path, source in sources.items():
        assert source in [C.AUTO.value, C.DEFAULT_CFG.value, C.NOT_SET.value, C.NONE.value], (
            path,
            source,
        )


def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the source of effective settings given some environment variables.

    Args:
        monkeypatch: The pytest monkeypatch fixture
    """
    settings = deepcopy(NavigatorConfiguration)
    settings.internals.initializing = True

    prefix = settings.application_name
    monkeypatch.setenv(settings.entry("app").environment_variable(prefix), "images")
    monkeypatch.setenv(settings.entry("log_level").environment_variable(prefix), "debug")
    monkeypatch.setenv(settings.entry("log_append").environment_variable(prefix), "false")

    _messages, _exit_messages = parse_and_update(params=[], args=settings)
    assert not _exit_messages
    sources = to_sources(settings)

    assert sources.pop("ansible-navigator.app") == C.ENVIRONMENT_VARIABLE.value
    assert sources.pop("ansible-navigator.logging.level") == C.ENVIRONMENT_VARIABLE.value
    assert sources.pop("ansible-navigator.logging.append") == C.ENVIRONMENT_VARIABLE.value
    for path, source in sources.items():
        assert source in [C.AUTO.value, C.DEFAULT_CFG.value, C.NOT_SET.value, C.NONE.value], (
            path,
            source,
        )


def test_full(settings_env_var_to_full: tuple[Path, SettingsFileType]) -> None:
    """Test the source of effective settings given a full config.

    Args:
        settings_env_var_to_full: The pytest fixture to provide a full
            config
    """
    settings = deepcopy(NavigatorConfiguration)
    settings.internals.initializing = True
    _messages, _exit_messages = parse_and_update(params=[], args=settings)

    sources = to_sources(settings)
    for path, source in sources.items():
        if path.startswith("settings_file"):
            continue
        assert source in [C.USER_CFG.value, C.AUTO.value], (path, source)
