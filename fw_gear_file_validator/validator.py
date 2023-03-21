import json
import typing as t

import jsonschema


class JsonValidator:
    """Validator base class."""

    def __init__(self, schema: dict):
        self.validator = jsonschema.Draft7Validator(schema)

    @classmethod
    def from_file(cls, schema_path: t):
        with open(schema_path, "r") as fp:
            schema = json.load(fp)
            return cls(schema)

    def validate(self, d: dict) -> t.Tuple[bool, t.List[t.Dict]]:
        valid, errors = self.process(d)
        return valid, errors

    def process(self, d: dict) -> t.Tuple[bool, t.List[t.Dict]]:
        """validates a dict object."""

        valid = self.validator.is_valid(d)
        if valid:
            return valid, {}
        errors = self.validator.iter_errors(d)
        packaged_errors = self.handle_errors(errors)
        return valid, packaged_errors

    @staticmethod
    def handle_errors(
        json_schema_errors: t.Generator[
            jsonschema.exceptions.ValidationError, None, None
        ]
    ) -> t.List[t.Dict]:
        """Processes errors into a standard output format."""

        errors = sorted(json_schema_errors, key=lambda e: e.path)
        error_report = []
        for error in errors:
            error_report.append(
                {
                    "Error_Type": str(error.validator),
                    "Error_Location": str(".".join(error.path)),
                    "Value": str(error.instance),
                    "Expected": str(error.schema),
                    "Message": error.message,
                }
            )
        return error_report
