from dataclasses import dataclass, field


@dataclass
class NixConfigAttrs:
    attrs: list[str] = field(default_factory=list)
    fsattrs: list[str] = field(default_factory=list)
    initrd_available_kernel_modules: list[str] = field(default_factory=list)
    initrd_kernel_modules: list[str] = field(default_factory=list)
    kernel_modules: list[str] = field(default_factory=list)
    kernel_modules: list[str] = field(default_factory=list)
    module_packages: list[str] = field(default_factory=list)
    firmware_packages: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
