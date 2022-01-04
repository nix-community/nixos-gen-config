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


def get_config_dir(out_dir: str, root_dir: str) -> str:
    config_dir = ""
    if out_dir != "/etc/nixos":
        config_dir = out_dir
    if root_dir:
        config_dir = f"{root_dir}{out_dir}"

    return config_dir
