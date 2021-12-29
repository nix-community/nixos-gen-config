import os
from pathlib import Path
import subprocess
import sys

from icecream import ic # type: ignore
import pyudev # type: ignore

import nixos_gen_config.auxiliary_functions as auxiliary_functions  # type: ignore
from nixos_gen_config.arguments import process_args # type: ignore


def main():
    uniq = auxiliary_functions.uniq
    toNixStringList = auxiliary_functions.toNixStringList
    toNixList = auxiliary_functions.toNixList
    multiLineList = auxiliary_functions.multiLineList

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

        if os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"):
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
        # ic(virt)
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

    def udevGet(*query):
        context = pyudev.Context()

        if query[0] == "usbKbDriver":
            for device in context.list_devices(subsystem="input"):
                input_type = device.get("ID_INPUT_KEYBOARD")
                if input_type:
                    usb_driver = device.get("ID_USB_DRIVER")
                    # ic(usb_driver)
                    initrdAvailableKernelModules.append(usb_driver)


        if query[0] == "zfsPartitions":
            for device in context.list_devices(subsystem="block"):
                fs_type = device.get("ID_FS_TYPE")
                if fs_type == "zfs_member":
                    fs_label = device.get("ID_FS_LABEL")
                    ic(fs_label)

        if query[0] == "pciDrivers":
            for device in context.list_devices(subsystem="pci"):
                # https://github.com/systemd/systemd/blob/main/hwdb.d/20-pci-classes.hwdb
                pci_class = device.get("ID_PCI_CLASS_FROM_DATABASE")
                pci_id = device.get("ID_PCI_SUBCLASS_FROM_DATABASE")
                pci_driver = device.get("DRIVER")
                classFilter = [
                    "USB controller",
                    "FireWire (IEEE 1394)",
                    "Mass storage controller",
                ]
                driverOverride = {
                    # xhci_pci has xhci_hcd in deps. xhci_pci will be needed anyways so this keeps the list shorter.
                    "xhci_hcd": "xhci_pci",
                }
                if (pci_id or pci_class) and pci_driver:
                    if any(filter in (pci_class, pci_id) for filter in classFilter):
                        if pci_driver in driverOverride:
                            pci_driver = driverOverride[pci_driver]
                        initrdAvailableKernelModules.append(pci_driver)
                    #if pci_id == "USB controller" and pci_driver:
                    #    initrdAvailableKernelModules.append(pci_driver)

    udevGet("usbKbDriver")
    udevGet("zfsPartitions")
    udevGet("pciDrivers")


    def pciCheck(path):
        vendor = Path(path + "/vendor").read_text()
        device = Path(path + "/device").read_text()
        pclass = Path(path + "/class").read_text()

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
                "0x43b1",
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


    def genHwFile(
        initrdAvailableKernelModules,
        initrdKernelModules,
        kernelModules,
        modulePackages,
        firmwarePackages,
        imports,
    ):
        # unpacking using * so we don't return, for example, "['usbhid']"
        initrdAvailableKernelModules = toNixStringList(*(uniq(initrdAvailableKernelModules)))
        initrdKernelModules = toNixStringList(*(uniq(initrdKernelModules)))
        kernelModules = toNixStringList(*(uniq(kernelModules)))
        modulePackages = toNixList(*(uniq(modulePackages)))
        firmwarePackages = toNixList(*(uniq(firmwarePackages)))
        imports = multiLineList("    ", *imports)
        # ic(initrdAvailableKernelModules)
        with open(f"{rootDir}{outDir}/hardware-configuration.nix", "w") as tf:
            # ic(tf)
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


if __name__ == "__main__":
    main()
