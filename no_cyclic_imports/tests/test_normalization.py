# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

from unittest import TestCase

from parameterized import parameterized

from .._normalization import shortest_first_rotated


class RotationTest(TestCase):
    @parameterized.expand(
        [
            ("empty list intact", [], []),
            ("single value intact", ["single"], ["single"]),
            (
                "single shortest moved upfront length gt 2",
                ["xxxx", "x", "xx", "xxx"],
                ["x", "xx", "xxx", "xxxx"],
            ),
            (
                "single shortest moved upfront length eq 2",
                ["longest", "other"],
                ["other", "longest"],
            ),
            (
                "shortest and alphabetical moved upfront",
                ["xxxx", "2", "1", "3", "xxx"],
                ["1", "3", "xxx", "xxxx", "2"],
            ),
            ("identity length eq 2", ["other", "longest"], ["other", "longest"]),
        ],
    )
    def test(self, _label, names, expected_names):
        actual_names = shortest_first_rotated(names)
        self.assertEqual(actual_names, expected_names)
