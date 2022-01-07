# pylint: disable=invalid-name
# ^ pyudev names ID_VENDOR_ID etc
from dataclasses import dataclass
import subprocess
from unittest.mock import MagicMock, patch

import pytest
import pyudev

from nixos_gen_config import hardware
from nixos_gen_config.classes import NixConfigAttrs

@dataclass
class FakeDevice():
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

def test_usb_keyboard() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_INPUT_KEYBOARD = "1"
    pyudev_device.ID_USB_DRIVER = "usbhid"
    hardware.usb_keyboard(nix_config, pyudev_device)
    assert 'usbhid' in nix_config.initrd_available_kernel_modules

def test_bcache() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_FS_TYPE = "bcache"
    hardware.bcache(nix_config, pyudev_device)
    assert 'bcache' in nix_config.initrd_available_kernel_modules


def test_virt_section() -> None:
    nix_config = NixConfigAttrs()
    with patch("subprocess.run") as subprocess_mock:
        subprocess_mock.return_value.stdout = "kvm"
        hardware.virt_section(nix_config)
        assert '(modulesPath + "/profiles/qemu-quest.nix")' in nix_config.imports


def test_virt_section_process_error() -> None:
    nix_config = NixConfigAttrs()
    with patch("subprocess.run") as subprocess_mock:
        subprocess_mock.side_effect = subprocess.CalledProcessError(1, "cmd", "output")
        hardware.virt_section(nix_config)
        assert '(modulesPath + "/installer/scan/not-detected.nix")' in nix_config.imports
