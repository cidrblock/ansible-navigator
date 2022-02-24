"""Abstractions for common serialization formats."""

import json

from dataclasses import asdict
from dataclasses import is_dataclass
from typing import IO
from typing import Any
from typing import NamedTuple


class EnhancedJSONEncoder(json.JSONEncoder):
    """An enhanced json encoder accounting for dataclasses."""

    def default(self, o: Any) -> Any:
        """Encode a dataclass as a dictionary, else simply call super.

        :param o: The data needing encoding
        :returns: The data encoded
        """
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


class JsonParams(NamedTuple):
    """The parameters for json dump and dumps."""

    indent: int = 4
    sort_keys: bool = True
    ensure_ascii: bool = False


def json_dump(dumpable: Any, file_handle: IO, params: NamedTuple = JsonParams()) -> None:
    """Serialize and write the dumpable to a file.

    :param dumpable: The object to serialize
    :param file_handle: The file handle to write to
    :param params: Parameters to override the defaults
    """
    json.dump(dumpable, file_handle, cls=EnhancedJSONEncoder, **params._asdict())


def json_dumps(
    dumpable: Any,
    params: NamedTuple = JsonParams(),
) -> str:
    """Serialize the dumpable to json.

    :param dumpable: The object to serialize
    :param params: Parameters to override the defaults
    :returns: The object serialized
    """
    string = json.dumps(dumpable, cls=EnhancedJSONEncoder, **params._asdict())
    return string
