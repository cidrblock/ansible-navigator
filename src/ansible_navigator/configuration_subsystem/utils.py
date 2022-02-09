"""Utilities related to the configuration subsystem."""

from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple

from .definitions import ApplicationConfiguration
from .definitions import CliParameters
from .definitions import Constants


class HumanReadableEntry(NamedTuple):
    """Data structure for a setting entry."""

    choices: List
    cli_parameters: Dict[str, str]
    current_settings_file: str
    current_value: Any
    default_value: Any
    default: Any
    description: str
    env_var: str
    name: str
    settings_file_sample: Dict
    source: str


def _sample_generator(settings_path: str) -> Dict:
    """Generate a settings file sample.

    :param settings_path: The dot delimited settings file path for a settings entry
    :returns: A sample of the settings file
    """
    if "." not in settings_path:
        return {settings_path: "<------"}
    key, remainder = settings_path.split(".", 1)
    return {key: _sample_generator(remainder)}


def _settings_check(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all keys are present in the settings entry.

    :param entry: Settings entry to test
    """
    HumanReadableEntry(**entry)
    return entry


def transform_settings(
    settings: ApplicationConfiguration,
) -> List[Dict[str, Any]]:
    """Transform the current settings into a list of dictionaries."""

    entry = {}
    entry["name"] = "current_settings_file"

    current_settings_file = settings.internals.settings_file_path or "None"
    entry["choices"] = []
    entry["cli_parameters"] = {"short": "None", "long": "None"}
    entry["current_settings_file"] = current_settings_file
    entry["current_value"] = current_settings_file
    entry["default_value"] = (
        "{CWD}/ansible-navigator.{ext} or {HOME}/.ansible-navigator.{ext}"
        " where ext is yml, yaml or json"
    )
    entry["description"] = "The path to the current settings file"
    entry["env_var"] = "ANSIBLE_NAVIGATOR_CONFIG"
    entry["settings_file_sample"] = "Not applicable"
    entry["source"] = settings.internals.settings_source.value
    if settings.internals.settings_source is Constants.SEARCH_PATH:
        entry["default"] = str(True)
    elif (
        settings.internals.settings_source is Constants.NONE
        or settings.internals.settings_source is Constants.ENVIRONMENT_VARIABLE
    ):
        entry["default"] = str(False)

    settings_list = [_settings_check(entry)]

    for current_entry in settings.entries:
        entry = {}

        # Build the column data
        entry["name"] = current_entry.name
        entry["description"] = current_entry.short_description
        entry["current_settings_file"] = current_settings_file
        entry["source"] = current_entry.value.source.value
        entry["env_var"] = current_entry.environment_variable(settings.application_name.upper())
        entry["choices"] = current_entry.choices

        if current_entry.value.source in (Constants.NOT_SET, Constants.DEFAULT_CFG):
            entry["default"] = "True"
        else:
            entry["default"] = "False"

        if isinstance(current_entry.value.default, Constants):
            entry["default_value"] = current_entry.value.default.value
        else:
            entry["default_value"] = str(current_entry.value.default)

        if isinstance(current_entry.value.current, Constants):
            entry["current_value"] = current_entry.value.current.value
        else:
            # Translate all current_value variables to string for formatting purposes
            entry["current_value"] = str(current_entry.value.current)

        # Check for the CLI parameters
        if isinstance(current_entry.cli_parameters, CliParameters):

            if current_entry.cli_parameters.short:
                entry["cli_parameters"] = {"short": current_entry.cli_parameters.short}
            else:
                entry["cli_parameters"] = {"short": "No short CLI parameter"}

            entry["cli_parameters"]["long"] = (
                current_entry.cli_parameters.long_override or f"--{current_entry.name_dashed}"
            )
        else:
            entry["cli_parameters"] = {"short": "None", "long": "None"}

        entry["settings_file_sample"] = _sample_generator(
            current_entry.settings_file_path(prefix=settings.application_name.replace("-", "_")),
        )
        settings_list.append(_settings_check(entry))

    sorted_settings = sorted(settings_list, key=lambda d: d["name"])
    return sorted_settings
