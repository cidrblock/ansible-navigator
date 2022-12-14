"""Functionality related to the retrieval of packaged data files."""

from .compatibility import importlib_resources


def retrieve_content(app_name: str, filename: str) -> str:
    """Retrieve the content of a packaged data file.

    :param app_name: The name of the application.
    :param filename: The name of the file to retrieve.
    :returns: The content of the file.
    """
    data_directory = "data"
    package = f"{app_name}.{data_directory}"
    with importlib_resources.open_text(package, filename) as fh:
        content = fh.read()

    return content
