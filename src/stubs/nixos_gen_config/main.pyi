from nixos_gen_config.arguments import process_args as process_args
from nixos_gen_config.classes import NixConfigAttrs as NixConfigAttrs
from nixos_gen_config.generate_hw_config import generate_hw_config as generate_hw_config
from nixos_gen_config.hardware import cpu_section as cpu_section, udev_section as udev_section, virt_section as virt_section
from nixos_gen_config.partitions import get_fs as get_fs

def main() -> None: ...
