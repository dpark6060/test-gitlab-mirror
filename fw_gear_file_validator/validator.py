import json
import typing as t
from pathlib import Path

import jsonschema
from jsonschema.exceptions import ValidationError

from fw_gear_file_validator import utils

# We are not supporting array, object, or null.
JSON_TYPES = {"string": str, "number": float, "integer": int, "boolean": bool}


class JsonValidator:
    """Json Validator class."""

    def __init__(self, schema: t.Union[dict, Path, str]):
        if isinstance(schema, str):
            schema = Path(schema)
        if isinstance(schema, Path):
            with open(schema, "r", encoding="UTF-8") as schema_instance:
                schema = json.load(schema_instance)
        self.validator = jsonschema.Draft7Validator(schema)

    def validate(self, d: dict) -> t.Tuple[bool, t.List[t.Dict]]:
        valid, errors = self.process(d)
        return valid, errors

    def process(
        self, d: dict, reformat_error: bool = True
    ) -> t.Tuple[bool, t.List[t.Dict]]:
        """Validates a dict and returns a tuple of valid and formatted errors."""
        errors = list(self.validator.iter_errors(d))
        valid = False if errors else True
        if errors and reformat_error:
            errors = self.handle_errors(errors)
        return valid, errors

    @staticmethod
    def handle_errors(errors: list[ValidationError]) -> t.List[t.Dict]:
        """Processes errors into a standard output format.
        A jsonschema error in python has the following data structure:
        {
            'message': '[1, 2, 3, 4] is too long',
             'path': deque(['list']),
             'relative_path': deque(['list']),
             'schema_path': deque(['properties', 'list', 'maxItems']),
             'relative_schema_path': deque(['properties', 'list', 'maxItems']),
             'context': [],
             'cause': None,
             'validator': 'maxItems',
             'validator_value': 3,
             'instance': [1, 2, 3, 4],
             'schema': {'type': 'array', 'maxItems': 3},
             'parent': None,
             '_type_checker': <TypeChecker types={'array', 'boolean', 'integer', 'null', 'number', 'object', 'string'}>
         }

        This must be converted to the FW Error standard:
        type: str – “error” (always error)
        code: str – Type of the error (e.g. MaxLength)
        location: str – Location of the error
        flywheel_path: str – Flywheel path to the container/file
        container_id: str – ID of the source container/file
        value: str – current value
        expected: str – expected value
        message: str – error message description
        Additionally, the value for location will be formatted as such:
        For JSON input file: { “key_path”: string }, with string being the JSON key

        The flywheel relative items will be handled by a later function.
        They are omitted here to keep json validator flywheel client independent.
        These items are:
            - flywheel_path
            - container_id

        """

        errors = sorted(errors, key=lambda e: e.path)

        error_report = []
        for error in errors:
            error_report.append(
                {
                    "type": "error",  # For now, jsonValidaor can only produce errors.
                    "code": str(error.validator),
                    "location": {"key_path": ".".join(list(error.schema_path)[:-1])},
                    "value": str(error.instance),
                    "expected": str(error.schema),
                    "message": error.message,
                }
            )
        return error_report


class CsvValidator(JsonValidator):
    """CSV Validator class."""

    def __init__(self, schema: t.Union[dict, Path, str]):
        super().__init__(schema)

    def get_column_dtypes(self):
        column_types = {}
        schema = self.validator.schema
        for schema_property, property_val in schema["properties"].items():
            if "$ref" in property_val:
                _, property_val = self.validator.resolver.resolve(property_val["$ref"])
            json_type = property_val.get("type")
            column_types[schema_property] = self.convert_json_types_to_python(json_type)
        return column_types

    @staticmethod
    def convert_json_types_to_python(json_type: str) -> type:
        if isinstance(json_type, list):
            raise ValueError(
                "Multiple possible datatypes not allowed for csv validation.  Check your schema."
            )
        return JSON_TYPES.get(json_type, str)  # default to type str if not supported

    def validate(self, csv_dict: t.List[t.Dict]) -> t.Tuple[bool, t.List[t.Dict]]:
        csv_valid = True
        csv_errors = []
        column_types = self.get_column_dtypes()
        for (
            row_num,
            row_contents,
        ) in enumerate(csv_dict):
            cast_row = {
                key: utils.cast_csv_val(value, column_types[key])
                for key, value in row_contents.items()
            }
            valid, errors = self.process(cast_row)
            csv_valid = csv_valid & valid
            self.add_csv_location_spec(row_num, errors)
            csv_errors.extend(errors)
        return csv_valid, csv_errors

    @staticmethod
    def add_csv_location_spec(row_num, row_errors):
        for error in row_errors:
            # The old location will be something like "{'key_path': 'properties.Col2'}"
            # We just want the column name (Col2), so we extract it like this:
            col_name = error["location"]["key_path"].split(".")[-1]
            error["location"] = {"line": row_num + 1, "column_name": col_name}


def initialize_validator(
    file_type: str, schema: t.Union[dict, Path, str]
) -> t.Union[JsonValidator, CsvValidator]:
    """Initialize the validator.

    In the future we may implement a recursive subclass factory (or something),
    but for two validators the code does not require that complexity.

    Args:
        file_type: the type of file we're validating
        schema: the validation JSON schema file.

    Returns:
        JsonValidator | CsvValidator

    """
    if file_type == "json":
        return JsonValidator(schema)
    elif file_type == "csv":
        return CsvValidator(schema)
    else:
        raise ValueError("file type " + file_type + " Not supported")
