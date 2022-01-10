from pathlib import Path

import pytest

import nixos_gen_config.auxiliary_functions as af


def test_uniq() -> None:
    text: list[str] = ["dupe", "test", "anotherdupe", "notdupe", "dupe", "anotherdupe"]
    returned: list[str] = af.uniq(text)
    assert returned == ["dupe", "test", "anotherdupe", "notdupe"]


def test_to_nix_string_list() -> None:
    text: list[str] = ["amd", "intel", "kernel_module"]
    returned: str = af.to_nix_string_list(*text)
    assert returned == ' "amd" "intel" "kernel_module"'


def test_to_nix_list() -> None:
    text: list[str] = ["pkgs.package", "pkgs.hello", "pkgs.linuxPackages.kernel"]
    returned: str = af.to_nix_list(*text)
    assert returned == " pkgs.package pkgs.hello pkgs.linuxPackages.kernel"


def test_to_nix_multi_line_list() -> None:
    text: list[str] = [
        '(modulesPath + "/installer/scan/not-detected.nix")',
        '(modulesPath + "/profiles/qemu-quest.nix")',
    ]
    returned: str = af.to_nix_multi_line_list("    ", *text)
    assert (
        returned
        == """
    [ (modulesPath + "/installer/scan/not-detected.nix")
      (modulesPath + "/profiles/qemu-quest.nix")
    ]"""
    )


def test_to_nix_multi_line_list_empty() -> None:
    text: list[str] = []
    returned: str = af.to_nix_multi_line_list("    ", *text)
    assert returned == " [ ]"


def test_to_nix_true_attr() -> None:
    text: str = "boot.isContainer"
    returned = af.to_nix_true_attr(text)
    assert returned == "boot.isContainer = true;"


def test_to_nix_false_attr() -> None:
    text: str = "boot.isContainer"
    returned = af.to_nix_false_attr(text)
    assert returned == "boot.isContainer = false;"


conf_dir_testdata = [
    (Path("a_out_dir"), Path("/notmnt"), Path("a_out_dir")),
    (Path("/etc/nixos"), Path("/mnt"), Path("/mnt/etc/nixos")),
    (Path("/etc/nixos"), Path("/"), Path("/etc/nixos")),
    (Path("/etc/notnixos"), Path("/"), Path("/etc/notnixos")),
]


@pytest.mark.parametrize("out_dir, root_dir, expected", conf_dir_testdata)
def test_get_config_dir(out_dir: Path, root_dir: Path, expected: Path) -> None:
    returned = af.get_config_dir(out_dir, root_dir)
    assert returned == expected
