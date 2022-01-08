from pathlib import Path


def uniq(list1: list[str]) -> list[str]:
    uniq_list: list[str] = []
    for item in list1:
        if item not in uniq_list:
            uniq_list.append(item)
    return uniq_list


def to_nix_string_list(*args: str) -> str:
    res = ""
    for item in args:
        res += f' "{item}"'
    return res


def to_nix_list(*args: str) -> str:
    res = ""
    for item in args:
        res += f" {item}"
    return res


def to_nix_multi_line_list(indent: str, *args: str) -> str:
    if not args:
        return " [ ]"
    res = f"\n{indent}[ "
    first = 1
    for item in args:
        if not first:
            res += f"{indent}  "
        first = 0
        res += f"{item}\n"
    res += f"{indent}]"
    return res


def to_nix_true_attr(attr: str) -> str:
    return f"{attr} = true;"


def to_nix_false_attr(attr: str) -> str:
    return f"{attr} = false;"


# '--root /mnt --dir thisdir' should save the config to
# $PWD/thisdir instead of /mnt/thisdir
# the perl script saved it to /mnt/thisdir and i think thats a bug
def get_config_dir(out_dir: Path, root_dir: Path) -> Path:
    config_dir: Path = out_dir
    if root_dir and out_dir == Path("/etc/nixos"):
        # Allow paths to be joined without worrying about a leading slash
        # https://bugs.python.org/issue44452
        config_dir = root_dir.joinpath(str(out_dir).lstrip("/"))

    return config_dir
