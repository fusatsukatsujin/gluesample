"""Shared helper for parsing optional Glue job arguments (--NAME value)."""


def resolve_optional(argv, name, default):
    flag = f"--{name}"
    if flag in argv:
        idx = argv.index(flag)
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return default
