import os
from pathlib import Path
import subprocess

from icecream import ic  # type: ignore
import pyudev  # type: ignore

from nixos_gen_config import auxiliary_functions  # type: ignore
from nixos_gen_config.arguments import process_args  # type: ignore


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
            cpuinfo = Path("/proc/cpuinfo").read_text('utf-8')
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
            governors = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors").read_text('utf-8')
            desired_governors = ["ondemand", "powersave"]
            for d_g in desired_governors:
                if d_g in governors:
                    attrs.append(f'powerManagement.cpuFreqGovernor = lib.mkDefault "{d_g}";')
                    break

    def virtSection():
        virtcmd = ""
        # systemd-detect-virt exits with 1 when virt = none
        try:
            virtcmd = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            # Provide firmware for devices that are not detected by this script,
            # unless we're in a VM/container.
            imports.append('(modulesPath + "/installer/scan/not-detected.nix")')


        if virtcmd:
            virt = (virtcmd.stdout).strip()
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
            if virt in ("qemu", "kvm", "bochs"):
                ic()
                imports.append('(modulesPath + "/profiles/qemu-quest.nix")')


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
                pci_class = device.get("ID_PCI_CLASS_FROM_DATABASE")
                pci_id = device.get("ID_PCI_SUBCLASS_FROM_DATABASE")
                pci_driver = device.get("DRIVER")
                model_id = device.get("ID_MODEL_FROM_DATABASE")
                # https://github.com/systemd/systemd/blob/main/hwdb.d/20-pci-classes.hwdb
                classFilter = [
                    "USB controller",
                    "FireWire (IEEE 1394)",
                    "Mass storage controller",
                ]
                modelDict = {
                    # for some of these the device loads something that has a driver different
                    # to itself
                    "Virtio SCSI": "virtio_scsi",
                }
                driverOverride = {
                    # xhci_pci has xhci_hcd in deps. xhci_pci will be needed anyways so this keeps the list shorter.
                    "xhci_hcd": "xhci_pci",
                }
                if (pci_id or pci_class) and pci_driver:
                    if any(filter in (pci_class, pci_id) for filter in classFilter):
                        if pci_driver in list(driverOverride):
                            pci_driver = driverOverride[pci_driver]
                        initrdAvailableKernelModules.append(pci_driver)

                if model_id:
                    if any(filter in model_id for filter in modelDict):
                        initrdAvailableKernelModules.append(modelDict[model_id])

        if query[0] == "wifiDrivers":
            for device in context.list_devices(subsystem="pci"):
                pci_driver = device.get("DRIVER")
                model_id = device.get("ID_MODEL_FROM_DATABASE")
                classFilter = [
                    "Network controller",
                ]
                broadcomSTAList = [
                    "BCM4311",  # https://linux-hardware.org/?id=pci:14e4-4311
                    "BCM4360",  # https://linux-hardware.org/?id=pci:14e4-43a0
                    "BCM4322",  # https://linux-hardware.org/?id=pci:14e4-432b
                    "BCM4313",  # https://linux-hardware.org/?id=pci:14e4-4727
                    "BCM4312",  # https://linux-hardware.org/?id=pci:14e4-4315
                    "BCM4321",  # https://linux-hardware.org/?id=pci:14e4-4328
                    "BCM43142",  # https://linux-hardware.org/?id=pci:14e4-4365
                    "BCM43224",  # https://linux-hardware.org/?id=pci:14e4-4353
                    "BCM43225",  # https://linux-hardware.org/?id=pci:14e4-4357
                    "BCM43227",  # https://linux-hardware.org/?id=pci:14e4-4358
                    "BCM43228",  # https://linux-hardware.org/?id=pci:14e4-4359
                    "BCM4331",  # https://linux-hardware.org/?id=pci:14e4-4331
                    "BCM4352",  # https://linux-hardware.org/?id=pci:14e4-43b1
                    # more devices probably belong here. however it is really tedious to go through them
                    # https://linux-hardware.org/?view=search&vendor=Broadcom&typeid=net%2Fwireless#list
                    # https://github.com/systemd/systemd/blob/main/hwdb.d/20-pci-vendor-model.hwdb
                    # https://linux-hardware.org/?view=search
                ]
                if model_id:
                    if any(filter in model_id for filter in broadcomSTAList):
                        modulePackages.append("config.boot.kernelPackages.broadcom_sta")
                        kernelModules.append("wl")

                # NOTE for reviewers: Intel3945ABG and Intel2200BG are included in enableRedistributableFirmware
                # devices that use brcmfmac are not needed to be specified due to the drivers being
                # included in firmwareLinuxNonfree

    udevGet("usbKbDriver")
    udevGet("zfsPartitions")
    udevGet("pciDrivers")
    udevGet("wifiDrivers")

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
        with open(f"{rootDir}{outDir}/hardware-configuration.nix", "w", encoding='utf-8') as t_f:
            # ic(t_f)
            t_f.write(
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
                t_f.write("  " + attr + "\n")
            t_f.write("\n}\n")

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
