"""JSONL (JSON Lines) serialization utilities for the ablation framework.

This module provides functions for serializing and deserializing data to and from JSONL format.
JSONL stores each JSON object on a separate line, making it more efficient for large datasets.
"""

import json
import logging
from typing import Any, Generator, List, Union

from ..models import ActivityData, TruthData
from .serialization import AblationJSONEncoder, to_dict, from_dict

logger = logging.getLogger(__name__)


def to_jsonl_line(data: Union[ActivityData, TruthData, dict[str, Any]]) -> str:
    """Convert a single object to a JSONL line.

    Args:
        data: The data to convert.

    Returns:
        str: A single line of JSONL (no pretty printing, no trailing newline).
    """
    # Convert to dictionary
    data_dict = to_dict(data)

    # Convert to JSON without indentation or newlines
    return json.dumps(data_dict, cls=AblationJSONEncoder)


def batch_to_jsonl(data_list: List[Union[ActivityData, TruthData, dict[str, Any]]]) -> str:
    """Convert a list of objects to JSONL format.

    Args:
        data_list: The list of data to convert.

    Returns:
        str: The data in JSONL format (each object on a separate line).
    """
    # Convert each item to a JSONL line and join with newlines
    return "\n".join(to_jsonl_line(data) for data in data_list)


def from_jsonl_line(jsonl_line: str) -> Union[ActivityData, TruthData]:
    """Convert a JSONL line to an object.

    Args:
        jsonl_line: A single line of JSONL.

    Returns:
        Union[ActivityData, TruthData]: The converted object.
    """
    # Parse the JSON line
    data = json.loads(jsonl_line)

    # Convert to an object
    return from_dict(data)


def batch_from_jsonl(jsonl_str: str) -> List[Union[ActivityData, TruthData]]:
    """Convert a JSONL string to a list of objects.

    Args:
        jsonl_str: A string in JSONL format.

    Returns:
        List[Union[ActivityData, TruthData]]: The converted objects.
    """
    # Split into lines and filter out empty lines
    lines = [line.strip() for line in jsonl_str.splitlines() if line.strip()]

    # Convert each line
    return [from_jsonl_line(line) for line in lines]


def save_to_jsonl_file(data_list: List[Union[ActivityData, TruthData, dict[str, Any]]], file_path: str) -> None:
    """Save a list of data to a file in JSONL format.

    Args:
        data_list: The list of data to save.
        file_path: The file path.
    """
    # Convert to JSONL
    jsonl_str = batch_to_jsonl(data_list)

    # Write to file
    with open(file_path, "w") as f:
        f.write(jsonl_str)


def load_from_jsonl_file(file_path: str) -> List[Union[ActivityData, TruthData]]:
    """Load a list of data from a JSONL file.

    Args:
        file_path: The file path.

    Returns:
        List[Union[ActivityData, TruthData]]: The loaded data.
    """
    # Read from file
    with open(file_path) as f:
        jsonl_str = f.read()

    # Convert from JSONL
    return batch_from_jsonl(jsonl_str)


def stream_from_jsonl_file(file_path: str) -> Generator[Union[ActivityData, TruthData], None, None]:
    """Stream data from a JSONL file, yielding one object at a time.

    This is more memory-efficient for large files than loading the entire file at once.

    Args:
        file_path: The file path.

    Yields:
        Union[ActivityData, TruthData]: Each object from the file.
    """
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                yield from_jsonl_line(line)


def stream_to_jsonl_file(data_iterable: List[Union[ActivityData, TruthData, dict[str, Any]]], file_path: str) -> None:
    """Stream data to a JSONL file, writing one object at a time.

    This is more memory-efficient for large datasets than saving all at once.

    Args:
        data_iterable: An iterable of data to save.
        file_path: The file path.
    """
    with open(file_path, "w") as f:
        for data in data_iterable:
            jsonl_line = to_jsonl_line(data)
            f.write(jsonl_line + "\n")
