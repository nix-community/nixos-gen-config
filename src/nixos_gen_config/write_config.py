import sys
from pathlib import Path

from nixos_gen_config.classes import NixConfigAttrs
from nixos_gen_config.generate_hw_config import generate_hw_config


def write_hw_config(nix_config: NixConfigAttrs, config_dir: Path) -> None:
    try:
        Path(config_dir).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Creation of {config_dir} failed due to a permission error. run script as root.")
        sys.exit(1)
    except OSError as error:
        print(f"Creation of {config_dir} failed {error}")
        sys.exit(1)

    try:
        with open(f"{config_dir}/hardware-configuration.nix", "w", encoding="utf-8") as t_f:
            t_f.write(generate_hw_config(nix_config))
    except PermissionError:
        print(
            f"Creation of {config_dir}/hardware-configuration.nix failed due to a permission error. run script as root."
        )
        sys.exit(1)
