from pathlib import Path
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


def test_config_dir_different_out() -> None:
    out_dir = Path("a_out_dir")
    root_dir = Path("/notmnt")
    returned = af.get_config_dir(out_dir, root_dir)
    assert returned == Path("a_out_dir")


def test_config_dir_mnt_root_default_out() -> None:
    out_dir = Path("/etc/nixos")
    root_dir = Path("/mnt")
    returned = af.get_config_dir(out_dir, root_dir)
    assert returned == Path("/mnt/etc/nixos")


def test_config_dir_no_root_default_out() -> None:
    out_dir = Path("/etc/nixos")
    root_dir = Path("/")
    returned = af.get_config_dir(out_dir, root_dir)
    assert returned == Path("/etc/nixos")


def test_config_dir_no_root_different_out() -> None:
    out_dir = Path("/etc/notnixos")
    root_dir = Path("/")
    returned = af.get_config_dir(out_dir, root_dir)
    assert returned == Path("/etc/notnixos")
