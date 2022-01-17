# pylint: disable=invalid-name
# ^ pyudev names ID_VENDOR_ID etc
from nixos_gen_config.classes import NixConfigAttrs
from nixos_gen_config.hardware import pci

from .conftest import FakeDevice


def test_pci_usb_controller() -> None:
    nix_hw_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_PCI_SUBCLASS_FROM_DATABASE = "USB controller"
    pyudev_device.DRIVER = "xhci_hcd"
    pci(nix_hw_config, pyudev_device)
    assert "xhci_pci" in nix_hw_config.initrd_available_kernel_modules


def test_pci_virtio_scsi() -> None:
    nix_hw_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_MODEL_FROM_DATABASE = "Virtio SCSI"
    pci(nix_hw_config, pyudev_device)
    assert "virtio_scsi" in nix_hw_config.initrd_available_kernel_modules
