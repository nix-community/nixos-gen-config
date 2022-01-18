import sys
from pathlib import Path

from nixos_gen_config.classes import NixConfigAttrs
from nixos_gen_config.generate_hw_config import generate_hw_config
from nixos_gen_config.generate_nixos_config import generate_nixos_config


def create_config_dir(config_dir: Path) -> None:
    try:
        Path(config_dir).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Creation of {config_dir} failed due to a permission error. run script as root.")
        sys.exit(1)
    except OSError as error:
        print(f"Creation of {config_dir} failed {error}")
        sys.exit(1)


def write_hw_config(nix_hw_config: NixConfigAttrs, config_dir: Path) -> None:
    create_config_dir(config_dir)
    config_file: Path = Path(f"{config_dir}/hardware-configuration.nix")
    print(f"Writing {config_file}")
    try:
        with open(config_file, "w", encoding="utf-8") as t_f:
            t_f.write(generate_hw_config(nix_hw_config))
    except PermissionError:
        print(f"Creation of {config_file} failed due to a permission error. run script as root.")
        sys.exit(1)


def write_nixos_config(nix_nixos_config: NixConfigAttrs, config_dir: Path, overwrite: bool) -> None:
    create_config_dir(config_dir)
    config_file: Path = Path(f"{config_dir}/configuration.nix")
    print(f"Writing {config_file}")
    if config_file.exists() and not overwrite:
        print(f"{config_file} already exists, use --force to overwrite.")
        return
    try:
        with open(config_file, "w", encoding="utf-8") as t_f:
            t_f.write(generate_nixos_config(nix_nixos_config))
    except PermissionError:
        print(f"Creation of {config_file} failed due to a permission error. run script as root.")
        sys.exit(1)
