"""Base class for collections interactive tests."""

import difflib
import os

from collections.abc import Generator
from pathlib import Path

import pytest

from tests.defaults import FIXTURES_COLLECTION_DIR
from tests.integration._common import copytree
from tests.integration._common import retrieve_fixture_for_step
from tests.integration._common import update_fixtures
from tests.integration._interactions import SearchFor
from tests.integration._interactions import UiTestStep
from tests.integration._tmux_session import TmuxSession
from tests.integration._tmux_session import TmuxSessionKwargs


EXPECTED_COLLECTIONS = ["ansible.builtin", "company_name.coll_1", "company_name.coll_2"]

base_steps = (
    UiTestStep(user_input=":1", comment="Browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":0", comment="filter_1 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":1", comment="lookup_1 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":2", comment="mod_1 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":3", comment="role_full details window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":4", comment="role_minimal details window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(
        user_input=":back",
        comment="Back to ansible-navigator collections browse window",
        present=EXPECTED_COLLECTIONS,
    ),
    UiTestStep(user_input=":2", comment="Browse company_name.coll_2 plugins window"),
    UiTestStep(user_input=":0", comment="lookup_2 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_2 plugins window"),
    UiTestStep(user_input=":1", comment="mod_2 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_2 plugins window"),
    UiTestStep(
        user_input=":back",
        comment="Back to ansible-navigator collections browse window",
        present=EXPECTED_COLLECTIONS,
    ),
    # Try some things that should not work but not fail (#1061 and #1062)
    UiTestStep(
        user_input=":collections --ee FFFFF",
        comment="Provide an invalid ee value",
        present=["Issues were found while applying the settings"],
        search_within_response=SearchFor.WARNING,
    ),
    # Dismiss the warning
    UiTestStep(
        user_input="Enter",
        comment="ansible-navigator collections browse window",
        present=EXPECTED_COLLECTIONS,
    ),
    # and repeat some basic browsing
    UiTestStep(user_input=":1", comment="Browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":0", comment="filter_1 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(user_input=":1", comment="lookup_1 plugin docs window"),
    UiTestStep(user_input=":back", comment="Back to browse company_name.coll_1 plugins window"),
    UiTestStep(
        user_input=":back",
        comment="Back to ansible-navigator collections browse window",
        present=EXPECTED_COLLECTIONS,
    ),
    UiTestStep(
        user_input=":0",
        comment="Browse ansible.builtin plugins window",
        present=["yum_repository"],
    ),
    UiTestStep(
        user_input=":1",
        comment="Browse ansible.builtin.add_host module",
        present=["ansible.builtin.add_host"],
    ),
)


class BaseClass:
    """Base class for interactive ``collections`` tests."""

    update_fixtures = False
    pane_height = 2000
    pane_width = 200

    @pytest.fixture(scope="module", name="tmux_session")
    def fixture_tmux_session(
        self,
        request: pytest.FixtureRequest,
        os_independent_tmp: str,
    ) -> Generator[TmuxSession, None, None]:
        """Tmux fixture for this module.

        Args:
            request: The request for this fixture
            os_independent_tmp: An OS independent tmp directory
        :yields: A tmux session
        """
        tmp_coll_dir = Path(os_independent_tmp) / request.node.name / ""
        Path(tmp_coll_dir).mkdir(parents=True, exist_ok=True)
        copytree(
            FIXTURES_COLLECTION_DIR,
            Path(tmp_coll_dir) / "collections",
            dirs_exist_ok=True,
        )
        params: TmuxSessionKwargs = {
            "setup_commands": [
                f"cd {tmp_coll_dir}",
                f"export ANSIBLE_COLLECTIONS_PATH={tmp_coll_dir}",
                "export ANSIBLE_DEVEL_WARNING=False",
                "export ANSIBLE_DEPRECATION_WARNINGS=False",
            ],
            "pane_height": self.pane_height,
            "pane_width": self.pane_width,
            "request": request,
        }

        with TmuxSession(**params) as tmux_session:
            yield tmux_session

    def test(
        self,
        os_independent_tmp: str,
        request: pytest.FixtureRequest,
        step: UiTestStep,
        tmux_session: TmuxSession,
        skip_if_already_failed: None,
    ) -> None:
        """Run the tests for ``collections``, mode and ``ee`` set in child class.

        Args:
            os_independent_tmp: An OS independent tmp directory
            request: The request for this fixture
            step: The UI test step
            tmux_session: A tmux session

        Raises:
            ValueError: If test mode is not set
        """
        if step.search_within_response is SearchFor.HELP:
            search_within_response = ":help help"
        elif step.search_within_response is SearchFor.PROMPT:
            search_within_response = tmux_session.cli_prompt
        elif step.search_within_response is SearchFor.WARNING:
            search_within_response = "Warning"
        else:
            msg = "test mode not set"
            raise ValueError(msg)

        received_output = tmux_session.interaction(
            value=step.user_input,
            search_within_response=search_within_response,
        )
        received_output = [
            line.replace(os_independent_tmp, "FIXTURES_COLLECTION_DIR") for line in received_output
        ]

        fixtures_update_requested = (
            self.update_fixtures
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
            assert not any(look_not in page for look_not in step.absent)

        if not any((step.present, step.absent)):
            expected_output = retrieve_fixture_for_step(request, step.step_index)
            assert expected_output == received_output, "\n" + "\n".join(
                difflib.unified_diff(expected_output, received_output, "expected", "received"),
            )
