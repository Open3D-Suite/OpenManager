# SPDX-License-Identifier: GPL-3.0-or-later
"""Runs the tests that need neither 3ds Max nor Qt, with any Python from 3.11 on or with the one of 3ds Max:

python -I tests/run.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.dont_write_bytecode = True  # no __pycache__ beside the sources
# The package lives in package/OpenScene, which tools/build.py puts in the bundle as it is.
sys.path.insert(0, os.path.join(REPO, "package", "OpenScene"))
sys.path.insert(0, HERE)


def main():
    # No test reads or writes the person's real folders: every Open3D folder is a scratch one.
    with tempfile.TemporaryDirectory(prefix="openscene-tests-") as scratch:
        os.environ["OPEN3D_SETTINGS_DIR"] = os.path.join(scratch, "settings")
        os.environ["OPEN3D_DATA_DIR"] = os.path.join(scratch, "data")
        suite = unittest.defaultTestLoader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
