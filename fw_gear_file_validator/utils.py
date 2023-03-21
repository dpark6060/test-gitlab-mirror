import csv
import typing as t
from pathlib import Path

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils.datatypes import Container

PARENT_INCLUDE = [
    # General values
    "label",
    "info",
    "uid",
    # Session values
    "label",
    "age",
    "weight",
    # Subject values
    "label",
    "sex",
    "cohort",
    "mlset",
    "ethnicity",
    "species",
    "strain",
    "code",
    "firstname",
    "lastname",
]

PARENT_ORDER = [
    "group",
    "project",
    "subject",
    "session",
    "acquisition",
    "analysis",
    "file",
]


def add_flywheel_location_to_errors(hierarchy_object, validation_level, errors):
    """Takes a set of packaged errors and adds flywheel hierarchy information to them.

    If validation was run at the "flywheel" level, then validation was done on a json schema.
    When this creates flywheel URLs for that, it relies heavily on the predictable structure
    of that schema.
    """

    # If validation level is flywheel, then the input_file_object should have every parent object
    parents = {}
    for parent_level in hierarchy_object.keys():
        if parent_level == "file":
            parents[parent_level] = hierarchy_object[parent_level].get("name", None)
            continue
        parents[parent_level] = hierarchy_object[parent_level].get("label", None)

    ordered_parents = [parents[order] for order in PARENT_ORDER if order in parents]
    # if the validation level was the file, we just need to add the same flywheel path to every error
    if validation_level == "file":
        fw_url = "fw://" + "/".join(ordered_parents)
        for e in errors:
            e["Flywheel_Path"] = fw_url
            e["Container_ID"] = hierarchy_object["file"]["file_id"]

    # If the validation level was on Flywheel, that means it was a json schema and we can use the first level of
    # Error_Location to get the level.  This is a bit complicated but so is adding flywheel specific error stuff
    # to general schema error handling.

    elif validation_level == "flywheel":
        for e in errors:
            location = e["Error_Location"].split(".")[0]
            if location not in PARENT_ORDER:
                raise ValueError(
                    f"Value {location} not valid flywheel hierarchy location"
                )

            ordered_parents = [
                parents[order]
                for order in PARENT_ORDER[: PARENT_ORDER.index(location) + 1]
                if order in parents
            ]
            fw_url = "fw://" + "/".join(ordered_parents)
            e["Flywheel_Path"] = fw_url
            if location == "file":
                id_location = "file_id"
            else:
                id_location = "id"

            e["Container_ID"] = hierarchy_object[location][id_location]

    return errors


def save_errors(errors: t.List[t.Dict], output_dir: t.Union[Path, str]):
    """Saves the packaged errors to a csv file"""
    if not errors:
        return

    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    error_file = output_dir / "file_validator_errors.csv"

    headers = errors[0].keys()

    with open(error_file, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(errors)


def create_metadata(context: GearToolkitContext, valid: bool, input_object: Container):
    """Populate .metadata.json.

    Args:
        context (GearToolkitContext): The gear context.
        valid: Did the file pass validation?
        input_object: The flywheel container or gear context input file to modify metadata for
    """
    state = "PASS" if valid else "FAIL"

    # Add qc information
    # context.metadata.add_qc_result(file_input, "validation", state=state)

    if input_object["container_type"] == "file":
        updator = context.metadata.update_file
    else:
        updator = context.metadata.update_container
    updator(
        input_object, info={"qc": {"file-validator": {"validation": {"state": state}}}}
    )


def get_parents_hierarchy(client: flywheel.Client, container: Container) -> dict:
    """Returns Creates a file that is the json representation of the flywheel hierarchy containing the file and its parents"""
    parents_hierarchy = {}
    parents = container.parents
    for parent, p_id in parents.items():
        if p_id is None or parent == "group":
            continue
        getter = getattr(client, f"get_{parent}")
        parent_object = getter(p_id)
        parents_hierarchy[parent] = {
            k: v for k, v in parent_object.to_dict().items() if k in PARENT_INCLUDE
        }

    return parents_hierarchy


def handle_metadata(context, strategy, valid, tag):
    if strategy == "flywheel-container":
        input_object = context.client.get(context.destination["id"])
    else:
        input_object = context.get_input_file_object("input_file")
        context.metadata.add_file_tags(input_object, str(tag))

    create_metadata(context, valid, input_object)
