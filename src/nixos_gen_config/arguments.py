from pathlib import Path
import argparse


def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        help=(
            "If this option is given, treat the directory root as the root of the file system. This means that "
            "configuration files will be written to root/etc/nixos, and that any file systems outside of root are "
            "ignored for the purpose of generating the fileSystems option."
        ),
    )
    parser.add_argument(
        "--dir",
        type=Path,
        # NOTE: uncomment
        default="/etc/nixos1",
        # default="config1",
        help="write the configuration files to the directory specified instead of /etc/nixos",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite /etc/nixos/configuration.nix if it already exists",
    )
    parser.add_argument(
        # NOTE: remember to change default to 0
        "--debug",
        action="store_true",
        default=1,
        help="icecream debug",
    )
    parser.add_argument(
        "--no-filesystems",
        action="store_true",
        help="Omit everything concerning file systems and swap devices from the hardware configuration",
    )
    parser.add_argument(
        "--show-hardware-config",
        action="store_true",
        help=(
            "Don't generate configuration.nix or hardware-configuration.nix and print the hardware configuration to"
            "stdout only."
        ),
    )
    return parser.parse_args()
