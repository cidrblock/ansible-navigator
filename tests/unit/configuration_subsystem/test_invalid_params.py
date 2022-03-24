"""Some test using invalid parameters
"""
import tempfile

# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-872
from unittest.mock import patch

import pytest

from ansible_navigator.configuration_subsystem import NavigatorConfiguration
from ansible_navigator.utils.functions import ExitMessage
from .utils import id_for_name


def test_generate_argparse_error(generate_config):
    """Ensure exit_messages generated by argparse are caught"""
    params = "Sentinel"
    response = generate_config(params=params.split())
    assert len(response.exit_messages) == 2
    exit_msg = "invalid choice: 'Sentinel'"
    assert exit_msg in response.exit_messages[1].message


@patch("shutil.which", return_value="/path/to/container_engine")
def test_inventory_no_inventory(_mocked_func, generate_config):
    """Ensure exit_messages generated for an inventory without an inventory specified"""
    response = generate_config(params=["inventory"])
    exit_msg = "An inventory is required when using the inventory subcommand"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


@patch(
    "ansible_navigator.configuration_subsystem.navigator_post_processor.check_for_ansible",
    return_value=([], [ExitMessage(message="no_ansible")]),
)
def test_ee_false_no_ansible(_mocked_func, generate_config):
    """Ensure an error is created if EE is false and ansible not present"""
    response = generate_config(params=["--ee", "false"])
    assert "no_ansible" in [exit_msg.message for exit_msg in response.exit_messages]


@patch("shutil.which", return_value=None)
def test_no_container_engine(_mocked_func, generate_config):
    """Ensure an error is created if EE is false and ansible not present"""
    response = generate_config()
    expected = "No container engine could be found"
    assert any(
        expected in exit_msg.message for exit_msg in response.exit_messages
    ), response.exit_messages


@patch("os.makedirs", side_effect=OSError)
@patch("shutil.which", return_value="/path/to/container_engine")
def test_fail_log_file_dir(_mf1, _mf2, generate_config):
    """Ensure an error is created if log file cannot be created"""
    response = generate_config()
    exit_msg = "Failed to create log file"
    assert exit_msg in " ".join([exit_msg.message for exit_msg in response.exit_messages])


@patch("shutil.which", return_value="/path/to/container_engine")
def test_doc_no_plugin_name(_mocked_func, generate_config):
    """Ensure an error is created doc is used without plugin_name"""
    response = generate_config(params=["doc"])
    exit_msg = "A plugin name is required when using the doc subcommand"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


@patch("shutil.which", return_value="/path/to/container_engine")
def test_replay_no_artifact(_mocked_func, generate_config):
    """Ensure an error is created replay is used without playbook artifact"""
    response = generate_config(params=["replay"])
    exit_msg = "An playbook artifact file is required when using the replay subcommand"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


@patch("shutil.which", return_value="/path/to/container_engine")
def test_replay_missing_artifact(_mocked_func, generate_config):
    """Ensure an error is created load is used with a missing playbook artifact"""
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file_name = temp_file.name
    response = generate_config(params=["replay", temp_file_name])
    exit_msg = "The specified playbook artifact could not be found:"
    assert exit_msg in " ".join([exit_msg.message for exit_msg in response.exit_messages])


@patch("shutil.which", return_value="/path/to/container_engine")
def test_badly_formatted_env_var(_mocked_func, generate_config):
    """Ensure exit_messages generated for badly formatted ``--senv``."""
    params = "run site.yml --senv TK1:TV1"
    response = generate_config(params=params.split())
    exit_msg = "The following set-environment-variable entry could not be parsed: TK1:TV1"
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


@patch("shutil.which", return_value="/path/to/container_engine")
def test_not_a_bool(_mocked_func, generate_config):
    """Ensure exit_messages generated for wrong type of value"""

    response = generate_config(setting_file_name="ansible-navigator_not_bool.yml")
    exit_msg = "In 'ansible-navigator.execution-environment.enabled': 5 is not of type 'boolean'."
    assert exit_msg in [exit_msg.message for exit_msg in response.exit_messages]


choices = [entry for entry in NavigatorConfiguration.entries if entry.choices]


@patch("shutil.which", return_value="/path/to/container_engine")
@pytest.mark.parametrize("entry", choices, ids=id_for_name)
def test_poor_choices(_mocked_func, generate_config, entry):
    """Ensure exit_messages generated for poor choices"""

    def test(subcommand, param, look_for):
        if subcommand is None:
            response = generate_config(params=[param, "Sentinel"])
        else:
            response = generate_config(params=[subcommand, param, "Sentinel"])
        assert any(
            look_for in exit_msg.message for exit_msg in response.exit_messages
        ), response.exit_messages

    if isinstance(entry.subcommands, list):
        subcommand = entry.subcommands[0]
    else:
        subcommand = None

    if entry.cli_parameters and entry.cli_parameters.action == "store_true":
        pass
    elif entry.cli_parameters:
        look_for = "must be one"
        # ansible-navigator choice error
        test(subcommand, entry.cli_parameters.short, look_for)
        test(
            subcommand,
            entry.cli_parameters.long_override or f"--{entry.name_dashed}",
            look_for,
        )
    else:
        # argparse choice error
        test(subcommand, "", "choose from")
