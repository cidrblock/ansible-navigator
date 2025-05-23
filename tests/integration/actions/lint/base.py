"""Base class for lint interactive tests."""

from __future__ import annotations

import difflib
import os

from typing import TYPE_CHECKING

import pytest

from tests.defaults import FIXTURES_DIR
from tests.integration._common import retrieve_fixture_for_step
from tests.integration._common import update_fixtures
from tests.integration._interactions import SearchFor
from tests.integration._interactions import UiTestStep
from tests.integration._tmux_session import TmuxSession
from tests.integration._tmux_session import TmuxSessionKwargs


if TYPE_CHECKING:
    from collections.abc import Generator


LINT_FIXTURES = FIXTURES_DIR / "integration" / "actions" / "lint"


class BaseClass:
    """Base class for interactive lint tests."""

    UPDATE_FIXTURES = False

    @staticmethod
    @pytest.fixture(scope="module", name="tmux_session")
    def fixture_tmux_session(request: pytest.FixtureRequest) -> Generator[TmuxSession]:
        """Tmux fixture for this module.

        Args:
            request: Pytest request object
        :yields: TmuxSession object
        """
        params: TmuxSessionKwargs = {
            "request": request,
        }
        with TmuxSession(**params) as tmux_session:
            yield tmux_session

    def test(
        self,
        request: pytest.FixtureRequest,
        tmux_session: TmuxSession,
        step: UiTestStep,
        skip_if_already_failed: None,
    ) -> None:
        """Run the tests for lint, mode and ``ee`` set in child class.

        Args:
            request: Pytest request object
            tmux_session: TmuxSession fixture
            step: UiTestStep object
        """
        search_within_response: str | list[str]
        if step.search_within_response is SearchFor.HELP:
            search_within_response = ":help help"
        elif step.search_within_response is SearchFor.PROMPT:
            search_within_response = tmux_session.cli_prompt
        elif step.search_within_response is SearchFor.WARNING:
            search_within_response = "WARNING"
        else:
            search_within_response = step.search_within_response

        received_output = tmux_session.interaction(
            value=step.user_input,
            search_within_response=search_within_response,
        )

        fixtures_update_requested = (
            self.UPDATE_FIXTURES
            or os.environ.get("ANSIBLE_NAVIGATOR_UPDATE_TEST_FIXTURES") == "true"
        )
        if fixtures_update_requested:
            update_fixtures(
                request,
                step.step_index,
                received_output,
                step.comment,
                additional_information={
                    "present": step.present,
                    "absent": step.absent,
                    "compared_fixture": not any((step.present, step.absent)),
                },
            )

        page = " ".join(received_output)

        if step.present:
            assert all(present in page for present in step.present)

        if step.absent:
            assert not any(absent in page for absent in step.absent)

        if not any((step.present, step.absent)):
            expected_output = retrieve_fixture_for_step(request, step.step_index)
            assert expected_output == received_output, "\n" + "\n".join(
                difflib.unified_diff(expected_output, received_output, "expected", "received"),
            )
