#!/usr/bin/env python
"""The run script"""
import json
import logging

from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_file_validator.loaders import FwLoader
from fw_gear_file_validator.main import run
from fw_gear_file_validator.parser import parse_config
from fw_gear_file_validator.utils import (
    add_flywheel_location_to_errors,
    handle_metadata,
    save_errors,
)
from fw_gear_file_validator.validator import JsonValidator

log = logging.getLogger(__name__)


def main(context: GearToolkitContext) -> None:  # pragma: no cover
    """Parses gear config, runs main algorithm, and performs flywheel-specific actions."""

    (
        debug,
        tag,
        validation_level,
        file_type,
        add_parents,
        schema_path,
        reference,
    ) = parse_config(context)

    # loading input dict
    if validation_level == "file":
        loader = FileLoader(
            file_type=...
        )  # uniffied loader for JSON, YAML, XML, CSV, etc.
        d = loader.load(context.get_input_path("input_file"))
        schema = loader.load_schema(schema_path)
    elif validation_level == "flywheel":
        loader = FwLoader(
            context=context,
            add_parents=add_parents,
        )
        d = loader.load(reference)
        schema = loader.load_schema(schema_path)
    else:
        raise ValueError(f"Validation level {validation_level} unsupported")

    # Validate
    validator = JsonValidator(schema)
    valid, errors = validator.validate(d)

    # Format output
    errors = add_flywheel_location_to_errors(
        flywheel_hierarchy, validation_level, errors
    )
    save_errors(errors, context.output_dir)

    handle_metadata(context, strategy, valid, tag)


# Only execute if file is run as main, not when imported by another module
if __name__ == "__main__":  # pragma: no cover
    # Get access to gear config, inputs, and sdk client if enabled.
    with GearToolkitContext() as gear_context:
        # Initialize logging, set logging level based on `debug` configuration
        # key in gear config.
        gear_context.init_logging()

        # Pass the gear context into main function defined above.
        main(gear_context)
