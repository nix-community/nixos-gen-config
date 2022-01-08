# pylint: disable=invalid-name
# ^ pyudev names ID_VENDOR_ID etc
from dataclasses import dataclass
from pathlib import Path

import pyudev

from nixos_gen_config.classes import NixConfigAttrs
from nixos_gen_config.hardware import pci

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


def test_pci_usb_controller() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_PCI_SUBCLASS_FROM_DATABASE = "USB controller"
    pyudev_device.DRIVER = "xhci_hcd"
    pci(nix_config, pyudev_device)
    assert "xhci_pci" in nix_config.initrd_available_kernel_modules


def test_pci_virtio_scsi() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_MODEL_FROM_DATABASE = "Virtio SCSI"
    pci(nix_config, pyudev_device)
    assert "virtio_scsi" in nix_config.initrd_available_kernel_modules
