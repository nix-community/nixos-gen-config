import os
from pathlib import Path
import sys

from icecream import ic

from nixos_gen_config import auxiliary_functions as af
from nixos_gen_config.arguments import process_args
from nixos_gen_config.classes import NixConfigAttrs
from nixos_gen_config.generate_hw_config import generate_hw_config
from nixos_gen_config.hardware import cpu_section, udev_section, virt_section
from nixos_gen_config.partitions import get_fs


def main() -> None:
    nix_config = NixConfigAttrs()

    args = process_args()
    if not args.debug:
        ic.disable()

    # out_dir = os.path.abspath(args.dir)
    out_dir = os.path.abspath(args.dir)
    if args.root:
        root_dir = os.path.normpath(args.root)
    else:
        root_dir = ""
    force = args.force
    no_filesystems = args.no_filesystems
    show_hardware_config = args.show_hardware_config

    config_dir = af.get_config_dir(out_dir, root_dir)

    udev_section(nix_config)
    virt_section(nix_config)
    cpu_section(nix_config)

    def write_hw_config(nix_config: NixConfigAttrs) -> None:
        try:
            Path(config_dir).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"Creation of {config_dir} failed due to a permission error. run script as root.")
            sys.exit(1)
        except OSError as error:
            print(f"Creation of {out_dir} failed {error}")

        try:
            with open(f"{config_dir}/hardware-configuration.nix", "w", encoding="utf-8") as t_f:
                t_f.write(generate_hw_config(nix_config))
        except PermissionError:
            print(
                f"Creation of {config_dir}/hardware-configuration.nix failed due to a permission error. run script as root."
            )
            sys.exit(1)

    get_fs(nix_config, root_dir)

    if show_hardware_config:
        print(generate_hw_config(nix_config))
    else:
        write_hw_config(nix_config)


if __name__ == "__main__":
    main()
