from nixos_gen_config.classes import NixConfigAttrs


def test_nixconfigattrs_get_str_list() -> None:
    nix_hw_config = NixConfigAttrs()
    nix_hw_config.initrd_kernel_modules.append("something")
    nix_hw_config.initrd_kernel_modules.append("another")
    assert nix_hw_config.get_string("initrd_kernel_modules") == ' "something" "another"'


def test_nixconfigattrs_get_str() -> None:
    nix_hw_config = NixConfigAttrs()
    nix_hw_config.module_packages.append("something")
    nix_hw_config.module_packages.append("another")
    assert nix_hw_config.get_string("module_packages") == " something another"


def test_nixconfigattrs_get_str_empty() -> None:
    nix_hw_config = NixConfigAttrs()
    assert nix_hw_config.get_string("attrs") == ""
