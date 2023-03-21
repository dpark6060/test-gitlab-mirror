from fw_gear_file_validator import validator


def test_process():
    schema = {"properties": {"list": {"type": "array", "maxItems": 3}}}
    json_object = {"list": [1, 2, 3]}
    jvalidator = validator.JsonValidator(schema)
    valid, errors = jvalidator.process(json_object)
    assert valid
    assert errors == {}

    json_object = {"list": [1, 2, 3, 4]}
    jvalidator = validator.JsonValidator(schema)
    valid, errors = jvalidator.process(json_object)
    assert not valid
    assert len(errors) == 1
