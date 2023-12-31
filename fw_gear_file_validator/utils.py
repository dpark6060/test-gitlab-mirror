import logging
import time
import typing as t
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import flywheel
import flywheel_gear_toolkit
from flywheel_gear_toolkit.utils.datatypes import Container

PARENT_ORDER = [
    "group",
    "project",
    "subject",
    "session",
    "acquisition",
    "analysis",
    "file",
]

log = logging.getLogger()

N_TRIES = 5
SLEEP_TIME = 5


@dataclass
class FwReference:
    """A reference to a flywheel object (being a container or a gear input file).

    Host a set of methods to facilitate the loading of the object in its specific
    context (gear input file, flywheel container or flywheel file).

    """

    cont_id: str = None
    cont_type: str = None
    file_name: str = None
    file_path: Path = None
    file_type: str = None
    _client: flywheel.Client = None

    def __post_init__(self):
        self.is_valid()

    def loc(self) -> t.Union[Path, "FwReference"]:
        """Returns location of the object."""
        if self.file_path:
            return self.file_path
        else:
            return self

    def is_valid(self) -> bool:
        """Returns True if the reference is valid, raise exception otherwise."""
        if self.file_path and not self.file_path.exists():
            raise ValueError(f"File {self.file_path} does not exist")
        if self.cont_type and self.cont_type not in PARENT_ORDER:
            raise ValueError(f"Invalid type {self.cont_type}")
        return True

    def validate_file_contents(self) -> bool:
        """Returns True if the object is a local file, False otherwise."""
        if self.file_path:
            return True
        return False

    def is_file(self) -> bool:
        """Returns True if the object is a file, False otherwise."""
        if self.file_name:
            return True
        return False

    @property
    def client(self) -> flywheel.Client:
        """Returns the Flywheel client."""
        if not self._client:
            raise ValueError("Client not set. Use set_client() to set the client.")
        return self._client

    def set_client(self, client: flywheel.Client):
        """Sets the Flywheel client as attribute."""
        self._client = client

    def get_lookup_path(self, level: str = None) -> str:
        """Returns the Flywheel path of the Flywheel object."""
        container = self.container
        parents = self.parents
        parents[container.container_type] = container.to_dict()
        hierarchy_parts = []
        for k in PARENT_ORDER:
            if k in parents:
                if k == "file":
                    hierarchy_parts.append(parents[k].get("name"))
                else:
                    hierarchy_parts.append(parents[k].get("label"))
            if k == level:
                break
        return "fw://" + "/".join(hierarchy_parts)

    @cached_property
    def container(self) -> Container:
        """Returns the container for the provided Flywheel reference."""
        getter = getattr(self.client, f"get_{self.cont_type}")

        tries = 0
        while tries < N_TRIES:
            container = getter(self.cont_id)
            if container:
                break
            tries += 1
            log.debug("Empty parent object, retrying")
            time.sleep(SLEEP_TIME)

        if not container:
            # Better to exit here with a good error than crash later
            raise ValueError(
                f"Unable to retrieve container {self.cont_type}: {self.cont_id}"
            )

        if self.file_name:
            container = container.get_file(self.file_name)
        return container

    @cached_property
    def parents(self) -> dict:
        """Returns all the parent containers."""
        parents_hierarchy = {}
        container = self.container
        parents = container.parents
        for p_type, p_id in parents.items():
            if p_id:  # some parents are None
                getter = getattr(self.client, f"get_{p_type}")
                tries = 0
                while tries < N_TRIES:
                    parent_object = getter(p_id)
                    if parent_object:
                        break
                    tries += 1
                    log.debug("Empty parent object, retrying")
                    time.sleep(SLEEP_TIME)

                if not parent_object:
                    # Better to exit here with a good error than crash later
                    raise ValueError(f"Unable to retrieve parent {p_type}: {p_id}")

                parents_hierarchy[p_type] = parent_object
        return parents_hierarchy

    @cached_property
    def children(self):
        """Returns all the child containers."""
        # TODO: Add support for child containers
        raise NotImplementedError

    @cached_property
    def all(self) -> dict:
        """Returns the container and its parents."""

        return {**self.parents, self.container.container_type: self.container}


def handle_metadata(
    context: flywheel_gear_toolkit.GearToolkitContext,
    fw_ref: FwReference,
    valid,
    tag,
):
    state = "PASS" if valid else "FAIL"

    if fw_ref.is_file():
        input_filename = context.get_input_filename("input_file")
        file_ = flywheel_gear_toolkit.utils.metadata.get_file(
            input_filename, context, None
        )
        fail_tag = f"{tag}-FAIL"
        pass_tag = f"{tag}-PASS"
        tag = f"{tag}-{state}"
        input_object = context.get_input("input_file")
        tags = file_.tags
        if state == "PASS" and fail_tag in tags:
            tags.remove(fail_tag)
            context.metadata.update_file(input_filename, tags=tags)
        elif state == "FAIL" and pass_tag in tags:
            tags.remove(pass_tag)
            context.metadata.update_file(input_filename, tags=tags)

        context.metadata.add_qc_result(
            input_object, name=context.manifest["name"], state=state
        )
        context.metadata.add_file_tags(input_object, str(tag))
    else:
        # we do not have an add_qc_result for container other than file so we
        # need to build it the info manually
        # TODO: replace when context.add_qc_result supports all container
        context.metadata.pull_job_info()
        job_info = context.metadata.job_info
        job_info[context.manifest["name"]]["state"] = state
        container = fw_ref.container
        qc = container.info.get("qc", {})
        qc.update(job_info)
        context.metadata.update_container(fw_ref.cont_type, info=qc)
