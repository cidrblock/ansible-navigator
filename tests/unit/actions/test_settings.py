"""Unit tests for the ``settings`` action."""

import curses

from dataclasses import dataclass

import pytest

from ansible_navigator.actions.settings import color_menu
from ansible_navigator.actions.settings import content_heading
from ansible_navigator.actions.settings import filter_content_keys
from ansible_navigator.ui_framework.curses_defs import CursesLinePart


@dataclass
class ColorMenuTestEntry:
    """A test for menu coloring."""

    color: int
    comment: str
    decoration: int
    is_default: bool

    def __str__(self):
        """Provide a string representation.

        :returns: The string representation of self
        """
        return self.comment


ColorMenuTestEntries = (
    ColorMenuTestEntry(
        comment="default/green",
        color=2,
        decoration=0,
        is_default=True,
    ),
    ColorMenuTestEntry(
        comment="not default/yellow",
        color=3,
        decoration=0,
        is_default=False,
    ),
)


@pytest.mark.parametrize(argnames="data", argvalues=ColorMenuTestEntries, ids=str)
def test_color_menu_true(data: ColorMenuTestEntry):
    """Test color menu for a val set to the default.

    :param data: A test entry
    """
    entry = {"is_default": data.is_default}
    assert color_menu(0, "", entry) == (data.color, data.decoration)


def test_content_heading_true():
    """Test menu generation for a defaulted value."""
    line_length = 100
    default_value = "default_value"
    current_value = default_value
    obj = {
        "name": "test settings entry",
        "current_value": current_value,
        "default": default_value,
        "is_default": current_value == default_value,
        "option": "test_option",
    }
    heading = content_heading(obj, line_length)
    assert len(heading) == 1
    assert len(heading[0]) == 1
    assert isinstance(heading[0][0], CursesLinePart)
    assert len(heading[0][0].string) == line_length + 1
    assert f"test settings entry (current/default: {default_value})" in heading[0][0].string
    assert heading[0][0].color == curses.COLOR_GREEN
    assert heading[0][0].column == 0


def test_content_heading_false() -> None:
    """Test menu generation for a value not default."""
    line_length = 100
    current_value = "current_value"
    default_value = "default_value"
    obj = {
        "name": "test settings entry",
        "current_value": current_value,
        "default": default_value,
        "is_default": current_value == default_value,
        "option": "test_option",
    }
    heading = content_heading(obj, line_length)
    assert heading
    assert len(heading) == 1
    assert len(heading[0]) == 1
    assert isinstance(heading[0][0], CursesLinePart)
    assert len(heading[0][0].string) == line_length + 1
    assert (
        f"test settings entry (current: {current_value})  (default: {default_value})"
        in heading[0][0].string
    )
    assert heading[0][0].color == curses.COLOR_YELLOW
    assert heading[0][0].column == 0


def test_filter_content_keys() -> None:
    """Test filtering keys."""
    obj = {"__key": "value", "key": "value"}
    ret = {"key": "value"}
    assert filter_content_keys(obj) == ret
