# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

import logging
import os
from typing import IO

from ._imports import (
    ImportGraph,
    determine_source_module_name,
    toplevel_package_of,
)
from ._normalization import shortest_first_rotated

_logger = logging.getLogger(__name__)


class ToplevelCollector:
    def __init__(self):
        self._toplevel_packages = set()

    def add_file(self, abs_path: str):
        module_name = determine_source_module_name(abs_path)
        toplevel_package = toplevel_package_of(module_name)
        self._toplevel_packages.add(toplevel_package)

    def __iter__(self):
        return sorted(self._toplevel_packages)

    def touched_by(self, module_names: list[str]) -> bool:
        return any(
            (toplevel_package_of(module_name) in self._toplevel_packages)
            for module_name in module_names
        )


def _format_cycle(cycle: list[str]) -> str:
    normalized_cycle = shortest_first_rotated(cycle)
    normalized_cycle.append(normalized_cycle[0])
    return " -> ".join(normalized_cycle)


def _report_cycles(
    imports: ImportGraph,
    toplevel_packages: ToplevelCollector,
    file_: IO,
) -> int:
    lines = []
    for cycle in imports.iterate_cycles():
        if not toplevel_packages.touched_by(cycle):
            continue
        lines.append(_format_cycle(cycle))
    count_cycles = len(lines)

    if lines:
        print("\n".join(sorted(lines)), file=file_)
        print(file=file_)

    print(f"{count_cycles} cycle(s).")

    return count_cycles


def run(abs_paths: list[str], *, follow: bool, file_: IO) -> int:
    imports = ImportGraph()
    toplevel_packages = ToplevelCollector()

    for abs_path in abs_paths:
        if not os.path.exists(abs_path):
            # This will raise FileNotFoundError the way that stdlib does:
            open(abs_path)  # noqa: SIM115
            raise AssertionError  # avoiding "assert" in case of "python3 -O"

        if os.path.isdir(abs_path):
            # Find all .py files
            _logger.info(
                f"Scanning directory {abs_path!r} for Python files recursively...",
            )
            for root, folders, files in os.walk(abs_path):
                folders[:] = sorted(folders)  # for alphabetical ascend

                py_files = sorted(
                    os.path.join(root, f) for f in files if f.endswith(".py")
                )
                if not py_files:
                    continue

                toplevel_packages.add_file(py_files[0])  # any of them would do

                for py_file in py_files:
                    imports.add_file(py_file, follow=follow)
        else:
            toplevel_packages.add_file(abs_path)

            imports.add_file(abs_path, follow=follow)

    return _report_cycles(imports, toplevel_packages, file_)
