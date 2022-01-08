from pathlib import Path
import subprocess

from icecream import ic
import pyudev

from nixos_gen_config import auxiliary_functions as af
from nixos_gen_config.classes import NixConfigAttrs


def cpu_info(field: str) -> str:
    cpudata: dict[str, str] = {}
    # list comprehension to remove empty lines which break split
    cpuinfo: list[str] = [s for s in (Path("/proc/cpuinfo").read_text("utf-8")).splitlines() if s]
    for line in cpuinfo:
        left, right = line.split(":")
        cpudata[left.strip()] = right.strip()
    return cpudata[field]


def cpu_section(nix_config: NixConfigAttrs) -> None:
    if cpu_info("vendor_id") == "AuthenticAMD":
        nix_config.attrs.append(
            "hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
        )
    elif cpu_info("vendor_id") == "GenuineIntel":
        nix_config.attrs.append(
            "hardware.cpu.intel.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;"
        )

    if "svm" in cpu_info("flags"):
        nix_config.kernel_modules.append("kvm-amd")
    if "vmx" in cpu_info("flags"):
        nix_config.kernel_modules.append("kvm-intel")

    if Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors").exists():
        governors = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors").read_text("utf-8")
        desired_governors = ["ondemand", "powersave"]
        for d_g in desired_governors:
            if d_g in governors:
                nix_config.attrs.append(f'powerManagement.cpuFreqGovernor = lib.mkDefault "{d_g}";')
                break


# TODO
def gpu_section(nix_config: NixConfigAttrs) -> None:
    video_driver = 0
    if video_driver:
        nix_config.attrs.append(f'services.xserver.videoDrivers = [ "{video_driver}" ]')


def usb_keyboard(nix_config: NixConfigAttrs, device: pyudev.Device) -> None:
    usb_driver: str
    if device.get("ID_INPUT_KEYBOARD") and (usb_driver := device.get("ID_USB_DRIVER")):
        nix_config.initrd_available_kernel_modules.append(usb_driver)


def pci(nix_config: NixConfigAttrs, device: pyudev.Device) -> None:
    pci_class: str = device.get("ID_PCI_CLASS_FROM_DATABASE")
    pci_id: str = device.get("ID_PCI_SUBCLASS_FROM_DATABASE")
    pci_driver: str = device.get("DRIVER")
    # https://github.com/systemd/systemd/blob/main/hwdb.d/20-pci-classes.hwdb
    class_filter: list[str] = [
        "USB controller",
        "FireWire (IEEE 1394)",
        "Mass storage controller",
    ]
    model_dict: dict[str, str] = {
        # for some of these the device loads something that has a driver different
        # to itself
        "Virtio SCSI": "virtio_scsi",
    }
    driver_overrides: dict[str, str] = {
        # xhci_pci has xhci_hcd in deps. xhci_pci will be needed anyways so this keeps the list shorter.
        "xhci_hcd": "xhci_pci",
    }
    if (pci_id or pci_class) and pci_driver:
        if any(filter in (pci_class, pci_id) for filter in class_filter):
            if pci_driver in list(driver_overrides):
                pci_driver = driver_overrides[pci_driver]
            nix_config.initrd_available_kernel_modules.append(pci_driver)

    model_id: str
    if model_id := device.get("ID_MODEL_FROM_DATABASE"):
        if any(filter in model_id for filter in model_dict):
            nix_config.initrd_available_kernel_modules.append(model_dict[model_id])


def wifi(nix_config: NixConfigAttrs, device: pyudev.Device) -> None:
    broadcom_sta_list: list[str] = [
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
    model_id: str
    if model_id := device.get("ID_MODEL_FROM_DATABASE"):
        if any(filter in model_id for filter in broadcom_sta_list):
            nix_config.module_packages.append("config.boot.kernelPackages.broadcom_sta")
            nix_config.kernel_modules.append("wl")

    # NOTE for reviewers: Intel3945ABG and Intel2200BG are included in enableRedistributableFirmware
    # devices that use brcmfmac are not needed to be specified due to the drivers being
    # included in firmwareLinuxNonfree


def bcache(nix_config: NixConfigAttrs, device: pyudev.Device) -> None:
    if device.get("ID_FS_TYPE") == "bcache":
        nix_config.initrd_available_kernel_modules.append("bcache")


def udev_section(nix_config: NixConfigAttrs) -> None:
    context: pyudev.Context = pyudev.Context()
    device: pyudev.Device
    for device in context.list_devices(subsystem="pci"):
        wifi(nix_config, device)
        pci(nix_config, device)

    for device in context.list_devices(subsystem="block"):
        bcache(nix_config, device)

    for device in context.list_devices(subsystem="input"):
        usb_keyboard(nix_config, device)


def virt_section(nix_config: NixConfigAttrs) -> None:
    virtcmd = None
    # systemd-detect-virt exits with 1 when virt = none
    try:
        virtcmd = subprocess.run(["systemd-detect-virt"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        # Provide firmware for devices that are not detected by this script,
        # unless we're in a VM/container.
        nix_config.imports.append('(modulesPath + "/installer/scan/not-detected.nix")')

    if virtcmd:
        virt: str = (virtcmd.stdout).strip()
        if virt == "oracle":
            nix_config.attrs.append(af.to_nix_true_attr("virtualisation.virtualbox.guest.enable"))
        if virt == "microsoft":
            nix_config.attrs.append(af.to_nix_true_attr("virtualisation.hypervGuest.enable"))
        if virt == "systemd-nspawn":
            nix_config.attrs.append(af.to_nix_true_attr("boot.isContainer"))
        if virt in ("qemu", "kvm", "bochs"):
            nix_config.imports.append('(modulesPath + "/profiles/qemu-quest.nix")')
