# pylint: disable=invalid-name
# ^ pyudev names ID_VENDOR_ID etc
from dataclasses import dataclass
from pathlib import Path
import subprocess
from unittest.mock import patch

import pyudev

from nixos_gen_config import hardware
from nixos_gen_config.classes import NixConfigAttrs

from .conftest import FakeDevice
from .conftest import Helpers


def test_cpu_section_amd() -> None:
    nix_config = NixConfigAttrs()
    cpuinfo = Helpers.read_asset("cpu_info_amd")
    governors = Helpers.read_asset("available_governors")

    def fake_read(path: str, encoding: str) -> str:
        if str(path) == "/proc/cpuinfo":
            return cpuinfo
        if str(path) == "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors":
            return governors
        return "shouldn't be reached"

    with patch.object(Path, "read_text", new=fake_read):
        with patch.object(Path, "exists", return_value=True):
            hardware.cpu_section(nix_config)

    assert (
        "hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
        in nix_config.attrs
    )
    assert 'powerManagement.cpuFreqGovernor = lib.mkDefault "powersave";' in nix_config.attrs
    assert "kvm-amd" in nix_config.kernel_modules


def test_cpu_section_intel() -> None:
    nix_config = NixConfigAttrs()
    cpuinfo = Helpers.read_asset("cpu_info_intel")
    governors = Helpers.read_asset("available_governors")

    def fake_read(path: str, encoding: str) -> str:
        if str(path) == "/proc/cpuinfo":
            return cpuinfo
        if str(path) == "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors":
            return governors
        return "shouldn't be reached"

    with patch.object(Path, "read_text", new=fake_read):
        with patch.object(Path, "exists", return_value=True):
            hardware.cpu_section(nix_config)

    assert (
        "hardware.cpu.intel.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
        in nix_config.attrs
    )
    assert 'powerManagement.cpuFreqGovernor = lib.mkDefault "powersave";' in nix_config.attrs
    assert "kvm-intel" in nix_config.kernel_modules


def test_usb_keyboard() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_INPUT_KEYBOARD = "1"
    pyudev_device.ID_USB_DRIVER = "usbhid"
    hardware.usb_keyboard(nix_config, pyudev_device)
    assert "usbhid" in nix_config.initrd_available_kernel_modules


def test_bcache() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_FS_TYPE = "bcache"
    hardware.bcache(nix_config, pyudev_device)
    assert "bcache" in nix_config.initrd_available_kernel_modules


def test_bcache_false() -> None:
    nix_config = NixConfigAttrs()
    pyudev_device = FakeDevice()
    pyudev_device.ID_FS_TYPE = "ext4"
    hardware.bcache(nix_config, pyudev_device)
    assert "bcache" not in nix_config.initrd_available_kernel_modules


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
