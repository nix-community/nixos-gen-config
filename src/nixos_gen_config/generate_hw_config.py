from string import Template

from nixos_gen_config import auxiliary_functions
from nixos_gen_config.classes import NixConfigAttrs

uniq = auxiliary_functions.uniq
to_nix_string_list = auxiliary_functions.to_nix_string_list
to_nix_list = auxiliary_functions.to_nix_list
to_nix_multi_line_list = auxiliary_functions.to_nix_multi_line_list
to_nix_true_attr = auxiliary_functions.to_nix_true_attr
to_nix_false_attr = auxiliary_functions.to_nix_false_attr

hwConfigTemplate: Template = Template(
    """\
# Do not modify this file!  It was generated by ‘nixos-generate-config’
# and may be overwritten by future invocations.  Please make changes
# to /etc/nixos/configuration.nix instead.
{ config, lib, pkgs, modulesPath, ... }:
{
  imports =${imports};

  boot.initrd.availableKernelModules = [${i_a_k_m} ];
  boot.initrd.kernelModules = [${i_k_m} ];
  boot.kernelModules = [${k_m} ];
  boot.extraModulePackages = [${m_p} ];
  hardware.firmware = [${f_p} ];
\
"""
)


def generate_hw_config(nix_config: NixConfigAttrs) -> str:
    hw_config_replaced = hwConfigTemplate.substitute(
        imports=to_nix_multi_line_list("    ", *nix_config.imports),
        i_a_k_m=to_nix_string_list(*(uniq(nix_config.initrd_available_kernel_modules))),
        i_k_m=to_nix_string_list(*(uniq(nix_config.initrd_kernel_modules))),
        k_m=to_nix_string_list(*(uniq(nix_config.kernel_modules))),
        m_p=to_nix_list(*(uniq(nix_config.module_packages))),
        f_p=to_nix_list(*(uniq(nix_config.firmware_packages))),
    )
    for attr in uniq(nix_config.attrs):
        hw_config_replaced = hw_config_replaced + "  " + attr + "\n"

    for fsattr in uniq(nix_config.fsattrs):
        hw_config_replaced = hw_config_replaced + fsattr
    hw_config_replaced = hw_config_replaced.rstrip()

    return hw_config_replaced
