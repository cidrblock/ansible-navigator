"""The ``settings`` subcommand action."""

import curses

from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import Tuple

from types import SimpleNamespace

from . import _actions as actions
from . import run_action

from ..app import App
from ..app_public import AppPublic
from ..configuration_subsystem.definitions import CliParameters
from ..configuration_subsystem.definitions import Constants
from ..steps import Step
from ..ui_framework import CursesLinePart
from ..ui_framework import CursesLines
from ..ui_framework import Interaction
from .._yaml import human_dump


def filter_content_keys(obj: Dict[Any, Any]) -> Dict[Any, Any]:
    """Filter out some keys when showing content.

    :param obj: The object to be filtered
    :return: The object with keys filtered out
    """
    return {k: v for k, v in obj.items() if not k.startswith("__")}


def color_menu(colno: int, colname: str, entry: Dict[str, Any]) -> Tuple[int, int]:
    # pylint: disable=unused-argument

    """color the menu"""
    if entry["default"] == "False":
        return 3, 0
    return 2, 0


def content_heading(obj: Any, screen_w: int) -> Union[CursesLines, None]:
    """create a heading for host showing

    :param obj: The content going to be shown
    :type obj: Any
    :param screen_w: The current screen width
    :type screen_w: int
    :return: The heading
    :rtype: Union[CursesLines, None]
    """

    heading = []
    string = obj["name"].replace("_", " ")
    if obj["default"] == "False":
        string += f" (current: {obj['current_value']})  (default: {obj['default']})"
        color = 3
    else:
        string += f" (current/default: {obj['current_value']})"
        color = 2

    string = string + (" " * (screen_w - len(string) + 1))

    heading.append(
        tuple(
            [
                CursesLinePart(
                    column=0,
                    string=string,
                    color=color,
                    decoration=curses.A_UNDERLINE,
                )
            ]
        )
    )
    return tuple(heading)


class HumanReadableEntry(SimpleNamespace):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
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


@actions.register
class Action(App):
    """The action class for the settings subcommand."""

    KEGEX = r"^se(?:ttings)?$"

    def __init__(self, args):
        super().__init__(args=args, logger_name=__name__, name="settings")
        self._settings: List[Dict]

    def run(self, interaction: Interaction, app: AppPublic) -> Union[Interaction, None]:
        """Handle the ``settings`` subcommand in mode ``interactive``.

        :param interaction: The interaction from the user
        :param app: The app instance
        """
        self._logger.debug("settings requested")
        self._prepare_to_run(app, interaction)

        self._transform_current_settings()
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

    def run_stdout(self) -> int:
        """Handle settings in mode stdout."""
        self._logger.debug("settings requested in stdout mode")
        self._transform_current_settings()
        print(human_dump(self._settings))
        return 0

    def _build_main_menu(self):
        """Build the main menu of settings."""
        return Step(
            name="all_options",
            columns=["name", "default", "source", "current_value"],
            select_func=self._build_settings_content,
            tipe="menu",
            value=self._settings,
        )

    def _build_settings_content(self):
        """Build the content for one settings entry."""
        return Step(
            name="setting_content",
            tipe="content",
            value=self._settings,
            index=self.steps.current.index,
        )

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

            if self.steps.current.type == "menu":
                result = self._interaction.ui.show(
                    obj=self.steps.current.value,
                    columns=self.steps.current.columns,
                    color_menu_item=color_menu,
                )
            elif self.steps.current.type == "content":
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

    def _sample_generator(self, settings_path: str) -> Dict:
        """Generate a settings file sample.

        :param settings_path: The dot delimited settings file path for a settings entry
        :returns: A sample of the settings file
        """
        if "." not in settings_path:
            return {settings_path: "<------"}
        key, remainder = settings_path.split(".", 1)
        return {key: self._sample_generator(remainder)}

    def _transform_current_settings(self):
        """Transform the current settings into a list of dictionaries."""
        
        new_entry = HumanReadableEntry()
        new_entry.name = "current_settings_file"

        current_settings_file = self.app.args.internals.settings_file_path or "None"
        new_entry.current_settings_file = current_settings_file
        new_entry.current_value = current_settings_file
        new_entry.default_value = (
            "{CWD}/ansible-navigator.{ext} or {HOME}/.ansible-navigator.{ext}" 
            " where ext is yml, yaml or json"
            )
        new_entry.description = "The path to the current settings file"
        new_entry.env_var = "ANSIBLE_NAVIGATOR_CONFIG"
        new_entry.settings_file_sample = "Not applicable"
        new_entry.source = self.app.args.internals.settings_source.value
        if self.app.args.internals.settings_source is Constants.SEARCH_PATH:
            new_entry.default = str(True)
        elif self.app.args.internals.settings_source is Constants.NONE or self.app.args.internals.settings_source is Constants.ENVIRONMENT_VARIABLE:
            new_entry.default = str(False)
        settings = [vars(new_entry)]
     
        for current_entry in self.app.args.entries:
            new_entry = HumanReadableEntry()

            # Build the column data
            new_entry.name = current_entry.name
            new_entry.description = current_entry.short_description
            new_entry.current_settings_file = current_settings_file
            new_entry.source = current_entry.value.source.value
            new_entry.env_var = current_entry.environment_variable(
                self.app.args.application_name.upper()
            )
            new_entry.choices = current_entry.choices

            if current_entry.value.source in (Constants.NOT_SET, Constants.DEFAULT_CFG):
                new_entry.default = "True"
            else:
                new_entry.default = "False"

            if isinstance(current_entry.value.default, Constants):
                new_entry.default_value = current_entry.value.default.value
            else:
                new_entry.default_value = str(current_entry.value.default)

            if isinstance(current_entry.value.current, Constants):
                new_entry.current_value = current_entry.value.current.value
            else:
                # Translate all current_value variables to string for formatting purposes
                new_entry.current_value = str(current_entry.value.current)

            # Check for the CLI parameters
            if isinstance(current_entry.cli_parameters, CliParameters):

                if current_entry.cli_parameters.short:
                    new_entry.cli_parameters = {"short": current_entry.cli_parameters.short}
                else:
                    new_entry.cli_parameters = {"short": "No short CLI parameter"}

                new_entry.cli_parameters["long"] = (
                    current_entry.cli_parameters.long_override or f"--{current_entry.name_dashed}"
                )
            else:
                new_entry.cli_parameters = {"short": "None", "long": "None"}

            new_entry.settings_file_sample = self._sample_generator(
                current_entry.settings_file_path(
                    prefix=self.app.args.application_name.replace("-", "_")
                )
            )

            settings.append(vars(new_entry))
        sorted_settings = sorted(settings, key=lambda d: d['name'])
        self._settings = sorted_settings