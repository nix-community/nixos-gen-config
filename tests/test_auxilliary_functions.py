import nixos_gen_config.auxiliary_functions as af


def test_uniq():
    text: list[str] = ["dupe", "test", "anotherdupe", "notdupe", "dupe", "anotherdupe"]
    returned: list[str] = af.uniq(text)
    assert returned == ["dupe", "test", "anotherdupe", "notdupe"]


def test_to_nix_string_list():
    text: list[str] = ["amd", "intel", "kernel_module"]
    returned: str = af.to_nix_string_list(*text)
    assert returned == ' "amd" "intel" "kernel_module"'


def test_to_nix_list():
    text: list[str] = ["pkgs.package", "pkgs.hello", "pkgs.linuxPackages.kernel"]
    returned: str = af.to_nix_list(*text)
    assert returned == " pkgs.package pkgs.hello pkgs.linuxPackages.kernel"


def test_to_nix_multi_line_list():
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


def test_to_nix_multi_line_list_empty():
    text: list[str] = []
    returned: str = af.to_nix_multi_line_list("    ", *text)
    assert returned == " [ ]"


def test_to_nix_true_attr():
    text: str = "boot.isContainer"
    returned = af.to_nix_true_attr(text)
    assert returned == "boot.isContainer = true;"


def test_to_nix_false_attr():
    text: str = "boot.isContainer"
    returned = af.to_nix_false_attr(text)
    assert returned == "boot.isContainer = false;"


def test_config_dir_different_out():
    out_dir: str = "/etc/notnixos"
    root_dir: str = "/notmnt"
    returned = af.get_config_dir(out_dir, root_dir)
    assert returned == "/notmnt/etc/notnixos"


def test_config_dir_default():
    out_dir: str = "/etc/nixos"
    root_dir: str = "/mnt"
    returned = af.get_config_dir(out_dir, root_dir)
    print(returned)
    assert returned == "/mnt/etc/nixos"
