"""Unit tests for the ``settings`` action."""

from dataclasses import dataclass

import pytest

from ansible_navigator.actions.settings import CONTENT_HEADING_DEFAULT
from ansible_navigator.actions.settings import CONTENT_HEADING_NOT_DEFAULT
from ansible_navigator.actions.settings import PresentableEntry
from ansible_navigator.actions.settings import color_menu
from ansible_navigator.actions.settings import content_heading
from ansible_navigator.actions.settings import filter_content_keys
from ansible_navigator.ui_framework import Color
from ansible_navigator.ui_framework import CursesLinePart
from ansible_navigator.ui_framework import Decoration


@dataclass
class ColorMenuTestEntry:
    """A test for menu coloring."""

    color: int
    """The color for menu entry"""
    comment: str
    """Describe the test"""
    decoration: int
    """The test decoration"""
    is_default: bool
    """Is the current value equal to the default"""

    def __str__(self):
        """Provide a string representation.

        :returns: The string representation of self
        """
        return self.comment


ColorMenuTestEntries = (
    ColorMenuTestEntry(
        comment="default/green",
        color=Color.GREEN,
        decoration=Decoration.NORMAL,
        is_default=True,
    ),
    ColorMenuTestEntry(
        comment="not default/yellow",
        color=Color.YELLOW,
        decoration=Decoration.NORMAL,
        is_default=False,
    ),
)


@pytest.mark.parametrize(argnames="data", argvalues=ColorMenuTestEntries, ids=str)
def test_color_menu(data: ColorMenuTestEntry):
    """Test color menu for a val set to the default.

    :param data: A test entry
    """
    entry = PresentableEntry(is_default=data.is_default)
    assert color_menu(0, "", entry) == (data.color, data.decoration)


@dataclass
class ContentHeadingEntry:
    """A test for content headings."""

    color: int
    """The color for menu entry"""
    comment: str
    """Describes the test"""
    content: PresentableEntry
    """The content"""

    def __post_init__(self):
        """Set is_default after initialization."""
        self.content["is_default"] = self.content["current_value"] == self.content["default"]

    @property
    def heading(self):
        """Create the expected heading for this content.

        :returns: The expected heading
        """
        if self.content["is_default"]:
            heading = CONTENT_HEADING_DEFAULT
        else:
            heading = CONTENT_HEADING_NOT_DEFAULT
        return heading.format(**self.content)

    def __str__(self):
        """Provide a string representation.

        :returns: The string representation of self
        """
        return self.comment


ContentHeadingEntries = (
    ContentHeadingEntry(
        color=Color.GREEN,
        comment="same",
        content=PresentableEntry(
            current_value="navigator",
            default="navigator",
            name="TEST",
        ),
    ),
    ContentHeadingEntry(
        color=Color.YELLOW,
        comment="different",
        content=PresentableEntry(
            current_value="ansible",
            default="navigator",
            name="TEST",
        ),
    ),
)


@pytest.mark.parametrize(argnames="data", argvalues=ContentHeadingEntries, ids=str)
def test_content_heading(data: ContentHeadingEntry):
    """Test menu generation.

    :param data: The test data
    """
    width = 100
    heading = content_heading(obj=data.content, screen_w=width)
    heading_lines = 1
    line_parts = 1

    assert len(heading) == heading_lines

    first_line = heading[0]
    assert len(first_line) == line_parts

    first_line_part = heading[0][0]
    assert isinstance(first_line_part, CursesLinePart)
    assert len(first_line_part.string) == width + 1
    assert first_line_part.color == data.color
    assert first_line_part.column == 0
    assert data.heading in first_line_part.string


def test_filter_content_keys() -> None:
    """Test filtering keys."""
    obj = PresentableEntry(__default="value", __current_value="value", name="name")
    ret = PresentableEntry(name="name")
    assert filter_content_keys(obj) == ret
