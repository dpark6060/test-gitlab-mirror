import json
import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from flywheel_gear_toolkit.utils.datatypes import Container

from fw_gear_file_validator.utils import FwReference

PARENT_INCLUDE = [
    # General values
    "label",
    "info",
    "uid",
    # Session values
    "age",
    "weight",
    # Subject values
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


class Loader(ABC):
    """Abstract base class for loaders.
    This is used to load the schema and the object to be validated."""

    name = None
    has_config = False

    @classmethod
    def factory(cls, name: str, config: t.Dict[str, t.Any] = None) -> "Loader":
        """Returns a configured loader based on the name and config provided."""
        loader = None
        for subclass in cls.__subclasses__():
            if subclass.name == name:
                if subclass.has_config:
                    loader = subclass(config)
                else:
                    loader = subclass()
                break

        if not loader:
            raise ValueError(f"Loader {name} not found")

        return loader

    @staticmethod
    def load_schema(file_path: Path) -> dict:
        return JsonLoader().load_object(file_path)

    @abstractmethod
    def load_object(self, file: t.Union[Path, dict]) -> dict:
        """Returns the object to be validated as a dict."""
        pass


class JsonLoader(Loader):
    """Loads a JSON file."""

    name = "json"
    has_config = False

    def __init__(self):
        super().__init__()

    def load_object(self, file_path: Path) -> dict:
        """Returns the content of the JSON file as a dict."""
        try:
            with open(file_path, "r", encoding="UTF-8") as fp:
                content = json.load(fp)
            return content
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading JSON object: {e}")


class FwLoader(Loader):
    """Loads a Flywheel object."""

    name = "flywheel"
    has_config = True

    def __init__(self, config: t.Dict[str, t.Any]):
        self.add_parents = config.get("add_parents")

    def load_object(self, fw_ref: FwReference) -> dict:
        """Returns the content of the Flywheel reference as a dict."""
        if self.add_parents:
            containers_d = fw_ref.all
        else:
            container = fw_ref.container
            containers_d = {container.container_type: container}

        for k, container in containers_d.items():
            containers_d[k] = self._filter_container(container)
        return containers_d

    @staticmethod
    def _filter_container(container: Container):
        """Filters the container to remove unwanted fields."""
        cont_f = {k: v for k, v in container.to_dict().items() if k in PARENT_INCLUDE}
        return cont_f
