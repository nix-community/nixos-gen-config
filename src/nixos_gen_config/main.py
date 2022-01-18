from pathlib import Path

from icecream import ic

from nixos_gen_config import auxiliary_functions as af
from nixos_gen_config.arguments import process_args
from nixos_gen_config.classes import NixConfigAttrs
from nixos_gen_config.generate_hw_config import generate_hw_config
from nixos_gen_config.hardware import cpu_section, udev_section, virt_section
from nixos_gen_config.partitions import get_fs
from nixos_gen_config.write_config import write_hw_config, write_nixos_config


def main() -> None:
    nix_hw_config = NixConfigAttrs()
    nix_nixos_config = NixConfigAttrs()

    args = process_args()
    if not args.debug:
        ic.disable()
    out_dir: Path = Path(args.dir).resolve()
    root_dir: Path = Path(args.root).resolve()
    overwrite_configuration: bool = args.force
    no_filesystems: bool = args.no_filesystems
    show_hardware_config: bool = args.show_hardware_config

    config_dir = af.get_config_dir(out_dir, root_dir)

    udev_section(nix_hw_config)
    virt_section(nix_hw_config)
    cpu_section(nix_hw_config)

    if not no_filesystems:
        get_fs(nix_hw_config, root_dir)

    if show_hardware_config:
        print(generate_hw_config(nix_hw_config))
    else:
        write_hw_config(nix_hw_config, config_dir)
        write_nixos_config(nix_nixos_config, config_dir, overwrite_configuration)


if __name__ == "__main__":
    main()
