import subprocess
import pytest
import pyudev
from unittest.mock import MagicMock, patch

from nixos_gen_config import hardware
from nixos_gen_config.classes import NixConfigAttrs


def test_bcache() -> None:
    class Device(object):
        #product = None
        #device_node = None
        #action = None
        #ID_VENDOR_ID = None
        #ID_MODEL_ID = None
        ID_FS_TYPE: str

        def get(self, attribute: str) -> pyudev.Device:
            return getattr(self, attribute)

    pyudev_device = Device()
    pyudev_device.ID_FS_TYPE = "bcache"
    nix_config = NixConfigAttrs()

    hardware.bcache(nix_config, pyudev_device)

    assert 'bcache' in nix_config.initrd_available_kernel_modules


def test_virt_section() -> None:
    nix_config = NixConfigAttrs()
    with patch("subprocess.run") as subprocess_mock:
        subprocess_mock.return_value.stdout = "kvm"
        hardware.virt_section(nix_config)
        assert '(modulesPath + "/profiles/qemu-quest.nix")' in nix_config.imports


def test_virt_section_processor_error() -> None:
    nix_config = NixConfigAttrs()
    with patch("subprocess.run") as subprocess_mock:
        subprocess_mock.side_effect = subprocess.CalledProcessError(1, "cmd", "output")
        hardware.virt_section(nix_config)
        assert '(modulesPath + "/installer/scan/not-detected.nix")' in nix_config.imports
