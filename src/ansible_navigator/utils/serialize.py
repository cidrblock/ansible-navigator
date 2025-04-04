"""Abstractions for common serialization formats."""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile

from dataclasses import is_dataclass
from functools import partial
from pathlib import Path
from typing import IO
from typing import Any
from typing import NamedTuple

import yaml

from ansible_navigator.content_defs import ContentBase
from ansible_navigator.content_defs import ContentFormat
from ansible_navigator.content_defs import ContentType
from ansible_navigator.content_defs import ContentView
from ansible_navigator.content_defs import SerializationFormat


logger = logging.getLogger(__name__)

try:
    from yaml import CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeDumper  # type: ignore

try:
    from yaml import CLoader as Loader
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import Loader  # type: ignore
    from yaml import SafeLoader  # type: ignore


def serialize(
    content: ContentType,
    content_view: ContentView,
    serialization_format: SerializationFormat,
) -> str | None:
    """Serialize a dataclass based on format and view.

    Args:
        content: The content dataclass to serialize
        content_view: The content view
        serialization_format: The serialization format

    Raises:
        ValueError: When serialization format is not recognized

    Returns:
        The serialized content
    """
    dumpable = _prepare_content(
        content=content,
        content_view=content_view,
        serialization_format=serialization_format,
    )
    if serialization_format == SerializationFormat.YAML:
        return _yaml_dumps(dumpable=dumpable)
    if serialization_format == SerializationFormat.JSON:
        return _json_dumps(dumpable=dumpable)
    msg = "Unknown serialization format"
    raise ValueError(msg)


def serialize_write_file(
    content: ContentType,
    content_view: ContentView,
    file_mode: str,
    file: Path,
    serialization_format: SerializationFormat,
) -> None:
    """Serialize and write content to a file.

    Args:
        content: The content to serialize
        content_view: The content view
        file_mode: The file mode for the file
        file: The file to write to
        serialization_format: The serialization format

    Raises:
        ValueError: When serialization format is not recognized
    """
    dumpable = _prepare_content(
        content=content,
        content_view=content_view,
        serialization_format=serialization_format,
    )
    with file.open(mode=file_mode, encoding="utf-8") as file_handle:
        if serialization_format == SerializationFormat.JSON:
            _json_dump(dumpable=dumpable, file_handle=file_handle)
            return
        if serialization_format == SerializationFormat.YAML:
            _yaml_dump(dumpable=dumpable, file_handle=file_handle)
            return
    msg = "Unknown serialization format"
    raise ValueError(msg)


def serialize_write_temp_file(
    content: ContentType,
    content_view: ContentView,
    content_format: ContentFormat,
) -> Path:
    """Serialize and write content to a premanent temporary file.

    Args:
        content: The content to serialize
        content_view: The content view
        content_format: The content format

    Raises:
        ValueError: When serialization format is not recognized

    Returns:
        A ``Path`` to the file written to
    """
    serialization_format = content_format.value.serialization
    suffix = content_format.value.file_extension

    if serialization_format is not None:
        dumpable = _prepare_content(
            content=content,
            content_view=content_view,
            serialization_format=serialization_format,
        )
    else:
        dumpable = content

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w+t") as file_like:
        if content_format == ContentFormat.JSON:
            _json_dump(dumpable=dumpable, file_handle=file_like)
            return Path(file_like.name)
        if content_format == ContentFormat.YAML:
            _yaml_dump(dumpable=dumpable, file_handle=file_like)
            return Path(file_like.name)
        _text_dump(dumpable=str(dumpable), file_handle=file_like)
        return Path(file_like.name)
    msg = "Unknown serialization format"
    raise ValueError(msg)


SERIALIZATION_FAILURE_MSG = (
    "The requested content could not be converted to {serialization_format}.\n"
    "The content was {content}\n"
    "Please log an issue for this, it should not have happened\n"
    "Error details: {exception_str}\n"
)


def _prepare_content(
    content: ContentType,
    content_view: ContentView,
    serialization_format: SerializationFormat,
) -> ContentType:
    """Prepare content for serialization.

    Args:
        content: The content to prepare
        content_view: The content view
        serialization_format: The serialization format

    Returns:
        The prepared content
    """
    if isinstance(content, tuple | list):
        if all(is_dataclass(c) for c in content):
            return [
                c.asdict(
                    content_view=content_view,
                    serialization_format=serialization_format,
                )
                for c in content
            ]
        return content
    if isinstance(content, bool | dict | float | int | str):
        return content
    if isinstance(content, ContentBase):
        return content.asdict(
            content_view=content_view,
            serialization_format=serialization_format,
        )

    # This is a big chance, it suggests all content is
    # one of ``ContentType``. the thinking is it's better
    # to error here early, then return a str(content)
    # Ideally this get caught in testing
    value_error = "Content type not recognized"
    error = SERIALIZATION_FAILURE_MSG.format(
        content=str(content),
        exception_str=value_error,
        serialization_format=serialization_format.value,
    )
    error += f"Content view: {content_view}\n"
    return error


class JsonParams(NamedTuple):
    """The parameters for json dump and dumps."""

    indent: int = 4
    sort_keys: bool = True
    ensure_ascii: bool = False


def _json_dump(dumpable: ContentType, file_handle: IO[str]) -> None:
    """Serialize the dumpable to json and write to a file.

    Args:
        dumpable: The object to dump
        file_handle: The file handle to write to
    """
    try:
        json.dump(dumpable, file_handle, **JsonParams()._asdict())
        file_handle.write("\n")  # Add newline json does not
    except TypeError as exc:
        error_message = SERIALIZATION_FAILURE_MSG.format(
            content=str(dumpable),
            exception_str=str(exc),
            serialization_format="JSON",
        )
        file_handle.write(error_message)
        logger.exception(error_message)


def _json_dumps(dumpable: ContentType) -> str:
    """Serialize the dumpable to json.

    Args:
        dumpable: The object to serialize

    Returns:
        The object serialized
    """
    try:
        return json.dumps(dumpable, **JsonParams()._asdict())
    except TypeError as exc:
        error_message = SERIALIZATION_FAILURE_MSG.format(
            content=str(dumpable),
            exception_str=str(exc),
            serialization_format="JSON",
        )
        logger.exception(error_message)
        return error_message


def _text_dump(dumpable: str, file_handle: IO[str]) -> None:
    """Write text to a file.

    Args:
        dumpable: The text to write
        file_handle: The file handle to write to
    """
    file_handle.write(dumpable)
    if not dumpable.endswith("\n"):
        file_handle.write("\n")


class YamlStyle(NamedTuple):
    """The parameters for yaml dump."""

    default_flow_style: bool = False
    explicit_start: bool = True
    allow_unicode: bool = True


def _yaml_dump(dumpable: ContentType, file_handle: IO[str]) -> None:
    """Serialize the dumpable to yaml and write to a file.

    Args:
        dumpable: The object to serialize
        file_handle: The file handle to write to
    """
    try:
        yaml.dump(dumpable, file_handle, Dumper=HumanDumper, **YamlStyle()._asdict())
    except yaml.representer.RepresenterError as exc:
        error_message = SERIALIZATION_FAILURE_MSG.format(
            content=str(dumpable),
            exception_str=str(exc),
            serialization_format="YAML",
        )
        file_handle.write(error_message)
        logger.exception(error_message)


def _yaml_dumps(dumpable: ContentType) -> str | None:
    """Serialize the dumpable to yaml.

    Args:
        dumpable: The object to serialize

    Returns:
        The serialized object
    """
    try:
        return yaml.dump(dumpable, Dumper=HumanDumper, **YamlStyle()._asdict())
    except yaml.representer.RepresenterError as exc:
        error_message = SERIALIZATION_FAILURE_MSG.format(
            content=str(dumpable),
            exception_str=str(exc),
            serialization_format="YAML",
        )
        logger.exception(error_message)
        return error_message


class HumanDumper(SafeDumper):
    # pylint: disable=too-many-ancestors
    """An instance of a pyyaml Dumper.

    This deviates from the base to dump a multiline string in a human readable format
    and disables the use of anchors and aliases.
    """

    def ignore_aliases(self, _data: Any) -> bool:
        """Disable the use of anchors and aliases in the given data.

        Args:
            _data: The data used to make the determination

        Returns:
            True, indicating aliases and anchors should not be used
        """
        return True

    def represent_scalar(
        self,
        tag: str,
        value: str,
        style: str | None = None,
    ) -> yaml.nodes.ScalarNode:
        """Represent all multiline strings as block scalars to improve readability for humans.

        Args:
            tag: A custom tag
            value: The value to represent
            style: The style to use

        Returns:
            The serialized multiline string, result of the super scalar
        """
        if style is None and _is_multiline_string(value):
            style = "|"

            # Remove leading or trailing newline and convert tabs to spaces
            # which can cause havoc on yaml blocks
            value = value.strip().expandtabs()

            # Replace some whitespace chars
            value = re.sub(r"[\r]", "", value)

        return super().represent_scalar(tag, value, style)


def _is_multiline_string(value: str) -> bool:
    """Determine if a string is multiline.

    Note:
        Inspired by http://stackoverflow.com/a/15423007/115478.

    Args:
        value: The value to check

    Returns:
        A boolean indicating if the string is multiline
    """
    return any(character in value for character in "\n\r\x1c\x1d\x1e\x85\u2028\u2029")


def opener(path: str, flags: int, mode: int) -> int:
    """Open a file with the given path and flags.

    Args:
        path: The path of the file to open.
        flags: The flags to use when opening the file.
        mode: The mode to use when opening the file.

    Returns:
        The file descriptor of the opened file.
    """
    return os.open(path=path, flags=flags, mode=mode)


def write_diagnostics_json(path: str, mode: int, content: object) -> None:
    """Write a file with the given name.

    Args:
        content: The content we want to write in the file.
        mode: The mode to use when writing the file.
        path: The path of the file to write.
    """
    # Without this, the created file will have 0o777 - 0o022 (default umask) = 0o755 permissions
    oldmask = os.umask(0)

    opener_func = partial(opener, mode=mode)
    with open(path, "w", encoding="utf-8", opener=opener_func) as f:
        f.write(json.dumps(content, indent=4, sort_keys=True))
    os.umask(oldmask)


__all__ = ("Loader", "SafeDumper", "SafeLoader", "SerializationFormat", "yaml")
