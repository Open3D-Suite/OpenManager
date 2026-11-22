# SPDX-License-Identifier: GPL-3.0-or-later
"""A small stand-in for what exists only inside 3ds Max (pymxs, qtmax), so that the modules that use it load in a
test. Every test that needs it calls install(); the first call puts it in place for all of them."""

import contextlib
import sys
import types


class Runtime(types.SimpleNamespace):
    """pymxs.runtime: any MAXScript name is there and gives nothing."""

    def __getattr__(self, name):
        return None


def install():
    if "pymxs" not in sys.modules:
        pymxs = types.ModuleType("pymxs")
        pymxs.runtime = Runtime()
        pymxs.undo = lambda *a, **k: contextlib.nullcontext()
        sys.modules["pymxs"] = pymxs
    sys.modules.setdefault("qtmax", types.ModuleType("qtmax"))
    return sys.modules["pymxs"]
