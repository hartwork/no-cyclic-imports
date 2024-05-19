# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

import os
import sys
from io import StringIO
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import TestCase
from unittest.mock import patch

from parameterized import parameterized

from ..__main__ import _inner_main
from ..version import VERSION
from .factories import add_cyclic_import_to


class MainTest(TestCase):
    def _invoke(self, *argv_one_plus: list[str]) -> tuple[int, str, str]:
        with (
            patch("sys.stdout", new_callable=StringIO) as stdout,
            patch(
                "sys.stderr",
                new_callable=StringIO,
            ) as stderr,
            self.assertRaises(SystemExit) as catcher,
        ):
            _inner_main(["dummy", *argv_one_plus])

        exit_code = catcher.exception.code

        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_version(self):
        self.assertEqual(self._invoke("--version"), (0, f"{VERSION}\n", ""))

    def test_help(self):
        exit_code, stdout, stderr = self._invoke("--help")

        self.assertEqual(exit_code, 0)
        self.assertIn("usage: no-cyclic-imports", stdout)
        self.assertEqual(stderr, "")

    def test_empty_directory__explicit(self):
        with TemporaryDirectory() as tempdir:
            self.assertEqual(self._invoke(tempdir), (0, "0 cycle(s).\n", ""))

    def test_empty_directory__implicit(self):
        oldpwd = os.getcwd()
        with TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                self.assertEqual(self._invoke(), (0, "0 cycle(s).\n", ""))
            finally:
                os.chdir(oldpwd)

    @parameterized.expand(
        [
            ("warning", [], False, False),
            ("info", ["--verbose"], True, False),
            ("debug", ["--debug"], True, True),
        ],
    )
    def test_single_cycle_and_log_level(
        self,
        _log_level,
        extra_argv,
        expecting_info_lines,
        expecting_debug_lines,
    ):
        with TemporaryDirectory() as tempdir:
            _, a_py, b_py, package_name, package_a_name, package_b_name = (
                add_cyclic_import_to(tempdir)
            )
            exit_code, stdout, stderr = self._invoke(
                "--no-follow",
                *(*extra_argv, tempdir),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            dedent(f"""\
                {package_name} -> {package_a_name} -> {package_b_name} -> {package_name}

                1 cycle(s).
            """),
            stdout,
        )

        self.assertEqual("no-cyclic-imports: [INFO] " in stderr, expecting_info_lines)
        self.assertEqual("no-cyclic-imports: [DEBUG] " in stderr, expecting_debug_lines)

    @parameterized.expand(
        [
            ("follow", [], True),
            ("no-follow", ["--no-follow"], False),
        ],
    )
    def test_single_file(self, _label, extra_argv, expecting_follow):
        with TemporaryDirectory() as tempdir:
            _, a_py, _, package_name, package_a_name, package_b_name = (
                add_cyclic_import_to(tempdir)
            )
            with patch("sys.path", [*sys.path, tempdir]):
                exit_code, stdout, stderr = self._invoke(
                    "--verbose",
                    *(*extra_argv, a_py),
                )

        if expecting_follow:
            self.assertEqual(exit_code, 2)
            self.assertEqual(
                dedent(f"""\
                    {package_name} -> {package_a_name} -> {package_b_name} -> {package_name}

                    1 cycle(s).
                """),  # noqa: E501
                stdout,
            )
        else:
            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout, "0 cycle(s).\n")

        self.assertEqual("/coverage/" in stderr, expecting_follow)
