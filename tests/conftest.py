# pylint: disable=invalid-name
# ^ pyudev names ID_VENDOR_ID etc
from dataclasses import dataclass
from pathlib import Path
from typing import Type

import pytest
import pyudev

TEST_ROOT = Path(__file__).parent.resolve()


@dataclass
class FakeDevice:
    ID_VENDOR_ID: str = ""
    ID_MODEL_ID: str = ""
    ID_MODEL_FROM_DATABASE: str = ""
    ID_FS_TYPE: str = ""
    ID_PCI_CLASS_FROM_DATABASE: str = ""
    ID_PCI_SUBCLASS_FROM_DATABASE: str = ""
    DRIVER: str = ""
    ID_INPUT_KEYBOARD: str = ""
    ID_USB_DRIVER: str = ""

    def get(self, attribute: str) -> pyudev.Attributes:
        return getattr(self, attribute)


class Helpers:
    @staticmethod
    def root() -> Path:
        return TEST_ROOT

    @staticmethod
    def read_asset(asset: str) -> str:
        return str(Path(TEST_ROOT.joinpath("assets", asset)).read_text("utf-8"))


@pytest.fixture
def helpers() -> Type[Helpers]:
    return Helpers
