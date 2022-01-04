class NixConfigAttrs:
    attrs: list[str]
    fsattrs: list[str]
    initrd_available_kernel_modules: list[str]
    initrd_kernel_modules: list[str]
    kernel_modules: list[str]
    module_packages: list[str]
    firmware_packages: list[str]
    imports: list[str]
    def __init__(self, attrs, fsattrs, initrd_available_kernel_modules, initrd_kernel_modules, kernel_modules, module_packages, firmware_packages, imports) -> None: ...
