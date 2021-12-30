import os
from pathlib import Path
import subprocess

from icecream import ic  # type: ignore
import pyudev  # type: ignore

from nixos_gen_config import auxiliary_functions  # type: ignore
from nixos_gen_config.arguments import process_args  # type: ignore


def main():
    uniq = auxiliary_functions.uniq
    to_nix_string_list = auxiliary_functions.to_nix_string_list
    to_nix_list = auxiliary_functions.to_nix_list
    to_nix_multi_line_list = auxiliary_functions.to_nix_multi_line_list

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

    attrs = []
    initrd_available_kernel_modules = []
    initrd_kernel_modules = []
    kernel_modules = []
    module_packages = []
    firmware_packages = []
    imports = []

    def cpu_section():
        cpudata = {}

        def cpu_info(field):
            cpuinfo = Path("/proc/cpuinfo").read_text('utf-8')
            for line in cpuinfo.split("\n"):
                # cpuinfo has a empty line at the end
                if line == "":
                    continue
                left, right = line.split(":")
                cpudata[left.strip()] = right.strip()
            return cpudata[field]

        if cpu_info("vendor_id") == "AuthenticAMD":
            attrs.append(
                "hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
            )
        elif cpu_info("vendor_id") == "GenuineIntel":
            attrs.append(
                "hardware.cpu.intel.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
            )

        if "svm" in cpu_info("flags"):
            kernel_modules.append("kvm-amd")
        elif "vmx" in cpu_info("flags"):
            kernel_modules.append("kvm-intel")

        if os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"):
            governors = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors").read_text('utf-8')
            desired_governors = ["ondemand", "powersave"]
            for d_g in desired_governors:
                if d_g in governors:
                    attrs.append(f'powerManagement.cpuFreqGovernor = lib.mkDefault "{d_g}";')
                    break

    def virt_section():
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


    def udevGet(*query: str) -> None:
        context = pyudev.Context()

        if query[0] == "usbKbDriver":
            for device in context.list_devices(subsystem="input"):
                input_type = device.get("ID_INPUT_KEYBOARD")
                if input_type:
                    usb_driver = device.get("ID_USB_DRIVER")
                    # ic(usb_driver)
                    initrd_available_kernel_modules.append(usb_driver)

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
                class_filter = [
                    "USB controller",
                    "FireWire (IEEE 1394)",
                    "Mass storage controller",
                ]
                model_dict = {
                    # for some of these the device loads something that has a driver different
                    # to itself
                    "Virtio SCSI": "virtio_scsi",
                }
                driver_overrides = {
                    # xhci_pci has xhci_hcd in deps. xhci_pci will be needed anyways so this keeps the list shorter.
                    "xhci_hcd": "xhci_pci",
                }
                if (pci_id or pci_class) and pci_driver:
                    if any(filter in (pci_class, pci_id) for filter in class_filter):
                        if pci_driver in list(driver_overrides):
                            pci_driver = driver_overrides[pci_driver]
                        initrd_available_kernel_modules.append(pci_driver)

                if model_id:
                    if any(filter in model_id for filter in model_dict):
                        initrd_available_kernel_modules.append(model_dict[model_id])

        if query[0] == "wifiDrivers":
            for device in context.list_devices(subsystem="pci"):
                pci_driver = device.get("DRIVER")
                model_id = device.get("ID_MODEL_FROM_DATABASE")
                class_filter = [
                    "Network controller",
                ]
                broadcom_sta_list = [
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
                    if any(filter in model_id for filter in broadcom_sta_list):
                        module_packages.append("config.boot.kernelPackages.broadcom_sta")
                        kernel_modules.append("wl")

                # NOTE for reviewers: Intel3945ABG and Intel2200BG are included in enableRedistributableFirmware
                # devices that use brcmfmac are not needed to be specified due to the drivers being
                # included in firmwareLinuxNonfree

    udevGet("usbKbDriver")
    udevGet("zfsPartitions")
    udevGet("pciDrivers")
    udevGet("wifiDrivers")

    video_driver = 0
    if video_driver:
        attrs.append(f'services.xserver.videoDrivers = [ "{video_driver}" ]')

    def gen_hw_file(
        initrd_available_kernel_modules,
        initrd_kernel_modules,
        kernel_modules,
        module_packages,
        firmware_packages,
        imports,
    ):
        # unpacking using * so we don't return, for example, "['usbhid']"
        initrd_available_kernel_modules = to_nix_string_list(*(uniq(initrd_available_kernel_modules)))
        initrd_kernel_modules = to_nix_string_list(*(uniq(initrd_kernel_modules)))
        kernel_modules = to_nix_string_list(*(uniq(kernel_modules)))
        module_packages = to_nix_list(*(uniq(module_packages)))
        firmware_packages = to_nix_list(*(uniq(firmware_packages)))
        imports = to_nix_multi_line_list("    ", *imports)
        # ic(initrdAvailableKernelModules)
        with open(f"{root_dir}{out_dir}/hardware-configuration.nix", "w", encoding='utf-8') as t_f:
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
                f"  boot.initrd.availableKernelModules = [{initrd_available_kernel_modules} ];\n"
                f"  boot.initrd.kernelModules = [{initrd_kernel_modules} ];\n"
                f"  boot.kernelModules = [{kernel_modules} ];\n"
                f"  boot.extraModulePackages = [{module_packages} ];\n"
                f"  hardware.firmware = [{firmware_packages} ];\n"
            )
            for attr in uniq(attrs):
                t_f.write("  " + attr + "\n")
            t_f.write("\n}\n")

    virt_section()
    cpu_section()
    gen_hw_file(
        initrd_available_kernel_modules,
        initrd_kernel_modules,
        kernel_modules,
        module_packages,
        firmware_packages,
        imports,
    )


if __name__ == "__main__":
    main()
