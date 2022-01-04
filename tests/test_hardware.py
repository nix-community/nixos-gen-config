import subprocess
from unittest.mock import MagicMock, patch

from nixos_gen_config import hardware
from nixos_gen_config.classes import NixConfigAttrs


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
