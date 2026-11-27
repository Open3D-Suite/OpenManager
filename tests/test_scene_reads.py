# SPDX-License-Identifier: GPL-3.0-or-later
"""The scene is never read on its own (a scene event, the mouse coming into the window, Camera Sync) while an object
is being created in a viewport: the object being drawn is half built and a right-click deletes it, and reading the
scene then stopped 3ds Max with an access violation."""

import ast
import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).absolute().parent.parent / "package" / "OpenManager"
WINDOW = PACKAGE / "openmanager" / "window.py"
MAXLINK = PACKAGE / "openmanager" / "maxlink.py"
CORE = PACKAGE / "openmanager_core.ms"


def methods(path, class_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {f.name: f for f in node.body if isinstance(f, ast.FunctionDef)}
    raise AssertionError("no class %s in %s" % (class_name, path.name))


def calls_busy(func):
    return any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "busy"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "maxlink"
        for n in ast.walk(func)
    )


class SceneReadsWaitForCreation(unittest.TestCase):
    def test_the_core_tells_when_an_object_is_being_created(self):
        text = CORE.read_text(encoding="utf-8-sig")
        match = re.search(r"^fn oscn_busy =\s*\((.*?)^\)", text, re.S | re.M)
        self.assertIsNotNone(match, "openmanager_core.ms has no oscn_busy")
        self.assertIn("isCreatingObject", match.group(1))

    def test_maxlink_asks_the_core(self):
        text = MAXLINK.read_text(encoding="utf-8")
        self.assertRegex(text, r"def busy\(\):(.|\n)*?rt\.oscn_busy\(\)")

    def test_the_scene_event_timer_waits(self):
        text = WINDOW.read_text(encoding="utf-8")
        self.assertIn("self.scene_timer = self._timer(350, self._scene_changed)", text)
        self.assertTrue(calls_busy(methods(WINDOW, "SceneManager")["_scene_changed"]))

    def test_reads_without_an_event_wait(self):
        found = methods(WINDOW, "SceneManager")
        for name in ("sync_scene", "_camera_sync_tick"):
            with self.subTest(name):
                self.assertTrue(calls_busy(found[name]), "%s reads the scene while an object is created" % name)


if __name__ == "__main__":
    unittest.main()
