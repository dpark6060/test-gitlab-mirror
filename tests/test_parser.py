"""Module to test parser.py"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import flywheel
import pytest

from fw_gear_file_validator import parser

# from fw_gear_{{gear_package}}.parser import parse_config
BASE_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = BASE_DIR / "tests"
test_config = BASE_DIR / "assets" / "config.json"

with open(test_config) as f:
    CONFIG_JSON = json.load(f)
CONFIG_JSON["inputs"]["input_file"]["location"]["path"] = (
    BASE_DIR / "assets" / CONFIG_JSON["inputs"]["input_file"]["location"]["name"]
)


def context_get_input_path_side_effect(value):
    return BASE_DIR / "assets" / CONFIG_JSON["inputs"][value]["location"]["name"]


def context_get_input_filename_side_effect(value):
    return CONFIG_JSON["inputs"][value]["location"]["name"]


def context_get_input_side_effect(value):
    return CONFIG_JSON["inputs"][value]


def test_parse_config():
    context = MagicMock()
    context.get_input_path.side_effect = context_get_input_path_side_effect
    context.get_input_filename.side_effect = context_get_input_filename_side_effect
    context.get_input.side_effect = context_get_input_side_effect
    context.config = CONFIG_JSON["config"]
    context.destination = CONFIG_JSON["destination"]

    file_name = CONFIG_JSON["inputs"]["input_file"]["location"]["name"]
    file_id = CONFIG_JSON["inputs"]["input_file"]["object"]["file_id"]
    file_type = CONFIG_JSON["inputs"]["input_file"]["object"]["type"]
    parents = {}

    file = flywheel.FileEntry(
        name=file_name, file_id=file_id, type=file_type, parents=parents
    )

    client = MagicMock()
    client.get_file = MagicMock(return_value=file)
    context.client = client
    context._client = client
    (debug, tag, schema_file_path, fw_reference, loader_config) = parser.parse_config(
        context
    )

    assert loader_config["add_parents"] is False

    assert fw_reference.id == "6442f29a9bb0718c0adfaf9f"
    assert fw_reference.type == "file"
    assert fw_reference.name == "test_input_valid.json"
    assert fw_reference.file_type == "json"

    assert tag == "file-validator"

    assert debug is False


def test_identify_json_type():
    ext = ".json"
    str_ext = parser.identify_file_type(ext=ext)
    assert str_ext == "json"
    mime = "application/json"
    str_ext = parser.identify_file_type(mime=mime)
    assert str_ext == "json"

    context = MagicMock()
    context.get_input_path.side_effect = context_get_input_path_side_effect
    context.get_input_filename.side_effect = context_get_input_filename_side_effect
    context.get_input.side_effect = context_get_input_side_effect
    context.config = CONFIG_JSON["config"]
    context.destination = CONFIG_JSON["destination"]

    file_fw = context.get_input("input_file")
    fw_ext, mime = parser.get_filetype_data(file_fw)
    assert fw_ext == ".json"

    file_fw["location"]["name"] = "noext"
    fw_ext, mime = parser.get_filetype_data(file_fw)
    assert mime == "application/json"



def test_identify_csv_type():
    ext = ".csv"
    str_ext = parser.identify_file_type(ext=ext)
    assert str_ext == "csv"
    mime = "text/csv"
    str_ext = parser.identify_file_type(mime=mime)
    assert str_ext == "csv"

    context = MagicMock()
    context.get_input_path.side_effect = context_get_input_path_side_effect
    context.get_input_filename.side_effect = context_get_input_filename_side_effect
    context.get_input.side_effect = context_get_input_side_effect
    context.config = CONFIG_JSON["config"]
    context.destination = CONFIG_JSON["destination"]

    file_fw = context.get_input("input_file")
    file_fw["object"]["mimetype"] = "text/csv"
    file_fw["location"]["name"] = "file.csv"
    fw_ext, mime = parser.get_filetype_data(file_fw)
    assert fw_ext == ".csv"
    assert mime == "text/csv"


def test_identify_unsupported_type():
    ext = ".json"
    str_ext = parser.identify_file_type(ext=ext)
    assert str_ext == "json"
    mime = "application/json"
    str_ext = parser.identify_file_type(mime=mime)
    assert str_ext == "json"

    context = MagicMock()
    context.get_input_path.side_effect = context_get_input_path_side_effect
    context.get_input_filename.side_effect = context_get_input_filename_side_effect
    context.get_input.side_effect = context_get_input_side_effect
    context.config = CONFIG_JSON["config"]
    context.destination = CONFIG_JSON["destination"]

    bad_str = "unsupported.ext"
    with pytest.raises(TypeError) as e_info:
        ext, mime = parser.get_filetype_data(bad_str)
        parser.validate_filetype(ext, mime)
