def uniq(list1):
    uniq_list = []
    for x in list1:
        if x not in uniq_list:
            uniq_list.append(x)
    return uniq_list


def to_nix_string_list(*args):
    res = ""
    for v in args:
        res += f' "{v}"'
    return res


def to_nix_list(*args):
    res = ""
    for v in args:
        res += f" {v}"
    return res


def to_nix_multi_line_list(indent, *args):
    if not args:
        return " [ ]"
    res = f"\n{indent}[ "
    first = 1
    for v in args:
        if not first:
            res += f"{indent}  "
        first = 0
        res += f"{v}\n"
    res += f"{indent}]"
    return res
