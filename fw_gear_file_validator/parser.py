"""Parser module to parse gear config.json."""

import os
import typing as t

from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_file_validator.env import (
    SUPPORTED_FILE_EXTENSIONS,
    SUPPORTED_FLYWHEEL_MIMETYPES,
)

level_dict = {"Validate File Contents": "file", "Validate Flywheel Objects": "flywheel"}


# This function mainly parses gear_context's config.json file and returns relevant
# inputs and options.
def parse_config(
    context: GearToolkitContext,
) -> t.Tuple[bool, str, str, bool, str, dict]:
    """parses necessary items out of the context object"""
    debug = context.config.get("debug")
    tag = context.config.get("tag", "file-validator")
    add_parents = context.config.get("add_parents")
    validation_level = context.config.get("validation_level")
    validation_level = level_dict[validation_level]
    schema_file_path = context.get_input_path("validation_schema")

    if context.get_input("input_file"):
        reference = context.destination
        reference["file"] = context.get_input_filename("input_file")
    else:
        reference = context.destination

    return (
        debug,
        tag,
        validation_level,
        add_parents,
        schema_file_path,
        reference
    )


def identify_file_type(input_file: dict) -> str:
    """Given a flywheel config input file object, identify the file type."""
    # First try to just check the file type from the file extension:
    file_name = input_file["location"]["name"]
    base, ext = os.path.splitext(file_name)
    if ext:
        input_file_type = SUPPORTED_FILE_EXTENSIONS.get(ext)
        if input_file_type is None:
            raise TypeError(f"file type {ext} is not supported")
        return input_file_type

    mime = input_file["object"]["mimetype"]
    input_file_type = SUPPORTED_FLYWHEEL_MIMETYPES.get(mime)
    if input_file_type is None:
        raise TypeError(f"file type {mime} is not supported")
    return input_file_type
