from nixos_gen_config.classes import NixConfigAttrs as NixConfigAttrs
from typing import Any

fsTemplate: Any
special_fs: Any

def get_fs(nix_config: NixConfigAttrs, root_dir: str) -> None: ...
