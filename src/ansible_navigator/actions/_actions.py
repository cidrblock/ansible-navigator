"""Helper functions for the ``actions`` package."""

from __future__ import annotations

import functools
import importlib
import importlib.resources as importlib_resources
import logging
import os
import re

from typing import TYPE_CHECKING
from typing import Any
from typing import NamedTuple

from ansible_navigator.ui_framework import error_notification


if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Generator

    from ansible_navigator.action_defs import RunStdoutReturn


logger = logging.getLogger(__name__)


# Basic structure for storing information about one action
class ActionT(NamedTuple):
    """NamedTuple representing an action."""

    name: str
    cls: str
    kegex: str


class Kegex(NamedTuple):
    """NamedTuple representing a kegex."""

    name: str
    kegex: str


# Dictionary with information about all registered actions
_ACTIONS: dict[str, dict[str, Any]] = {}


def _import(package: str, action: str) -> None:
    """Import the given action from a package.

    Args:
        package: The name of the package
        action: The action to import
    """
    importlib.import_module(f"{package}.{action}")


def _import_all(package: str) -> None:
    """Import all actions in a package.

    Args:
        package: The name of the package
    """
    for entry in importlib_resources.files(package).iterdir():
        if entry.is_file() and entry.name.endswith(".py") and not entry.name.startswith("_"):
            _import(package, entry.name[0:-3])


def register(cls: Any) -> Any:
    """Register an action, used as a decorator.

    Args:
        cls: The class to register

    Returns:
        The class after registration
    """
    package, _, action = cls.__module__.rpartition(".")
    pkg_info = _ACTIONS.setdefault(package, {})
    pkg_info[action] = ActionT(name=action, cls=cls, kegex=re.compile(cls.KEGEX))  # type: ignore[arg-type]
    return cls


def get(package: str, action: str) -> Callable[..., Any]:
    """Import and return a given action.

    Args:
        package: The name of the package
        action: The name of the action

    Returns:
        The action's registered class
    """
    _import(package, action)
    return _ACTIONS[package][action].cls


def get_factory(package: str) -> Callable[..., Any]:
    """Create a ``get()`` function for one package.

    Args:
        package: The name of the package

    Returns:
        The action's registered class
    """
    return functools.partial(get, package)


def kegex(package: str, action: str) -> tuple[str, str, str]:
    """Return a tuple of name, class, ``kegex`` for an action.

    Args:
        package: The name of the package
        action: The name of the action

    Returns:
        The name, class and kegex for an action
    """
    _import(package, action)
    return _ACTIONS[package][action]


def kegexes(package: str) -> Generator[tuple[str, str, str]]:
    """Return a tuple of tuples, name, ``kegex`` for all actions.

    Args:
        package: The name of the package

    Returns:
        A generator for all ``kegexes``
    """
    _import_all(package)
    return (kegex(package, name) for name in names(package))


def kegexes_factory(package: str) -> Callable[..., Any]:
    """Create a ``kegexes()`` function for all packages.

    Args:
        package: The name of the package

    Returns:
        A ``kegexes()`` method for the package
    """
    return functools.partial(kegexes, package)


def names(package: str) -> list[str]:
    """List all actions in one package.

    Args:
        package: The name of the package

    Returns:
        All packages
    """
    _import_all(package)
    return sorted(_ACTIONS[package])


def names_factory(package: str) -> Callable[..., Any]:
    """Create a ``names()`` function for one package.

    Args:
        package: The name of the package

    Returns:
        a ``names()`` method for the package
    """
    return functools.partial(names, package)


def run_interactive(package: str, action: str, *args: Any, **_kwargs: dict[str, Any]) -> Any:
    """Call the given action's ``run()`` method.

    Args:
        package: The name of the package
        action: The name of the action
        *args: The arguments passed to the action's run method
        **_kwargs: The keyword arguments passed to the action's run
            method

    Returns:
        The outcome of running the action's run method
    """
    action_cls = get(package, action)
    app, interaction = args
    app_action = action_cls(app.args)
    supports_interactive = hasattr(app_action, "run")
    if not supports_interactive:
        logger.error("Subcommand '%s' does not support mode interactive", action)
    run_action = app_action.run if supports_interactive else app_action.no_interactive_mode

    # Allow tracebacks to bring down the UI, used in tests
    if os.getenv("ANSIBLE_NAVIGATOR_ALLOW_UI_TRACEBACK") == "true":
        return run_action(app=app, interaction=interaction)

    # Capture and show a UI notification
    try:
        return run_action(app=app, interaction=interaction)
    except Exception:
        logger.critical("Subcommand '%s' encountered a fatal error.", action)
        logger.exception("Logging an uncaught exception")
        warn_msg = [f"Unexpected errors were encountered while running '{action}'."]
        warn_msg.append("Please log an issue with the log file contents.")
        warning = error_notification(warn_msg)
        interaction.ui.show_form(warning)
        return None


def run_interactive_factory(package: str) -> Callable[..., Any]:
    """Create a ``run_interactive()`` function for one package.

    Args:
        package: The name of the package

    Returns:
        A partial ``run_interactive()`` method for the package
    """
    return functools.partial(run_interactive, package)


def run_stdout(package: str, action: str, *args: Any, **_kwargs: dict[str, Any]) -> RunStdoutReturn:
    """Call the given action's ``run_stdout`` method.

    Args:
        package: The name of the package
        action: The name of the action
        *args: The arguments passed to the action's run_stdout method
        **_kwargs: The keyword arguments passed to the action's
            run_stdout method

    Returns:
        The outcome of running the action's ``run_stdout()`` method
    """
    # Refers to the action's run_stdout in the first line, not this function
    action_cls = get(package, action)
    args = args[0]
    return action_cls(args).run_stdout()


def run_stdout_factory(package: str) -> Callable[..., Any]:
    """Create a ``run_stdout()`` function for one package.

    Args:
        package: The name of the package

    Returns:
        A partial ``run_stdout()`` method for the package
    """
    return functools.partial(run_stdout, package)
