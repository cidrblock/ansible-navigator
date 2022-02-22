"""The ``settings`` subcommand action."""

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
from ..ui_framework import Color
from ..ui_framework import CursesLinePart
from ..ui_framework import CursesLines
from ..ui_framework import Decoration
from ..ui_framework import Interaction
from . import _actions as actions
from . import run_action


def filter_content_keys(obj: Dict[Any, Any]) -> Dict[Any, Any]:
    """Filter out some keys when showing content.

    :param obj: The object to be filtered
    :returns: The object with keys filtered out
    """
    return {k: v for k, v in obj.items() if not k.startswith("__")}


def color_menu(colno: int, colname: str, entry: Dict[str, Any]) -> Tuple[int, int]:
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


def content_heading(obj: Any, screen_w: int) -> CursesLines:
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
        self._settings: List[Dict]

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

        :returns: The settings menu definition
        """
        return Step(
            name="all_options",
            columns=["name", "__default", "source", "__current_value"],
            select_func=self._build_settings_content,
            step_type="menu",
            value=self._settings,
        )

    def _build_settings_content(self) -> Step:
        """Build the content for one settings entry.

        :returns: The option's content
        """
        return Step(
            name="setting_content",
            step_type="content",
            value=self._settings,
            index=self.steps.current.index,
        )

    def _gather_settings(self):
        """Gather the settings from the configuration subsystem and prepare for presentation.

        The __default value is used to make the menu heading consistent with the config menu,
        where ``is_default`` will show in the details for each setting.
        """
        settings = transform_settings(self._args)
        for setting in settings:
            setting["__default"] = setting["is_default"]
            setting["__current_value"] = str(setting["current_value"])
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
