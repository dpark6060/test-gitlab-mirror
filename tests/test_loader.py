import json
from pathlib import Path
from unittest.mock import MagicMock

from fw_gear_file_validator.loader import FwLoader
from fw_gear_file_validator.utils import FwReference

BASE_DIR = d = Path(__file__).resolve().parents[1]
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


def test_loader_init():
    context = MagicMock()
    context.get_input_path.side_effect = context_get_input_path_side_effect
    context.get_input_filename.side_effect = context_get_input_filename_side_effect
    context.get_input.side_effect = context_get_input_side_effect
    context.config = CONFIG_JSON["config"]
    context.destination = CONFIG_JSON["destination"]

    client = MagicMock()
    context._client = client

    fw_reference = FwReference.init_from_file(client, context.get_input("input_file"))
    fw_reference.parents = {"acquisition": "1234"}
    fw_reference.__post_init__()
    config = {"add_parents": True}
    loader = FwLoader(config=config)
    validation_dict = loader.load_object(fw_reference.loc)

    client.get_file.assert_called()
    client.get_file().parents.keys.assert_called()
    client.get_acquisition.assert_called()
    assert validation_dict == {"acquisition": {}, "file": {}}

    client2 = MagicMock()
    fw_reference = FwReference.init_from_file(
        client2, context.get_input("input_file")
    )
    fw_reference.parents = {"acquisition": "1234"}
    fw_reference.__post_init__()

    config = {"add_parents": False}
    loader = FwLoader(config=config)
    validation_dict = loader.load_object(fw_reference.loc)

    client2.get_file.assert_called()
    client2.get_acquisition.assert_not_called()
