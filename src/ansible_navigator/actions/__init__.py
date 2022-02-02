<<<<<<< HEAD
"""A package containing all available actions.

The actions package is a plugin-like implementation for all available application actions.

Actions can be added without registration and are discovered and loaded
when their ``KEGEX`` is matched against user input.

This allows for each action to be loaded multiple times, creating a unique
and isolated instance of the action.

Currently, the ``actions`` package is the only package supported for actions and
is identified in the
:class:`~ansible_navigator.configuration_subsystem.navigator_configuration.Internals`.
"""
||||||| parent of b1fa9a8e (updates)
"""actions for Explorer"""
=======
"""A package containing all available actions.

The actions package is a plugin like implementation for all available application actions.

Actions can be added without registration and are discovered and loaded
when their ``KEGEX`` is matched against user input.

This allows for each action to be loaded multiple times, creating a unique
and isolated instance of the action.

Currently, the actions package is the only package supported for actions and
is identified in the :class:`~ansible_navigator.navigator_subsystem.navigator_internals.Internals`
"""
>>>>>>> b1fa9a8e (updates)
from typing import Any
from typing import Callable
from typing import Union

from ..app_public import AppPublic
from ..configuration_subsystem import ApplicationConfiguration
from ..ui_framework import Interaction
from . import _actions as actions


get: Callable[[str], Any] = actions.get_factory(__package__)

names = actions.names_factory(__package__)

kegexes: Callable = actions.kegexes_factory(__package__)

run_action_stdout: Callable[[str, ApplicationConfiguration], int] = actions.run_stdout_factory(
    __package__,
)

run_action: Callable[
    [str, AppPublic, Interaction],
    Union[None, Interaction],
] = actions.run_interactive_factory(__package__)


__all__ = ["get", "kegexes", "names", "run_action", "run_action_stdout"]
