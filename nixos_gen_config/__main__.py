import argparse
import os
from pathlib import Path
import subprocess
import sys

import pyudev # type: ignore
from icecream import ic # type: ignore

def main():

    def uniq(list1):
        uniq_list = []
        for x in list1:
            if x not in uniq_list:
                uniq_list.append(x)
        return uniq_list


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
            # default="/etc/nixos",
            default="config1",
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
                "stdout only."),
        )
        return parser.parse_args()


    args = process_args()

    outDir = os.path.abspath(args.dir)
    if args.root:
        rootDir = os.path.normpath(args.root)
    else:
        rootDir = ""
    force = args.force
    noFilesystems = args.no_filesystems
    showHardwareConfig = args.show_hardware_config

    if not args.debug:
        ic.disable()


    try:
        os.mkdir(outDir)
    except FileExistsError:
        pass
    except OSError as error:
        print(f"Creation of {outDir} failed {error}")


    attrs = []
    initrdAvailableKernelModules = []
    initrdKernelModules = []
    kernelModules = []
    modulePackages = []
    firmwarePackages = []
    imports = []


    # cpuInfo("flags")
    # print(cpuInfo("flags"))


    def cpuSection():
        cpudata = {}

        def cpuInfo(field):
            cpuinfo = Path("/proc/cpuinfo").read_text()
            for line in cpuinfo.split("\n"):
                # cpuinfo has a empty line at the end
                if line == "":
                    continue
                left, right = line.split(":")
                cpudata[left.strip()] = right.strip()
            return cpudata[field]

        if cpuInfo("vendor_id") == "AuthenticAMD":
            attrs.append(
                "hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
            )
        elif cpuInfo("vendor_id") == "GenuineIntel":
            attrs.append(
                "hardware.cpu.intel.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
            )

        if "svm" in cpuInfo("flags"):
            kernelModules.append("kvm-amd")
        elif "vmx" in cpuInfo("flags"):
            kernelModules.append("kvm-intel")

        if os.path.exists(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
        ):
            governors = Path(
                "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
            ).read_text()
            desired_governors = ["ondemand", "powersave"]
            for dg in desired_governors:
                if dg in governors:
                    attrs.append(f'powerManagement.cpuFreqGovernor = lib.mkDefault "{dg}";')
                    break


    def virtSection():
        virt = (
            (subprocess.run(["systemd-detect-virt"], capture_output=True, text=True)).stdout
        ).strip()
        #ic(virt)
        if virt == "oracle":
            attrs.append("virtualisation.virtualbox.guest.enable = true;")
            ic()
        if virt == "microsoft":
            attrs.append("virtualisation.hypervGuest.enable = true;")
            ic()
        if virt == "systemd-nspawn":
            ic()
            attrs.append("boot.isContainer = true;")
        if virt == "qemu" or virt == "kvm" or virt == "bochs":
            ic()
            imports.append('(modulesPath + "/profiles/qemu-quest.nix")')


    imports.append('(modulesPath + "/installer/scan/not-detected.nix")')


    def udevGet():
        context = pyudev.Context()
        for device in context.list_devices(subsystem='input'):
            input_type = (device.get('ID_INPUT_KEYBOARD'))
            if input_type:
                usb_driver = (device.get('ID_USB_DRIVER'))
                print(usb_driver)



    udevGet()

    def pciCheck(path):
        vendor = Path(path + "/vendor").read_text()
        device = Path(path + "/device").read_text()
        pclass = Path(path + "/class").read_text()
        #ic(f"{path}: {vendor} {device} {pclass}")

        module = ""
        if Path(path + "/driver/module").exists():
            #ic()
            module = (Path(path + "/driver/module").resolve()).name

        if module:
            matchmodulei = [
                # Mass-storage controller.  Definitely important.
                "0x01",
                # Firewire controller.  A disk might be attached.
                "0x0c00",
                # USB controller.  Needed if we want to use the
                # keyboard when things go wrong in the initrd.
                "0x0c03"
            ]
            if any(x in pclass for x in matchmodulei):
                initrdAvailableKernelModules.append(module)

        if vendor == "0x1af4" and device == "0x1004":
            initrdAvailableKernelModules.append("virtio_scsi")


        # broadcom
        if vendor == "0x14e4":
            # broadcom STA driver (wl.ko)
            broadcomSTADevList = [
                # list taken from https://packages.debian.org/stretch/broadcom-sta-source README.txt
                "0x4311",
                "0x4312",
                "0x4313",
                "0x4315",
                "0x4727",
                "0x4328",
                "0x4329",
                "0x432a",
                "0x432b",
                "0x432c",
                "0x432d",
                "0x4365",
                "0x4353",
                "0x4357",
                "0x4358",
                "0x4359",
                "0x4331",
                "0x43a0",
                # from 2aa3580a5e49d04bfa63c7509092317b49f54952
                "0x43b1"
            ]
            broadcomFullMacDevList = [
                # list taken from
                # https://github.com/torvalds/linux/blob/master/drivers/net/wireless/broadcom/brcm80211/include/brcm_hw_ids.h
                # PCIE Device IDs
                "0x43a3",
                "0x43df",
                "0x43ec",
                "0x43d3",
                "0x43d9",
                "0x43e9",
                "0x43ef",
                "0x43ba",
                "0x43bb",
                "0x43bc",
                "0x4464",
                "0x43ca",
                "0x43cb",
                "0x43cc",
                "0x43c3",
                "0x43c4",
                "0x43c5",
                "0x440d",
            ]
            if any(x in device for x in broadcomSTADevList):
                modulePackages.append("config.boot.kernelPackages.broadcom_sta")
                kernelModules.append("wl")
            if any(x in device for x in broadcomFullMacDevList):
                firmwarePackages.append("pkgs.firmwareLinuxNonfree")
                kernelModules.append("brcmfmac")

    for path in os.listdir("/sys/bus/pci/devices"):
        path = f"/sys/bus/pci/devices/{path}"
        pciCheck(path)




    videoDriver = 0
    if videoDriver:
        attrs.append(f'services.xserver.videoDrivers = [ "{videoDriver}" ]')


    def fsSection():
        pass


    fsSection()




    def toNixStringList(*args):
        res = ""
        for v in args:
            res += f' "{v}"'
        return res


    def toNixList(*args):
        res = ""
        for v in args:
            res += f" {v}"
        return res


    def multiLineList(indent, *args):
        if not args:
            return " [ ]"
        res = f"\n{indent}[ "
        first = 1
        for v in args:
            if not first:
                res += f"{indent}  "
            first = 0
            res += f"{v}\n"
        res += f"{indent}]"
        return res

    def genHwFile(
        initrdAvailableKernelModules,
        initrdKernelModules,
        kernelModules,
        modulePackages,
        firmwarePackages,
        imports,
    ):
        # unpacking using * so we don't return, for example, "['usbhid']"
        initrdAvailableKernelModules = toNixStringList(
            *(uniq(initrdAvailableKernelModules))
        )
        initrdKernelModules = toNixStringList(*(uniq(initrdKernelModules)))
        kernelModules = toNixStringList(*(uniq(kernelModules)))
        modulePackages = toNixList(*(uniq(modulePackages)))
        firmwarePackages = toNixList(*(uniq(firmwarePackages)))
        imports = multiLineList("    ", *imports)
        #ic(initrdAvailableKernelModules)
        with open(f"{rootDir}{outDir}/hardware-configuration.nix", "w") as tf:
            #ic(tf)
            tf.write(
                "# Do not modify this file!  It was generated by ‘nixos-generate-config’\n"
                "# and may be overwritten by future invocations.  Please make changes\n"
                "# to /etc/nixos/configuration.nix instead.\n"
                "{ config, lib, pkgs, modulesPath, ... }:\n"
                "\n"
                "{\n"
                f"  imports ={imports};\n"
                "\n"
                f"  boot.initrd.availableKernelModules = [{initrdAvailableKernelModules} ];\n"
                f"  boot.initrd.kernelModules = [{initrdKernelModules} ];\n"
                f"  boot.kernelModules = [{kernelModules} ];\n"
                f"  boot.extraModulePackages = [{modulePackages} ];\n"
                f"  hardware.firmware = [{firmwarePackages} ];\n"
            )
            for attr in uniq(attrs):
                tf.write("  " + attr + "\n")
            tf.write("\n}\n")


    virtSection()
    cpuSection()
    genHwFile(
        initrdAvailableKernelModules,
        initrdKernelModules,
        kernelModules,
        modulePackages,
        firmwarePackages,
        imports,
    )

if __name__ == '__main__':
  main()
