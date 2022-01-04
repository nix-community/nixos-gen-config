from nixos_gen_config import auxiliary_functions as auxiliary_functions
from nixos_gen_config.classes import NixConfigAttrs as NixConfigAttrs
from typing import Any

uniq = auxiliary_functions.uniq
to_nix_string_list = auxiliary_functions.to_nix_string_list
to_nix_list = auxiliary_functions.to_nix_list
to_nix_multi_line_list = auxiliary_functions.to_nix_multi_line_list
to_nix_true_attr = auxiliary_functions.to_nix_true_attr
to_nix_false_attr = auxiliary_functions.to_nix_false_attr
hwConfigTemplate: Any

def generate_hw_config(nix_config: NixConfigAttrs) -> str: ...
