# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

import logging
import os.path
import sys

from import_deps import ast_imports
from networkx import DiGraph, chordless_cycles

_logger = logging.getLogger(__name__)

_stdlib_module_names = set()  # initialized via _initialize_stdlib_module_names() below


def toplevel_package_of(module_name: str) -> str:
    return module_name.split(".")[0]


def _initialize_stdlib_module_names():
    from stdlib_list.base import long_versions, stdlib_list

    for long_version in long_versions:
        _stdlib_module_names.update(stdlib_list(long_version))


def in_standard_library(candidate_module_name: str) -> bool:
    if not _stdlib_module_names:
        _initialize_stdlib_module_names()
        assert _stdlib_module_names

    return toplevel_package_of(candidate_module_name) in _stdlib_module_names


class PythonSourceNotFoundError(Exception):
    def __init__(self, module_names: list[str]):
        self.module_names = module_names

    @property
    def most_generic_module_name(self):
        return self.module_names[-1]

    def __str__(self):
        return (
            f"Import {self.most_generic_module_name!r} could not be resolved"
            " to a Python source file with regard to PYTHONPATH."
        )


def determine_path_of(module_name: str, _breadcrumbs: list[str] | None = None) -> str:
    if _breadcrumbs is None:
        _breadcrumbs = []
    _breadcrumbs.append(module_name)

    module_name_split = module_name.split(".")

    for path in sys.path:
        module_candidate_path = os.path.join(
            path,
            *(module_name_split[:-1] + [module_name_split[-1] + ".py"]),
        )
        if os.path.exists(module_candidate_path):
            return module_candidate_path

        package_candidate_path = os.path.join(
            path,
            *(*module_name_split, "__init__.py"),
        )
        if os.path.exists(package_candidate_path):
            return package_candidate_path

    # Let's try to make the error about top-level packages
    if len(module_name_split) > 1:
        parent_module_name = ".".join(module_name_split[:-1])

        # Let's see if this raises ModuleNotFoundError:
        determine_path_of(parent_module_name, _breadcrumbs)

    raise PythonSourceNotFoundError(_breadcrumbs)


def determine_source_module_name(abs_path: str) -> str:
    abs_path_backup = abs_path

    if not abs_path.endswith(".py"):
        raise ValueError(f"Path {abs_path!r} does not end in '.py'.")  # noqa: EM102, TRY003
    abs_path = abs_path[: -len(".py")]

    parts = []
    while True:
        package_path = os.path.dirname(abs_path)
        module_name = os.path.basename(abs_path)
        init_py_path = os.path.join(package_path, "__init__.py")

        parts.append(module_name)
        abs_path = package_path

        if not os.path.exists(init_py_path):
            module_name = ".".join(reversed(parts))
            _logger.debug(
                f"File {abs_path_backup!r} found to be module {module_name!r}.",
            )
            return module_name


def without_dot_init(module_name):
    if not module_name.endswith(".__init__"):
        return module_name
    return module_name[: -len(".__init__")]


def determine_target_module_name(
    source_module: str,
    module_name_or_none: str | None,
    object_name: str,
    as_name: str | None,
    depth_or_none: int | None,
) -> str:
    source_module_split = source_module.split(".")

    if depth_or_none is None:
        if module_name_or_none is None:
            target_module = object_name  # case "import <object_name>"
        else:
            # case "from <module_name_or_none> import <object_name>"
            target_module = module_name_or_none
    else:  # case "from [..] import [..]"
        if module_name_or_none is None:
            target_module_path = source_module_split[:-depth_or_none]
        else:
            target_module_path = source_module_split[:-depth_or_none] + [
                module_name_or_none,
            ]
        target_module = ".".join(target_module_path)

    _logger.debug(
        f"Import {(module_name_or_none, object_name, as_name, depth_or_none)}"
        f" from module {source_module!r} found to target module {target_module!r}.",
    )

    return target_module


class ImportGraph:
    def __init__(self):
        self._imports_from = {}
        self._seen_files = set()
        self._tried_to_follow = set()

    def _add_module(self, module_name: str, *, follow: bool):
        if module_name in self._tried_to_follow:
            _logger.debug(f"Skipping module {module_name!r} as tried before...")
            return

        self._tried_to_follow.add(module_name)

        module_filename = determine_path_of(module_name)

        self.add_file(module_filename, follow=follow)

    def add_file(self, abs_path: str, *, follow: bool):
        if abs_path in self._seen_files:
            _logger.debug(f"Skipping file {abs_path!r} as seen before...")
            return

        _logger.info(f"Adding file {abs_path!r}...")

        self._seen_files.add(abs_path)

        source_module = determine_source_module_name(abs_path)
        target_modules = self._imports_from.setdefault(
            without_dot_init(source_module),
            set(),
        )

        for module_name_or_none, object_name, as_name, depth_or_none in ast_imports(
            abs_path,
        ):
            target_module = determine_target_module_name(
                source_module,
                module_name_or_none,
                object_name,
                as_name,
                depth_or_none,
            )
            target_module = without_dot_init(target_module)

            if in_standard_library(target_module):
                continue

            if target_module not in target_modules:
                _logger.info(
                    f"Recording import from {source_module!r} to {target_module!r}...",
                )
            target_modules.add(target_module)

        if follow and target_modules:
            for module_name in target_modules:
                try:
                    self._add_module(module_name, follow=True)
                except PythonSourceNotFoundError as e:  # noqa: PERF203
                    if e.most_generic_module_name not in self._tried_to_follow:
                        _logger.warning(e)
                    self._tried_to_follow.update(e.module_names)

    def iterate_cycles(self):
        edges = []
        for source, targets in self._imports_from.items():
            for target in targets:
                edges.append((source, target))  # noqa: PERF401
        graph = DiGraph(edges)
        yield from chordless_cycles(graph)
