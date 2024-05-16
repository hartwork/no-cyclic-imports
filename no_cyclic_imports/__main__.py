# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under Affero GPL v3 or later

import argparse
import logging
import os
import sys

from ._engine import run
from .version import VERSION


def _main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(prog="no-cyclic-imports")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument(
        "--no-follow",
        dest="follow",
        default=True,
        action="store_false",
        help="do not follow discovered import statements"
        " (default: do follow discovered import statements)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="increase log level to INFO",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="increase log level to DEBUG",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="FILE|DIRECTORY",
        help="file(s) to analyze",
    )

    config = parser.parse_args(argv[1:])

    if not config.paths:
        config.paths = [os.getcwd()]

    config.paths = map(os.path.realpath, config.paths)

    if config.debug:
        log_level = logging.DEBUG
    elif config.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(
        level=log_level,
        format="no-cyclic-imports: [%(levelname)s] %(message)s",
        force=True,
    )

    cycles_count = run(config.paths, follow=bool(config.follow), file_=sys.stdout)

    exit_code = 1 if cycles_count else 0

    sys.exit(exit_code)


if __name__ == "__main__":
    _main(sys.argv)
