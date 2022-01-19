"""The ``settings`` subcommand action.
"""
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
from ..steps import Step
from ..ui_framework import Interaction
from .._yaml import human_dump

# use if needed
def filter_content_keys(obj: Dict[Any, Any]) -> Dict[Any, Any]:
    """Filter out some keys when showing content."""
    return {k: v for k, v in obj.items() if not k.startswith("__")}

def color_menu(colno: int, colname: str, entry: Dict[str, Any]) -> Tuple[int, int]:

    """color the menu"""
    #if entry["__default"] is False:     #uncomment when column __default is added
    #    return 3, 0
    return 2, 0

class HumanReadableEntry(SimpleNamespace):
    # pylint: disable=too-few-public-methods
    """Data structure for a setting entry."""
    name: str
    description: str
    cli_parameters: Dict[str, str]
    current_value: Any
    default_value: Any
    source: str


@actions.register
class Action(App):
    # pylint: disable=too-few-public-methods

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
        self._transform_current_settings()
        print(human_dump(self._settings))
        return 0

    def _build_main_menu(self):
        """Build the main menu of settings."""
        return Step(
            name="all_options",
            columns=["name", "description", "default_value", "current_value", "source"],
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
            # TODO: remember why this is here
            if self.steps.current.show_func:
                current_index = self.steps.current.index
                self.steps.current.show_func()
                self.steps.current.index = current_index

            if self.steps.current.type == "menu":
                result = self._interaction.ui.show(
                    obj=self.steps.current.value,
                    columns=self.steps.current.columns,
                    # TODO color the menu - green (default)/ yellow (changed)
                    color_menu_item=color_menu,
                )
            elif self.steps.current.type == "content":
                result = self._interaction.ui.show(
                    obj=self.steps.current.value,
                    index=self.steps.current.index,
                    # TODO build a heading for the content
                    # content_heading=content_heading,
                    filter_content_keys=filter_content_keys,
                )

        if result is None:
            self.steps.back_one()
        else:
            self.steps.append(result)

    def _transform_current_settings(self):
        """Transform the current settings from an ApplicationConfiguration into a list of
        dictionaries.
        """
        settings = []
        for current_entry in self.app.args.entries:
            new_entry = HumanReadableEntry()
            # basic information
            new_entry.name = current_entry.name
            new_entry.description = current_entry.short_description
            new_entry.source = current_entry.value.source
            new_entry.current_value = current_entry.value.current
            

            """Conditional to check for the default value of a setting"""
            if(current_entry.value.default is current_entry.value.current):
                new_entry.default_value = True
            else:
                new_entry.default_value = False
            

            # the CLI parameters
            if isinstance(current_entry.cli_parameters, CliParameters):
                # TODO: fix --playbook short
                new_entry.cli_parameters = {"short": current_entry.cli_parameters.short}
                new_entry.cli_parameters["long"] = (
                    current_entry.cli_parameters.long_override or f"--{current_entry.name_dashed}"
                )
            else:
                new_entry.cli_parameters = {"short": "None", "long": "None"}
            # TODO: add more content
            settings.append(new_entry.__dict__)
        self._settings = settings
