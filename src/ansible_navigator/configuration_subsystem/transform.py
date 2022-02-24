"""Methods of transforming the settings."""

from .definitions import ApplicationConfiguration
from .defs_presentable import PresentableSettingsEntry
from .defs_presentable import PresentableSettingsEntries


def to_presentable(settings: ApplicationConfiguration) -> PresentableSettingsEntries:
    """Transform the current settings into a structure that can be presented with the TUI.

    :param settings: The current settings
    :returns: The settings represented as a list of dictionaries
    """
    settings_list = []

    settings_file_entry = PresentableSettingsEntry.for_settings_file(internals=settings.internals)
    settings_list.append(settings_file_entry)

    settings_file_path = settings_file_entry.current_settings_file
    for entry in settings.entries:
        human_readable_entry = PresentableSettingsEntry.from_settings_entry(
            entry=entry,
            application_name_dashed=settings.application_name_dashed,
            settings_file_path=settings_file_path,
        )
        settings_list.append(human_readable_entry)

    settings_list.sort()
    return settings_list
