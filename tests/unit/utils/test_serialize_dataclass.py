"""Tests for serializing a dataclass."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING
from typing import Any
from typing import NamedTuple

import pytest

from ansible_navigator.content_defs import ContentBase
from ansible_navigator.content_defs import ContentView
from ansible_navigator.utils.serialize import SerializationFormat
from ansible_navigator.utils.serialize import serialize
from tests.defaults import id_func


if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable


class ParametrizeView(NamedTuple):
    """Keyword arguments for parametrization of view."""

    argnames: str = "content_view"
    argvalues: Iterable[Any] = (ContentView.NORMAL, ContentView.FULL)
    ids: Callable[..., Any] = id_func


class ParametrizeFormat(NamedTuple):
    """Keyword arguments for parametrization of format."""

    argnames: str = "serialization_tuple"
    argvalues: Iterable[Any] = (("j", SerializationFormat.JSON), ("y", SerializationFormat.YAML))
    ids: Callable[..., Any] = id_func


SimpleDictValue = bool | str | int


@dataclass
class ContentTestSimple(ContentBase[SimpleDictValue]):
    """Test content, no dictionary factory overrides."""

    attr_01: bool = False
    attr_02: int = 2
    attr_03: str = "three"


OverrideDictValueT = str
OverrideDictReturn = dict[str, OverrideDictValueT]
OverrideAllValues = bool | int | str


@dataclass
class ContentTestOverride(ContentBase[OverrideDictValueT]):
    """Test content, with dictionary factory overrides."""

    attr_01: bool = False
    attr_02: int = 2
    attr_03: str = "three"

    def serialize_json_full(self) -> OverrideDictReturn:
        """Provide dictionary factory for ``JSON`` with all attributes.

        Returns:
            The function used for conversion to a dictionary or nothing
        """
        return self._asdict(suffix=f"_j_{ContentView.FULL!s}")

    def serialize_json_normal(self) -> OverrideDictReturn:
        """Provide dictionary factory for ``JSON`` with curated attributes.

        Returns:
            The function used for conversion to a dictionary or nothing
        """
        return self._asdict(suffix=f"_j_{ContentView.NORMAL!s}")

    def serialize_yaml_full(self) -> OverrideDictReturn:
        """Provide dictionary factory for ``YAML`` with all attributes.

        Returns:
            The function used for conversion to a dictionary or nothing
        """
        return self._asdict(suffix=f"_y_{ContentView.FULL!s}")

    def serialize_yaml_normal(self) -> OverrideDictReturn:
        """Provide dictionary factory for ``JSON`` with curated attributes.

        Returns:
            The function used for conversion to a dictionary or nothing
        """
        return self._asdict(suffix=f"_y_{ContentView.NORMAL!s}")

    def _asdict(self, suffix: Any) -> OverrideDictReturn:
        """Create a dictionary from the dataclass with suffixed values.

        Args:
            suffix: The suffix to append to values

        Returns:
            The dictionary with suffixed values
        """
        return asdict(self, dict_factory=partial(self._custom_dict_factory, suffix=suffix))

    @staticmethod
    def _custom_dict_factory(
        kv_pairs: list[tuple[str, OverrideAllValues]],
        suffix: str,
    ) -> OverrideDictReturn:
        """Create a dictionary with suffixed values from a list of key-value pairs.

        Args:
            kv_pairs: The key-value pairs provided by
                ``dataclasses.asdict()``
            suffix: The suffix to append to values

        Returns:
            The dictionary with suffixed values
        """
        return {name: f"{value!s}_{suffix}" for name, value in kv_pairs}


parametrize_content_views = pytest.mark.parametrize(**ParametrizeView()._asdict())
parametrize_serialization_format = pytest.mark.parametrize(**ParametrizeFormat()._asdict())


@parametrize_serialization_format
@parametrize_content_views
def test_content_to_dict(
    content_view: ContentView,
    serialization_tuple: tuple[str, SerializationFormat],
) -> None:
    """Test the conversion of the dataclass to a dict.

    Args:
        content_view: The content view
        serialization_tuple: The suffix, serialization format
    """
    content = ContentTestSimple()
    content_as_dict = content.asdict(
        serialization_format=serialization_tuple[1],
        content_view=content_view,
    )
    assert content_as_dict == {"attr_01": False, "attr_02": 2, "attr_03": "three"}


@parametrize_content_views
def test_content_to_json(content_view: ContentView) -> None:
    """Test the conversion of the dataclass to json.

    Args:
        content_view: The content view
    """
    content = ContentTestSimple()
    content_serialized = serialize(
        content=content,
        content_view=content_view,
        serialization_format=SerializationFormat.JSON,
    )
    expected = '{\n    "attr_01": false,\n    "attr_02": 2,\n    "attr_03": "three"\n}'
    assert content_serialized == expected


@parametrize_content_views
def test_content_to_yaml(content_view: ContentView) -> None:
    """Test the conversion of the dataclass to yaml.

    Args:
        content_view: The content view
    """
    content = ContentTestSimple()
    content_serialized = serialize(
        content=content,
        content_view=content_view,
        serialization_format=SerializationFormat.YAML,
    )
    expected = "---\nattr_01: false\nattr_02: 2\nattr_03: three\n"
    assert content_serialized == expected


@parametrize_serialization_format
@parametrize_content_views
def test_content_to_dict_override(
    subtests: Any,
    content_view: ContentView,
    serialization_tuple: tuple[str, SerializationFormat],
) -> None:
    """Test the conversion of the dataclass with overrides to a ``dict``.

    Args:
        subtests: The pytest subtest fixture
        content_view: The content view
        serialization_tuple: The suffix, serialization format
    """
    content = ContentTestOverride()
    content_as_dict = content.asdict(
        content_view=content_view,
        serialization_format=serialization_tuple[1],
    )
    for key, value in content_as_dict.items():
        with subtests.test(msg=key, value=value):
            assert value.endswith(f"_{serialization_tuple[0]}_{content_view!s}")


@parametrize_content_views
def test_content_to_json_override(content_view: ContentView) -> None:
    """Test the conversion of the dataclass with overrides to ``JSON``.

    Args:
        content_view: The content view
    """
    content = ContentTestOverride()
    content_serialized = serialize(
        content=content,
        content_view=content_view,
        serialization_format=SerializationFormat.JSON,
    )
    expected_template = (
        '{{\n    "attr_01": "False__j_{view}",\n'
        '    "attr_02": "2__j_{view}",\n'
        '    "attr_03": "three__j_{view}"\n}}'
    )
    assert content_serialized == expected_template.format(view=content_view)


@parametrize_content_views
def test_content_to_yaml_override(content_view: ContentView) -> None:
    """Test the conversion of the dataclass with overrides to ``YAML``.

    Args:
        content_view: The content view
    """
    content = ContentTestOverride()
    content_serialized = serialize(
        content=content,
        content_view=content_view,
        serialization_format=SerializationFormat.YAML,
    )
    expected_template = (
        "---\nattr_01: False__y_{view}\nattr_02: 2__y_{view}\nattr_03: three__y_{view}\n"
    )
    assert content_serialized == expected_template.format(view=content_view)
