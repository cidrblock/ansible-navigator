"""image puller"""
import logging
import shlex
import subprocess

from types import SimpleNamespace
from typing import List

from ..utils import ExitMessage
from ..utils import ExitPrefix
from ..utils import LogMessage


class ImageAssessment(SimpleNamespace):
    """report the findings"""

    messages: List[LogMessage]
    exit_messages: List[ExitMessage]
    pull_required: bool


class ImagePuller:
    # pylint: disable=too-many-instance-attributes
    """Image puller"""

    def __init__(self, container_engine: str, image: str, arguments: List, policy: str):
        """Initialize the container image puller.

        :param container_engine: The name of the container engine
        :param image: The name of the image to pull
        :param arguments: Additional arguments to be appended to the pull policy
        :param policy: The current pull policy from the settings
        """
        self._arguments: List = arguments
        self._assessment = ImageAssessment
        self._container_engine = container_engine
        self._exit_messages: List[ExitMessage] = []
        self._image = image
        self._image_present: bool
        self._image_tag: str
        self._logger = logging.getLogger(__name__)
        self._messages: List[LogMessage] = []
        self._policy: str = policy
        self._pull_required: bool = False

    def assess(self):
        """assess need to pull"""
        self._extract_tag()
        self._check_for_image()
        self._determine_pull()
        if self._policy == "never" and self._image_present is False:
            exit_msg = (
                "Pull policy is set to 'never' and execution environment"
                " image was not found locally"
            )
            self._log_message(message=exit_msg, level=logging.ERROR)
            exit_msg = (
                "Try again with '--pp missing' or manually pull the execution environment image"
            )
            self._log_message(level=logging.INFO, message=exit_msg, hint=True)

        self._assessment = ImageAssessment(
            messages=self._messages,
            exit_messages=self._exit_messages,
            pull_required=self._pull_required,
        )

    @property
    def assessment(self):
        """return am image assessment"""
        return self._assessment

    def _check_for_image(self):
        try:
            subprocess.run(
                [self._container_engine, "image", "inspect", self._image],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._image_present = True

        except subprocess.CalledProcessError as exc:
            self._image_present = False
            if "no such image" not in str(exc.stderr).lower():
                message = "Image inspection failed, image assumed to be corrupted or missing"
                self._log_message(level=logging.WARNING, message=message)

    def _determine_pull(self):
        if self._policy == "missing" and self._image_present is False:
            pull = True
        elif self._policy == "always":
            pull = True
        elif self._policy == "tag" and self._image_tag == "latest":
            pull = True
        elif self._policy == "tag" and self._image_present is False:
            pull = True
        else:
            pull = False
        self._pull_required = pull
        self._assessment.pull_required = pull

    def _extract_tag(self):
        image_pieces = self._image.split(":")
        self._image_tag = "latest"
        if len(image_pieces) > 1:
            tag = image_pieces[-1]
            if "/" not in tag:
                # If there's a slash in the tag, it means we were probably given
                # an image name that has a port number but no tag at the end.
                # e.g.: registry.example.com:443/my/image
                # In this case, we /don't/ want "443/my/image" to be considered
                # a tag. Only if the ending doesn't have a slash in it, is it a
                # valid tag.
                self._image_tag = tag
        message = f"Image tag is: {self._image_tag}"
        self._log_message(level=logging.INFO, message=message)

    def _log_message(self, message: str, level: int, hint=False):
        if level == logging.ERROR:
            self._exit_messages.append(ExitMessage(message=message))
        elif hint:
            self._exit_messages.append(ExitMessage(message=message, prefix=ExitPrefix.HINT))
        else:

            self._messages.append(LogMessage(level=level, message=message))
        self._logger.log(level=level, msg=message)

    def prologue_stdout(self):
        """print a little value added information"""
        messages = [("Execution environment image name:", self._image)]
        messages.append(("Execution environment image tag:", self._image_tag))
        if isinstance(self._arguments, list):
            arguments = " ".join(shlex.quote(arg) for arg in self._arguments)
        else:
            arguments = "None"
        messages.append(("Execution environment pull arguments:", arguments))
        messages.append(("Execution environment pull policy:", self._policy))
        messages.append(("Execution environment pull needed:", self._pull_required))

        width = max((len(m[0]) + len(str(m[1])) + 2 for m in messages))
        print("\u002d" * width)
        print("Execution environment image and pull policy overview")
        print("\u002d" * width)
        column_width = max((len(m[0]) for m in messages))
        for msg, value in messages:
            print(f"{msg.ljust(column_width)} {value}")
            self._log_message(message=f"{msg}: {value}", level=logging.INFO)
        print("\u002d" * width)
        print("Updating the execution environment")
        print("\u002d" * width)

    def _generate_pull_command(self) -> List:
        """Generate the pull command.

        :returns: The list of command parts
        """
        command_line = [self._container_engine, "pull"]
        if isinstance(self._arguments, list):
            for argument in self._arguments:
                command_line.extend(shlex.split(argument))
        command_line.append(self._image)
        return command_line

    def pull_stdout(self):
        """pull the image, print to stdout

        podman writes to stderr
        docker writes to stdout
        """
        try:
            command_line = self._generate_pull_command()
            shlex_joined = " ".join(shlex.quote(arg) for arg in command_line)
            print(f"Running the command: {shlex_joined}")
            if self._container_engine == "podman":
                subprocess.run(command_line, check=True)
            elif self._container_engine == "docker":
                subprocess.run(
                    command_line,
                    check=True,
                    stderr=subprocess.PIPE,
                )
            else:
                raise ValueError("Unknown container engine")

            self._log_message(level=logging.INFO, message="Execution environment updated")
            self._pull_required = False
            self._assessment.pull_required = False
        except subprocess.CalledProcessError as exc:
            self._log_message(level=logging.ERROR, message="Execution environment pull failed")
            if exc.stderr is not None:
                self._log_message(level=logging.ERROR, message=exc.stderr.decode().strip())
            exit_msg = (
                "Check the execution environment image name, connectivity to and permissions"
                " for the registry, and try again"
            )
            self._log_message(level=logging.INFO, message=exit_msg, hint=True)
