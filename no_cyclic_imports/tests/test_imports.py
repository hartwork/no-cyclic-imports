# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

import os
import pkgutil
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized

from .._imports import (
    ImportGraph,
    _initialize_stdlib_module_names,
    _stdlib_module_names,
    determine_path_of,
    determine_source_module_name,
    determine_target_module_name,
    in_standard_library,
    toplevel_package_of,
    without_dot_init,
)
from .._normalization import shortest_first_rotated
from .factories import add_cyclic_import_to


class ToplevelPackageOfTest(TestCase):
    def test(self):
        self.assertEqual(toplevel_package_of("one.two.three"), "one")


class InitializeStdlibModuleNamesTest(TestCase):
    def test(self):
        _stdlib_module_names.clear()
        self.assertNotIn("cStringIO", _stdlib_module_names)
        _initialize_stdlib_module_names()
        self.assertIn("cStringIO", _stdlib_module_names)


class InStandardLibraryTest(TestCase):
    @parameterized.expand(
        [
            ("os", True),
            ("os.path", True),
            ("requests", False),
        ],
    )
    def test(self, module_name, expected_result):
        actual_result = in_standard_library(module_name)
        self.assertEqual(actual_result, expected_result)


class DeterminePathOfTest(TestCase):
    @parameterized.expand(
        [
            (__name__, __file__),
            ("stdlib_list.base", pkgutil.get_loader("stdlib_list.base").get_filename()),
        ],
    )
    def test(self, module_name, expected_path):
        actual_path = determine_path_of(module_name)
        self.assertEqual(actual_path, expected_path)


class WithoutDotInitTest(TestCase):
    @parameterized.expand(
        [
            ("one.two.three", "one.two.three"),
            ("one.two.__init__", "one.two"),
        ],
    )
    def test(self, original_module_name, expected):
        actual = without_dot_init(original_module_name)
        self.assertEqual(actual, expected)


class DetermineSourceModuleName(TestCase):
    @parameterized.expand(
        [
            ("__file__", __file__, "no_cyclic_imports.tests.test_imports"),
            (
                "../__init__.py",
                os.path.join(os.path.dirname(__file__), "__init__.py"),
                "no_cyclic_imports.tests.__init__",
            ),
        ],
    )
    def test(self, _label, abs_path, expected_module_name):
        actual_module_name = determine_source_module_name(abs_path)
        self.assertEqual(actual_module_name, expected_module_name)


class DetermineTargetModuleName(TestCase):
    @parameterized.expand(
        [
            ("import package123", (None, "package123", None, None), "package123"),
            (
                "from package123 import symbol123",
                ("package123", "symbol123", None, 0),
                "package123",
            ),
            (
                "from package123 import symbol123 as alias123",
                ("package123", "symbol123", "alias123", 0),
                "package123",
            ),
            (
                "from . import symbol123",
                (None, "symbol123", None, 1),
                "no_cyclic_imports.tests",
            ),
            (
                "from .. import symbol123",
                (None, "symbol123", None, 2),
                "no_cyclic_imports",
            ),
            (
                "from .module123 import symbol123",
                ("module123", "symbol123", None, 1),
                "no_cyclic_imports.tests.module123",
            ),
            (
                "from ..module123 import symbol123",
                ("module123", "symbol123", None, 2),
                "no_cyclic_imports.module123",
            ),
        ],
    )
    def test(self, _label, ast_imports_quad, expected_target_module_name):
        source_module_name = determine_source_module_name(__file__)
        module_name_or_none, object_name, as_name, depth_or_none = ast_imports_quad

        actual_target_module_name = determine_target_module_name(
            source_module_name,
            module_name_or_none,
            object_name,
            as_name,
            depth_or_none,
        )

        self.assertEqual(actual_target_module_name, expected_target_module_name)


class ImportGraphTest(TestCase):
    def test_add_file__follow_false(self):
        imports = ImportGraph()

        imports.add_file(__file__, follow=False)

        self.assertEqual(
            imports._seen_files,
            {
                __file__,
            },
        )
        self.assertEqual(imports._tried_to_follow, set())
        self.assertEqual(
            imports._imports_from,
            {
                "no_cyclic_imports.tests.test_imports": {
                    "no_cyclic_imports._imports",
                    "no_cyclic_imports._normalization",
                    "no_cyclic_imports.tests.factories",
                    "parameterized",
                },
            },
        )

    def test_add_file__follow_true(self):
        imports = ImportGraph()

        imports.add_file(__file__, follow=True)

        self.assertIn(__file__, imports._seen_files)
        self.assertIn("no_cyclic_imports._imports", imports._tried_to_follow)
        self.assertEqual(
            imports._imports_from["no_cyclic_imports.tests.test_imports"],
            {
                "no_cyclic_imports._imports",
                "no_cyclic_imports._normalization",
                "no_cyclic_imports.tests.factories",
                "parameterized",
            },
        )
        self.assertEqual(
            imports._imports_from["no_cyclic_imports._imports"],
            {
                "import_deps",
                "networkx",
                "stdlib_list.base",
            },
        )

    def test_add_module__follow_false(self):
        imports = ImportGraph()
        module_name = determine_source_module_name(__file__)
        imports.add_file = Mock(side_effect=imports.add_file)

        imports._add_module(module_name, follow=False)

        self.assertEqual(imports.add_file.call_count, 1)
        self.assertEqual(
            imports._seen_files,
            {
                __file__,
            },
        )
        self.assertEqual(
            imports._tried_to_follow,
            {
                "no_cyclic_imports.tests.test_imports",
            },
        )

        self.assertEqual(
            imports._imports_from,
            {
                "no_cyclic_imports.tests.test_imports": {
                    "no_cyclic_imports._imports",
                    "no_cyclic_imports._normalization",
                    "no_cyclic_imports.tests.factories",
                    "parameterized",
                },
            },
        )

    def test_iterate_cycles(self):
        imports = ImportGraph()

        with TemporaryDirectory() as tempdir:
            init_py, a_py, b_py, package_name, package_a_name, package_b_name = (
                add_cyclic_import_to(tempdir)
            )
            imports.add_file(init_py, follow=False)
            imports.add_file(a_py, follow=False)
            imports.add_file(b_py, follow=False)

        expected_cycles = [[package_name, package_a_name, package_b_name]]
        actual_cycles = [
            shortest_first_rotated(cycle) for cycle in imports.iterate_cycles()
        ]

        self.assertEqual(actual_cycles, expected_cycles)
