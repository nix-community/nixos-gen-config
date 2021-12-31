import os
from pathlib import Path
from dataclasses import dataclass, field
import subprocess

from icecream import ic  # type: ignore
import pyudev  # type: ignore

from nixos_gen_config import auxiliary_functions  # type: ignore
from nixos_gen_config.arguments import process_args  # type: ignore
from nixos_gen_config.hardware import cpu_section, udevGet # type: ignore
from nixos_gen_config.classes import nixConfigAttrs
from nixos_gen_config.generate_hw_config import generate_hw_config


def main():
    nixConfig = nixConfigAttrs()
    uniq = auxiliary_functions.uniq
    to_nix_string_list = auxiliary_functions.to_nix_string_list
    to_nix_list = auxiliary_functions.to_nix_list
    to_nix_multi_line_list = auxiliary_functions.to_nix_multi_line_list
    to_nix_true_attr = auxiliary_functions.to_nix_true_attr
    to_nix_false_attr = auxiliary_functions.to_nix_false_attr

    args = process_args()

    out_dir = os.path.abspath(args.dir)
    if args.root:
        root_dir = os.path.normpath(args.root)
    else:
        root_dir = ""
    force = args.force
    no_filesystems = args.no_filesystems
    show_hardware_config = args.show_hardware_config

    if not args.debug:
        ic.disable()

    try:
        os.mkdir(out_dir)
    except FileExistsError:
        pass
    except OSError as error:
        print(f"Creation of {out_dir} failed {error}")


    def virt_section(nix_config: nixConfigAttrs) -> None:
        virtcmd = ""
        # systemd-detect-virt exits with 1 when virt = none
        try:
            virtcmd = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            # Provide firmware for devices that are not detected by this script,
            # unless we're in a VM/container.
            nix_config.imports.append('(modulesPath + "/installer/scan/not-detected.nix")')


        if virtcmd:
            virt = (virtcmd.stdout).strip()
            if virt == "oracle":
                nix_config.attrs.append(to_nix_true_attr("virtualisation.virtualbox.guest.enable"))
            if virt == "microsoft":
                nix_config.attrs.append(to_nix_true_attr("virtualisation.hypervGuest.enable"))
            if virt == "systemd-nspawn":
                nix_config.attrs.append(to_nix_true_attr("boot.isContainer"))
            if virt in ("qemu", "kvm", "bochs"):
                nix_config.imports.append('(modulesPath + "/profiles/qemu-quest.nix")')


    udevGet(nixConfig)

    video_driver = 0
    if video_driver:
        nixConfig.attrs.append(f'services.xserver.videoDrivers = [ "{video_driver}" ]')


    virt_section(nixConfig)

    cpu_section(nixConfig)

    #gen_hw_file(nixConfig)

    def write_hw_config(nix_config: nixConfigAttrs) -> None:
        #print(generate_hw_config(nixConfig))
        with open(f"{root_dir}{out_dir}/hardware-configuration.nix", "w", encoding='utf-8') as t_f:
            t_f.write(generate_hw_config(nix_config))



    write_hw_config(nixConfig)



if __name__ == "__main__":
    main()
