"""Tests for doc from welcome, interactive, with an EE."""

from __future__ import annotations

import pytest

from .base import BaseClass


# module doc
CLI_MODULE_DOC = "ansible-navigator --execution-environment true"

testdata_module_doc = [
    pytest.param(0, CLI_MODULE_DOC, "welcome", "module_doc_pass", [], id="0"),
    pytest.param(1, ":doc company_name.coll_1.mod_1", "load doc", "module_doc_pass", [], id="1"),
    pytest.param(2, ":{{ examples }}", "load examples", "module_doc_pass", [], id="2"),
]

# lookup plugin doc
CLI_LOOKUP_DOC = "ansible-navigator --execution-environment true"

testdata_lookup_doc = [
    pytest.param(0, CLI_LOOKUP_DOC, "welcome", "lookup_doc_pass", [], id="0"),
    pytest.param(
        1,
        ":doc company_name.coll_1.lookup_1 -t lookup",
        "load doc",
        "lookup_doc_pass",
        [],
        id="1",
    ),
]

# filter plugin doc
CLI_FILTER_DOC = "ansible-navigator --execution-environment true"

testdata_filter_doc = [
    pytest.param(0, CLI_FILTER_DOC, "welcome", "filter_doc_pass", [], id="0"),
    pytest.param(
        1,
        ":doc company_name.coll_1.filter_1 -t filter",
        "load doc",
        "filter_doc_pass",
        [],
        id="1",
    ),
]

# plugin does not exist
CLI_WRONG_MODULE_NOT_EXIST = "ansible-navigator --execution-environment true"

testdata_module_doc_not_exist = [
    pytest.param(0, CLI_WRONG_MODULE_NOT_EXIST, "welcome", "module_doc_fail", [], id="0"),
    pytest.param(
        1,
        ":doc company_name.coll_1.doesnotexist",
        "ansible-navigator doc wrong plugin name",
        "module_doc_fail",
        [
            "WARNING",
            "module",
            "company_name.coll_1.doesnotexist",
            "not",
            "found",
            "execution_environment_errors",
        ],
        id="1",
    ),
]


@pytest.mark.parametrize(
    ("index", "user_input", "comment", "testname", "expected_in_output"),
    testdata_module_doc,
)
class TestModuleDoc(BaseClass):
    """Run the tests for doc from welcome, interactive, with an EE, module doc."""

    TEST_FOR_MODE = "interactive"
    UPDATE_FIXTURES = False


@pytest.mark.parametrize(
    ("index", "user_input", "comment", "testname", "expected_in_output"),
    testdata_lookup_doc,
)
class TestLookUpDoc(BaseClass):
    """Run the tests for doc from welcome, interactive, with an EE, lookup doc."""

    TEST_FOR_MODE = "interactive"
    UPDATE_FIXTURES = False


@pytest.mark.parametrize(
    ("index", "user_input", "comment", "testname", "expected_in_output"),
    testdata_filter_doc,
)
class TestFilterDoc(BaseClass):
    """Run the tests for doc from welcome, interactive, with an EE, filter doc."""

    TEST_FOR_MODE = "interactive"
    UPDATE_FIXTURES = False


@pytest.mark.parametrize(
    ("index", "user_input", "comment", "testname", "expected_in_output"),
    testdata_module_doc_not_exist,
)
class TestModuleDocNotExist(BaseClass):
    """Run the tests for doc from welcome, interactive, with an EE, doc not found."""

    TEST_FOR_MODE = "interactive"
    UPDATE_FIXTURES = False
