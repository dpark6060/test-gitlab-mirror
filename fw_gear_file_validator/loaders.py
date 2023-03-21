import json
import typing as t
from abc import ABC, abstractmethod
from pathlib import Path
import flywheel

from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_file_validator.utils import get_parents_hierarchy


class FwLoader:
    def __init__(
        self,
        context: GearToolkitContext,
        add_parents: bool = True,
    ):
        self.context = context
        self.add_parents = add_parents

        # if not input_file_key:
        #     input_file_key = ""
        # self.input_file_key = input_file_key
        # self.fw_meta_dict = self._get_fw_meta_dict()

    def load(self, reference: dict):
        cont = self.context.get_container_from_ref(reference)
        d = cont.to_dict()
        if self.add_parents:
            parents = get_parents_hierarchy(self.context.client, cont)
            d.update(parents)
        return d

    # def _get_loader(self, reference):
    #     if reference.get("type") == "file":
    #         return self._load_flywheel_file
    #     elif reference.get("type") in ["project", "subject", "session", "acquisition"]:
    #         return self._load_flywheel_container
    #     else:
    #         raise ValueError(f"Unsupported reference type {reference.get('type')}")
    #
    # def _load_flywheel_file(self, ref: dict) -> t.Dict:
    #     self.context.get_container_from_ref(ref)
    #     return {ctype: self.fw_meta_dict[ctype]}
    #
    # def _load_flywheel_container(self, ref: dict) -> t.Dict:
    #     # Otherwise isolate the target object (file if present, or the destination container)
    #
    #     ctype = self.context.destination["type"]
    #     return {ctype: self.fw_meta_dict[ctype]}
