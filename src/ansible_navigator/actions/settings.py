"""The ``settings`` subcommand action."""


import copy
import sys

from dataclasses import asdict
from typing import Dict
from typing import List
from typing import Mapping
from typing import Tuple
from typing import Union
from typing import cast

from .._yaml import human_dump
from ..action_base import ActionBase
from ..action_defs import RunStdoutReturn
from ..app_public import AppPublic
from ..configuration_subsystem import transform_settings
from ..configuration_subsystem.definitions import HRSettingsEntryValue
from ..steps import MappingStep as Step
from ..ui_framework import Color
from ..ui_framework import CursesLinePart
from ..ui_framework import CursesLines
from ..ui_framework import Decoration
from ..ui_framework import Interaction
from . import _actions as actions
from . import run_action


if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class PresentableCliParamters(TypedDict):
    """CLI parameters prepared for the UI."""

    short: str
    """The short CLI parameter"""
    long: str
    """The long CLI parameter"""


class PresentableEntry(TypedDict, total=False):
    """A settings entry prepared for the UI."""

    # pylint: disable=unused-private-member

    __default: str
    """The menu entry for is_default"""
    __current_value: str
    """The current value as a string for the menu"""

    choices: List
    """The possible values"""
    cli_parameters: PresentableCliParamters
    """The CLI parameters, long and short"""
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


PresentableEntries = List[PresentableEntry]


def filter_content_keys(obj: PresentableEntry) -> PresentableEntry:
    """Filter out some keys when showing content.

    :param obj: The object to be filtered
    :returns: The object with keys filtered out
    """
    show = copy.deepcopy(obj)
    show.pop("__default")
    show.pop("__current_value")
    return show


def color_menu(colno: int, colname: str, entry: PresentableEntry) -> Tuple[int, int]:
    # pylint: disable=unused-argument
    """Color the menu.

    :param colno: Column number
    :param colname: Column name
    :param entry: Column value
    :returns: Constants that curses uses to color a line of text
    """
    if entry["is_default"]:
        return Color.GREEN, Color.BLACK
    return Color.YELLOW, Color.BLACK


CONTENT_HEADING_DEFAULT = "{name} (current/default: {current_value})"
CONTENT_HEADING_NOT_DEFAULT = "{name} (current: {current_value})  (default: {default})"


def content_heading(obj: PresentableEntry, screen_w: int) -> CursesLines:
    """Create a heading for the setting entry showing.

    :param obj: The content going to be shown
    :param screen_w: The current screen width
    :returns: The heading
    """
    format_fields = {
        "name": obj["name"].replace("_", " ").upper(),
        "current_value": obj["current_value"],
        "default": obj["default"],
    }
    if obj["is_default"]:
        text = CONTENT_HEADING_DEFAULT.format(**format_fields)
        color = Color.GREEN
    else:
        text = CONTENT_HEADING_NOT_DEFAULT.format(**format_fields)
        color = Color.YELLOW

    fill_characters = screen_w - len(text) + 1
    heading_line = f"{text}{' ' * fill_characters}"

    heading = (
        (
            CursesLinePart(
                column=0,
                string=heading_line,
                color=color,
                decoration=Decoration.UNDERLINE,
            ),
        ),
    )

    return heading


@actions.register
class Action(ActionBase):
    """The action class for the settings subcommand."""

    KEGEX = r"^se(?:ttings)?$"

    def __init__(self, args):
        """Initialize the ``:settings`` action.

        :param args: The current settings for the application
        """
        super().__init__(args=args, logger_name=__name__, name="settings")
        self._settings: List[Mapping[str, object]]

    def run(self, interaction: Interaction, app: AppPublic) -> None:
        """Handle the ``settings`` subcommand in mode ``interactive``.

        :param interaction: The interaction from the user
        :param app: The app instance
        :returns: The pending :class:`~ansible_navigator.ui_framework.ui.Interaction` or
            :data:`None`
        """
        self._logger.debug("settings requested")
        self._prepare_to_run(app, interaction)

        self._gather_settings()
        self.steps.append(self._build_main_menu())

        while True:
            self._calling_app.update()
            self._take_step()

            if not self.steps:
                break

            if self.steps.current.name == "quit":
                return self.steps.current

        self._prepare_to_exit(interaction)
        return None

    def run_stdout(self) -> RunStdoutReturn:
        """Handle settings in mode stdout.

        :returns: RunStdoutReturn
        """
        self._logger.debug("settings requested in stdout mode")
        self._gather_settings()
        filtered = [filter_content_keys(s) for s in cast(PresentableEntries, self._settings)]
        info_dump = human_dump(filtered)
        if isinstance(info_dump, str):
            print(info_dump)
            return RunStdoutReturn(message="", return_code=0)
        return RunStdoutReturn(
            message="Settings could not be retrieved, please log an issue.",
            return_code=1,
        )

    def _build_main_menu(self) -> Step:
        """Build the main menu of settings.

        :returns: The settings menu definition
        """
        step = Step(
            name="all_options",
            columns=["name", "__default", "source", "__current_value"],
            select_func=self._build_settings_content,
            step_type="menu",
        )
        step.value = self._settings
        return step

    def _build_settings_content(self) -> Step:
        """Build the content for one settings entry.

        :returns: The option's content
        """
        step = Step(
            name="setting_content",
            step_type="content",
        )
        step.index = self.steps.current.index
        step.value = self._settings
        return step

    def _gather_settings(self):
        """Gather the settings from the configuration subsystem and prepare for presentation.

        The __default value is used to make the menu heading consistent with the config menu,
        where ``is_default`` will show in the details for each setting.
        """
        hr_settings = transform_settings(self._args)
        settings: PresentableEntries = []
        for setting in hr_settings:
            presentable = cast(PresentableEntry, asdict(setting))
            presentable["__default"] = setting.is_default
            presentable["__current_value"] = str(setting.current_value)
            settings.append(presentable)

        self._settings = settings

    def _take_step(self) -> None:
        """Take one step in the stack of steps."""
        result = None
        if isinstance(self.steps.current, Interaction):
            result = run_action(self.steps.current.name, self.app, self.steps.current)
        elif isinstance(self.steps.current, Step):
            if self.steps.current.show_func:
                current_index = self.steps.current.index
                self.steps.current.show_func()
                self.steps.current.index = current_index

            if self.steps.current.step_type == "menu":
                result = self._interaction.ui.show(
                    obj=self.steps.current.value,
                    columns=self.steps.current.columns,
                    color_menu_item=color_menu,
                )
            elif self.steps.current.step_type == "content":
                result = self._interaction.ui.show(
                    obj=self.steps.current.value,
                    index=self.steps.current.index,
                    content_heading=content_heading,
                    filter_content_keys=filter_content_keys,
                )

        if result is None:
            self.steps.back_one()
        else:
            self.steps.append(result)
