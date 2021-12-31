from string import Template

import psutil
import pyudev

from nixos_gen_config.classes import nixConfigAttrs

fsTemplate = Template('''\

  fileSystems."${mountpoint}" =
    { device = "${device}";
      fsType = "${filesystem}";
    };
\
''')

def get_fs(nix_config: nixConfigAttrs) -> None:

    context = pyudev.Context()
    devices = context.list_devices(subsystem="block")

    for part in psutil.disk_partitions(all=False):
        stable_path_device = 0
        for device in devices:
            if device.get("DEVNAME") == part.device:
                uuid = device.get("ID_FS_UUID")
                stable_path_device = f"/dev/disk/by-uuid/{uuid}"

        if stable_path_device:
            dev = stable_path_device
        else:
            dev = part.device
        f_s = fsTemplate.substitute(
            mountpoint = part.mountpoint,
            device = dev,
            filesystem = part.fstype
        )
        nix_config.attrs.append(f_s)
