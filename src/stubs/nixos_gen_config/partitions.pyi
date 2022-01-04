from nixos_gen_config.classes import NixConfigAttrs as NixConfigAttrs
from string import Template

fsTemplate: Template
special_fs: list[str]

def get_fs(nix_config: NixConfigAttrs, root_dir: str) -> None: ...
