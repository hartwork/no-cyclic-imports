# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

import os.path
from textwrap import dedent


def add_cyclic_import_to(directory: str) -> tuple[str, str, str, str, str, str]:
    package_name = "package123"
    package_dir = os.path.join(directory, package_name)
    init_py = os.path.join(package_dir, "__init__.py")
    a_py = os.path.join(package_dir, "a.py")
    b_py = os.path.join(package_dir, "b.py")

    os.mkdir(package_dir)

    with open(init_py, "w") as f:
        print(
            dedent("""\
                import coverage  # to feed follow-mode
                from .a import a
                c = 'c'
            """),
            file=f,
        )

    with open(a_py, "w") as f:
        print(
            dedent("""\
                import coverage  # to feed follow-mode
                from .b import b
                a = 'a'
            """),
            file=f,
        )

    with open(b_py, "w") as f:
        print(
            dedent("""\
                import coverage  # to feed follow-mode
                from . import c
                b = 'b'
            """),
            file=f,
        )

    package_a_name = f"{package_name}.a"
    package_b_name = f"{package_name}.b"

    return init_py, a_py, b_py, package_name, package_a_name, package_b_name
