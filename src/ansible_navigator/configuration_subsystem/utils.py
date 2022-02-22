"""Utilities related to the configuration subsystem."""

from dataclasses import asdict
from dataclasses import dataclass
from types import SimpleNamespace
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from .definitions import ApplicationConfiguration
from .definitions import CliParameters
from .definitions import Constants as C
from .definitions import HRSettingsEntryDicts
from .definitions import HRSettingsEntryValue
from .definitions import SettingsEntry


TCli = TypeVar("TCli", bound="_HRCliParameters")
TEnt = TypeVar("TEnt", bound="_HRSettingsEntry")

SettingsFileSample = Dict[str, Union[Dict, str]]


@dataclass(frozen=True)
class _HRCliParameters:
    """Human readable (HR) data structure for the cli parameters for an entry."""

    NO_LONG_MSG: ClassVar[str] = "No long CLI parameter"
    NO_SHORT_MSG: ClassVar[str] = "No short CLI parameter"

    long: str = NO_LONG_MSG
    """The long cli parameter value"""
    short: str = NO_SHORT_MSG
    """The short cli parameter value"""

    @classmethod
    def from_cli_params(
        cls: Type[TCli],
        cli_parameters: Optional[CliParameters],
        name_dashed: str,
    ) -> TCli:
        """Create an ``_HRCliParameters`` based on an entry's cli parameters.

        :param cli_parameters: The entry's cli parameters
        :param name_dashed: The dashed name of the parent settings entry
        :returns: The instance of self based on an entry's cli parameters
        """
        if isinstance(cli_parameters, CliParameters):
            short = cli_parameters.short or cls.NO_SHORT_MSG
            long = cli_parameters.long(name_dashed)
            return cls(long=long, short=short)
        return cls()


@dataclass(frozen=True)
class _HRSettingsEntry:
    # pylint: disable=too-many-instance-attributes
    """Human readable (HR) data structure for a settings entry."""

    choices: List
    """The possible values"""
    current_settings_file: str
    """The path to the current settings file"""
    current_value: HRSettingsEntryValue
    """The current, effective value"""
    default: HRSettingsEntryValue
    """The default value"""
    description: str
    """A short description"""
    env_var: str
    """The environment variable"""
    is_default: bool
    """Indicates if the current value == the default"""
    name: str
    """The name"""
    settings_file_sample: Union[str, Dict]
    """A sample settings file snippet"""
    source: str
    """The source of the current value"""

    cli_parameters: _HRCliParameters = _HRCliParameters()
    """The CLI parameters, long and short"""

    @classmethod
    def for_settings_file(cls: Type[TEnt], internals: SimpleNamespace) -> TEnt:
        """Create an ``_HRSettingsEntry`` containing the details for the settings file.

        :param internals: The internal storage for settings information
        :returns: The settings file entry
        """
        description = (
            "The path to the current settings file. Possible locations are"
            " {CWD}/ansible-navigator.{ext} or {HOME}/.ansible-navigator.{ext}"
            " where ext is yml, yaml or json."
        )
        return cls(
            choices=[],
            current_settings_file=internals.settings_file_path or C.NONE.value,
            current_value=internals.settings_file_path or C.NONE.value,
            default=C.NONE.value,
            is_default=internals.settings_source is C.NONE,
            description=description,
            name="current_settings_file",
            env_var="ANSIBLE_NAVIGATOR_CONFIG",
            settings_file_sample="Not applicable",
            source=internals.settings_source.value,
        )

    @classmethod
    def from_settings_entry(
        cls: Type[TEnt],
        application_name_dashed: str,
        entry: SettingsEntry,
        settings_file_path: str,
    ) -> TEnt:
        """Create an ``_HRSettingsEntry`` containing the details for one settings entry.

        :param application_name_dashed: The application name, dashed
        :param entry: A settings entry
        :param settings_file_path: The path to the settings file
        :return: The settings file entry
        """
        cli_parameters = _HRCliParameters.from_cli_params(
            cli_parameters=entry.cli_parameters,
            name_dashed=entry.name_dashed,
        )

        env_var = entry.environment_variable(application_name_dashed)
        entry_value_resolved = entry.value.resolved

        path = entry.settings_file_path(application_name_dashed)
        settings_file_sample = _create_settings_file_sample(path)

        result = cls(
            choices=list(entry.choices),  # May be a tuple e.g. PLUGIN_TYPES
            cli_parameters=cli_parameters,
            current_settings_file=str(settings_file_path),
            current_value=entry_value_resolved.current,
            default=entry_value_resolved.default,
            description=entry.short_description,
            env_var=env_var,
            is_default=entry_value_resolved.is_default,
            name=entry.name,
            settings_file_sample=settings_file_sample,
            source=entry.value.source.value,
        )
        return result


def transform_settings(settings: ApplicationConfiguration) -> HRSettingsEntryDicts:
    """Transform the current settings into a list of dictionaries.

    :param settings: The current settings
    :returns: The settings represented as a list of dictionaries
    """
    settings_list: List[_HRSettingsEntry] = []

    settings_file_entry = _HRSettingsEntry.for_settings_file(internals=settings.internals)
    settings_list.append(settings_file_entry)

    settings_file_path = settings_file_entry.current_settings_file
    for entry in settings.entries:
        human_readable_entry = _HRSettingsEntry.from_settings_entry(
            entry=entry,
            application_name_dashed=settings.application_name_dashed,
            settings_file_path=settings_file_path,
        )
        settings_list.append(human_readable_entry)

    sorted_settings = sorted(settings_list, key=lambda d: d.name)
    result = [asdict(entry) for entry in sorted_settings]
    return result


def _create_settings_file_sample(settings_path: str) -> SettingsFileSample:
    """Generate a settings file sample.

    :param settings_path: The dot delimited settings file path for a settings entry
    :returns: A sample of the settings file
    """
    if "." not in settings_path:
        return {settings_path: "<------"}
    key, remainder = settings_path.split(".", 1)
    return {key: _create_settings_file_sample(remainder)}
