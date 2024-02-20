import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import flywheel

from fw_gear_file_validator import errors, utils

BASE_DIR = d = Path(__file__).resolve().parents[1]
test_config = BASE_DIR / "tests" / "assets" / "config.json"


def test_save_errors_metadata():
    error_dict = [{"key1": "k1v1", "key2": "k2v1"}, {"key1": "k1v2", "key2": "k2v2"}]
    context = MagicMock()
    file_name = "test_file_name.ext"
    file_id = "test_container_id"
    file_type = "test_file_type"
    parent_dict = {}

    mock_client = MagicMock()

    file = flywheel.FileEntry(
        name=file_name, file_id=file_id, type=file_type, parents=parent_dict
    )
    mock_client.get_file.return_value = file
    fw_ref = utils.FwReference.init_from_file(mock_client, file, "file")

    errors.save_errors_metadata(error_dict, fw_ref, context)
    context.metadata.add_qc_result.assert_called_with(file_name, "validation", state="FAIL", data=error_dict)