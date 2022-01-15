from dataclasses import dataclass, field

from nixos_gen_config.auxiliary_functions import (to_nix_list,
                                                  to_nix_string_list, uniq)


@dataclass
class NixConfigAttrs:
    attrs: list[str] = field(default_factory=list)
    fsattrs: list[str] = field(default_factory=list)
    initrd_available_kernel_modules: list[str] = field(default_factory=list)
    initrd_kernel_modules: list[str] = field(default_factory=list)
    kernel_modules: list[str] = field(default_factory=list)
    module_packages: list[str] = field(default_factory=list)
    firmware_packages: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def get_string(self, query: str) -> str:
        """get a deduplicated string of values in a class list.
        if list is empty then returns a empty string"""
        val = getattr(self, query)
        return_str: str = ""
        if query in ["initrd_available_kernel_modules", "initrd_kernel_modules", "kernel_modules"]:
            return_str = to_nix_string_list(*(uniq(val)))
        elif query in ["module_packages", "firmware_packages"]:
            return_str = to_nix_list(*(uniq(val)))
        return return_str
