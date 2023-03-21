import os

import flywheel
import flywheel_gear_toolkit

from fw_gear_file_validator import loaders

client = flywheel.Client(os.environ["FWGA_API"])
context = flywheel_gear_toolkit.GearToolkitContext(
    config_path="/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/file-validator/file-validator/tests/assets/config.json"
)
context._client = client


def test_loader_init():
    strategy = "local-file"
    add_parents = False
    input_file_key = "input_file"
    loader = loaders.FwLoader(
        context=context,
        strategy=strategy,
        add_parents=add_parents,
        input_file_key=input_file_key,
    )

    assert loader.strategy == "local-file"
    assert "file" in loader.fw_meta_dict
