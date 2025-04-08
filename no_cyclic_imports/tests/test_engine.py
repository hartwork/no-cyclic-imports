
from tempfile import TemporaryFile, TemporaryDirectory
from parameterized import parameterized
from textwrap import dedent
from io import StringIO
from .._engine import run
from .factories import initialize_packages

from unittest import TestCase, expectedFailure
from unittest.mock import patch

PACKAGES_WITH_RENAME_IN_INIT = {
    "my_package": [
        (
            "__init__.py",
            dedent("""\
                from . import _constants as constants
            """),
        ),
        (
            "_constants.py",
            dedent("""\
                C = 123
            """),

        ),
    ],
}

class EngineTest(TestCase):

    @expectedFailure
    def test_run_wrong_nr_of_cycles(
        self,
    ):
        with (
            TemporaryFile(mode="w+") as tempfile,
            TemporaryDirectory() as tempdir,
        ):
            initialize_packages(PACKAGES_WITH_RENAME_IN_INIT, dir=tempdir)
            cycles_count = run(
                abs_paths=[tempdir], follow=False, file_=tempfile,
            )
        self.assertEqual(cycles_count, 0)