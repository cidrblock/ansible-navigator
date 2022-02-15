"""The ``settings`` subcommand action."""

import curses

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from .._yaml import human_dump
from ..action_base import ActionBase
from ..action_defs import RunStdoutReturn
from ..app_public import AppPublic
from ..configuration_subsystem import transform_settings
from ..steps import Step
from ..ui_framework import CursesLinePart
from ..ui_framework import CursesLines
from ..ui_framework import Interaction
from . import _actions as actions
from . import run_action


def filter_content_keys(obj: Dict[Any, Any]) -> Dict[Any, Any]:
    """Filter out some keys when showing content.

    :param obj: The object to be filtered
    :return: The object with keys filtered out
    """
    return {k: v for k, v in obj.items() if not k.startswith("__")}


def color_menu(colno: int, colname: str, entry: Dict[str, Any]) -> Tuple[int, int]:
    # pylint: disable=unused-argument
    """Color the menu.

    :param colno: Column number
    :param colname: Column name
    :param entry: Column value
    :return: Tuple int used to color the menu
    """
    if entry["default"] == "False":
        return 3, 0
    return 2, 0


def content_heading(obj: Any, screen_w: int) -> CursesLines:
    """Create a heading for the setting entry showing.

    :param obj: The content going to be shown
    :param screen_w: The current screen width
    :return: The heading
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
                ),
            ],
        ),
    )
    return tuple(heading)


@actions.register
class Action(ActionBase):
    """The action class for the settings subcommand."""

    KEGEX = r"^se(?:ttings)?$"

    def __init__(self, args):
        """Initialize the ``:settings`` action.

        :param args: The current settings for the application
        """
        super().__init__(args=args, logger_name=__name__, name="settings")
        self._settings: List[Dict]

    def run(self, interaction: Interaction, app: AppPublic) -> None:
        """Handle the ``settings`` subcommand in mode ``interactive``.

        :param interaction: The interaction from the user
        :param app: The app instance
        :return: The pending :class:`~ansible_navigator.ui_framework.ui.Interaction` or
            :data:`None`
        """
        self._logger.debug("settings requested")
        self._prepare_to_run(app, interaction)

        self._settings = transform_settings(self._args)
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

        :return: RunStdoutReturn
        """
        self._logger.debug("settings requested in stdout mode")
        self._settings = transform_settings(self._args)
        info_dump = human_dump(self._settings)
        if isinstance(info_dump, str):
            print(info_dump)
            return RunStdoutReturn(message="", return_code=0)
        return RunStdoutReturn(
            message="Settings could not be retrieved, please log an issue.",
            return_code=1,
        )

    def _build_main_menu(self) -> Step:
        """Build the main menu of settings.

        :return: The settings menu definition
        """
        return Step(
            name="all_options",
            columns=["name", "default", "source", "current_value"],
            select_func=self._build_settings_content,
            step_type="menu",
            value=self._settings,
        )

    def _build_settings_content(self) -> Step:
        """Build the content for one settings entry.

        :return: The option's content
        """
        return Step(
            name="setting_content",
            step_type="content",
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
