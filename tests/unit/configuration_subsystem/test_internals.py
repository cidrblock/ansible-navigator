"""Test the internals of a NavigatorConfiguration"""

import os

from copy import deepcopy

from .defaults import TEST_FIXTURE_DIR

from ansible_navigator.configuration_subsystem import Constants
from ansible_navigator.configuration_subsystem import NavigatorConfiguration
from ansible_navigator.initialization import parse_and_update


def test_settings_file_path_file_none(monkeypatch):
    """Confirm a settings file path is not stored in the internals when not present."""
    args = deepcopy(NavigatorConfiguration)
    _messages, _exit_messages = parse_and_update(params=[], args=args, initial=True)
    assert args.internals.settings_file_path is None
    assert args.internals.settings_source == Constants.NONE


def test_settings_file_path_file_system(monkeypatch):
    """Confirm a settings file path is stored in the internals when searched."""
    settings_file = "ansible-navigator.yml"
    settings_file_path = os.path.join(TEST_FIXTURE_DIR, settings_file)
    args = deepcopy(NavigatorConfiguration)

    def getcwd():
        return TEST_FIXTURE_DIR

    monkeypatch.setattr(os, "getcwd", getcwd)

    _messages, _exit_messages = parse_and_update(params=[], args=args, initial=True)
    assert args.internals.settings_file_path == settings_file_path
    assert args.internals.settings_source == Constants.SEARCH_PATH


def test_settings_file_path_environment_variable(monkeypatch):
    """Confirm a settings file path is stored in the internals when set via environment variable."""
    settings_file = "ansible-navigator.yml"
    settings_file_path = os.path.join(TEST_FIXTURE_DIR, settings_file)
    monkeypatch.setenv("ANSIBLE_NAVIGATOR_CONFIG", settings_file_path)
    args = deepcopy(NavigatorConfiguration)
    _messages, _exit_messages = parse_and_update(params=[], args=args, initial=True)
    assert args.internals.settings_file_path == settings_file_path
    assert args.internals.settings_source == Constants.ENVIRONMENT_VARIABLE
