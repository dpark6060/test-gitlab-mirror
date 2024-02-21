from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flywheel import Acquisition, FileEntry, Group, Project, Session, Subject

from fw_gear_file_validator import utils

PARENT_ORDER = utils.PARENT_ORDER
FwReference = utils.FwReference

BASE_DIR = d = Path(__file__).resolve().parents[1]
BASE_DIR = BASE_DIR / "tests"
test_config = BASE_DIR / "assets" / "config.json"


def test_is_valid():
    with pytest.raises(ValueError):
        ref = FwReference(type="file", parents={})
        ref.file_path = Path("does/not/exist.txt")
        ref.path_is_valid()

    ref = FwReference(type="file", parents={})
    ref.file_path = Path(test_config)
    assert ref.path_is_valid()

    with pytest.raises(ValueError):
        _ = FwReference.init_from_file(None, {"label": "123"})


def test_parents():
    ses_id = "63ceeda12bae5aafaf66306e"

    client = MagicMock()
    parents = {"session": ses_id}
    file_id = "6442edd40e732989de85e54d"
    file_name = "json_classifier.yaml"
    file_type = "json"

    file = FileEntry(name=file_name, file_id=file_id, type=file_type, parents=parents)
    client.get_file.return_value = file
    ref = FwReference.init_from_file(client, file)
    _ = ref.hierarchy_objects
    assert client.get_file.call_count == 2
    client.get_session.assert_called_once()


def test_get_lookup_path():
    group = Group()
    group.label = "test_group"
    project = Project()
    project.label = "test_project"
    subject = Subject()
    subject.label = "test_subject"
    session = Session()
    session.label = "test_session"
    acquisition = Acquisition()
    acquisition.label = "test_acquisition"
    file_name = "test_file_name.ext"
    file_id = "test_container_id"
    file_type = "test_file_type"
    parent_dict = {
        "group": group,
        "project": project,
        "subject": subject,
        "session": session,
        "acquisition": acquisition,
    }

    file = FileEntry(
        name=file_name, file_id=file_id, type=file_type, parents=parent_dict
    )
    object_hierarchy = {
        "group": group,
        "project": project,
        "subject": subject,
        "session": session,
        "acquisition": acquisition,
        "file": file,
    }
    mock_client = MagicMock()
    mock_client.get_file.return_value = file

    fw_ref = FwReference.init_from_file(mock_client, file)
    fw_ref.hierarchy_objects = object_hierarchy
    url = f"fw://{group.label}/{project.label}/{subject.label}/{session.label}/{acquisition.label}/{file.name}"
    assert fw_ref.get_lookup_path() == url

    url = f"fw://{group.label}/{project.label}/{subject.label}/{session.label}/{acquisition.label}"
    assert fw_ref.get_lookup_path(level="acquisition") == url

    url = f"fw://{group.label}/{project.label}/{subject.label}/{session.label}"
    assert fw_ref.get_lookup_path(level="session") == url

    url = f"fw://{group.label}/{project.label}/{subject.label}"
    assert fw_ref.get_lookup_path(level="subject") == url

    url = f"fw://{group.label}/{project.label}"
    assert fw_ref.get_lookup_path(level="project") == url

    url = f"fw://{group.label}"
    assert fw_ref.get_lookup_path(level="group") == url



