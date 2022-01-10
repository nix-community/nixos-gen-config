from pathlib import Path
from string import Template

import psutil
import pyudev

from nixos_gen_config.classes import NixConfigAttrs

fsTemplate: Template = Template(
    """
  fileSystems."${mountpoint}" =
    { device = "${device}";
      fsType = "${filesystem}";
    };
"""
)
special_fs: list[str] = ["/proc", "/dev", "/sys", "/run", "/var/lib/nfs/rpc_pipefs"]


def get_fs(nix_config: NixConfigAttrs, root_dir: Path) -> None:

    context: pyudev.Context = pyudev.Context()
    devices: pyudev.Device = context.list_devices(subsystem="block")

    for part in psutil.disk_partitions(all=True):
        if not part.mountpoint.startswith(str(root_dir)):
            continue

        if [x for x in special_fs if x in part.mountpoint]:
            continue

        stable_device_path: str = ""
        for device in devices:
            if device.get("DEVNAME") == part.device:
                uuid = device.get("ID_FS_UUID")
                stable_device_path = f"/dev/disk/by-uuid/{uuid}"

        # if stable_device_path then use that
        device_name: str = stable_device_path or part.device

        f_s = fsTemplate.substitute(mountpoint=part.mountpoint, device=device_name, filesystem=part.fstype)
        nix_config.fsattrs.append(f_s)
