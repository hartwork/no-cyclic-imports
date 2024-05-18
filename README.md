# no-cyclic-imports

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Run the test suite](https://github.com/hartwork/no-cyclic-imports/actions/workflows/run-tests.yml/badge.svg)](https://github.com/hartwork/no-cyclic-imports/actions/workflows/run-tests.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/no-cyclic-imports.svg)](https://pypi.org/project/no-cyclic-imports)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/no-cyclic-imports.svg)](https://pypi.org/project/no-cyclic-imports)

**Tool to detect and report on cyclic imports in a Python codebase**

```console
$ no-cyclic-imports --no-follow cyclic/
package123 -> package123.a -> package123.b -> package123

1 cycle(s).
```

-----

## Table of Contents

- [Installation](#installation)
- [License](#license)


## Installation

```console
$ pip3 install no-cyclic-imports
```

```console
$ pipx install no-cyclic-imports
```


## License

`no-cyclic-imports` is distributed under the terms of the [Affero GPL v3 or later](https://spdx.org/licenses/AGPL-3.0-or-later.html) license.
