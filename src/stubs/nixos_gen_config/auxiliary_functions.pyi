def uniq(list1: list[str]) -> list[str]: ...
def to_nix_string_list(*args: str) -> str: ...
def to_nix_list(*args: str) -> str: ...
def to_nix_multi_line_list(indent: str, *args: str) -> str: ...
def to_nix_true_attr(attr: str) -> str: ...
def to_nix_false_attr(attr: str) -> str: ...
def get_config_dir(out_dir: str, root_dir: str) -> str: ...
