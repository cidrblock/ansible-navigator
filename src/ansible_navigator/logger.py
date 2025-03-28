"""Logging initialization."""

from __future__ import annotations

import datetime
import logging
import zoneinfo

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from .configuration_subsystem import Constants


if TYPE_CHECKING:
    from .configuration_subsystem.definitions import ApplicationConfiguration


logger = logging.getLogger("ansible_navigator")


class Formatter(logging.Formatter):
    """Format a logging timestamp using a time zone."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the logging formatter.

        Args:
            *args: The arguments
            **kwargs: The keyword arguments
        """
        self._time_zone = kwargs.pop("time_zone")
        super().__init__(*args, **kwargs)

    def formatTime(  # noqa: N802
        self,
        record: logging.LogRecord,
        _datefmt: str | None = None,
    ) -> str:
        """Format the log timestamp.

        Args:
            record: The log record
            _datefmt: The optional date format

        Returns:
            The timestamp
        """
        if self._time_zone == "local":
            return (
                datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc)
                .astimezone()
                .isoformat()
            )
        return datetime.datetime.fromtimestamp(
            record.created,
            tz=zoneinfo.ZoneInfo(self._time_zone),
        ).isoformat()


def setup_logger(args: ApplicationConfiguration) -> None:
    """Set up the logger.

    Args:
        args: The CLI args
    """
    if Path(args.log_file).exists() and args.log_append is False:
        Path(args.log_file).unlink()
    handler = logging.FileHandler(args.log_file)

    time_zone = args.entry("time_zone").value.current
    # When the configuration is rolled back, the time_zone will be C.NOT_SET
    if isinstance(args.time_zone, Constants):
        time_zone = args.entry("time_zone").value.default

    formatter = Formatter(
        fmt="%(asctime)s %(levelname)s '%(name)s.%(funcName)s' %(message)s",
        time_zone=time_zone,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    log_level = getattr(logging, args.log_level.upper())
    logger.setLevel(log_level)
    logger.info("New %s instance, logging initialized", args.application_name_dashed)

    # set ansible-runner logs
    runner_logger = logging.getLogger("ansible-runner")
    runner_logger.setLevel(log_level)
    runner_logger.addHandler(handler)
    logger.info("New ansible-runner instance, logging initialized")
