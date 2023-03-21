"""Main module."""

import logging
import typing as t

from fw_gear_file_validator import validator

log = logging.getLogger(__name__)


def run(
    schema: str,
    input_json: t.Dict,
) -> t.Tuple[bool, t.List[t.Dict]]:
    """runs the validation and returns valid (T|F) and packaged errors

    Args:
        schema_file_path: the location of the schema file to use for validation
        schema_file_type: the type of schema file to be used to determine validation strategy
        input_file_path: the location of the file to validate
        output_dir: the direcory to save outputs in (error csv file)

    Returns:
        valid: True if the file passed validation, False otherwise

    """
    schema_validator = validator.JsonValidator(schema)
    valid, errors = schema_validator.validate(input_json)

    return valid, errors
