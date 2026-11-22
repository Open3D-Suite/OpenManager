# SPDX-License-Identifier: GPL-3.0-or-later
"""Every place where OpenScene turns text into code, listed here: a new one makes this test fail until it is looked
at and added, with the reason it is safe. And the names a setup read from a file carries are checked before they
reach 3ds Max (maxlink.actions, with a small stand-in for pymxs)."""

import re
import subprocess
import sys
import types
import unittest
from pathlib import Path

REPO = Path(__file__).absolute().parent.parent

# What turns text into code: MAXScript's execute, fileIn and python.Execute, the render preset loader, Python's
# eval / exec and pymxs' rt.execute. Not a macro's `on execute do` handler, nor the exec() of a Qt dialog.
DOOR = re.compile(
    r"(?<![\w.])execute\s*[\(\"']|(?<![\w.])execute\s+(?!do\b)\w|python\.Execute|\bfileIn\b|renderPresets\.Load"
    r"|(?<![\w.])eval\(|(?<![\w.])exec\(|rt\.execute"
)

# file -> (how many doors, why each is safe)
KNOWN = {
    "bundle/openscene_bundle.ms": (2, "python.Execute of the bundle's own folder; fileIn of its own start-up script"),
    "package/OpenScene.mcr": (1, "python.Execute of the bundle's own folder (oscn_home), set by the bundle"),
    "package/OpenScene/openscene/maxlink.py": (1, "fileIn of openscene_core.ms, next to the package"),
    "package/OpenScene/openscene_core.ms": (
        4,
        "oscn_runCode, oscn_preRender / oscn_postRender (fileIn of the script files) and oscn_loadPreset: they run "
        "only what window.review() lets through, which a person wrote or chose on this computer, or said yes to",
    ),
}


def tracked(*suffixes):
    # S607: git from PATH, to list the files of this repository
    names = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout  # noqa: S607
    return [n for n in names.splitlines() if n.endswith(suffixes)]


def code_lines(path):
    """The lines of a source without its comments (MAXScript -- and Python #, outside strings well enough here)."""
    out = []
    for line in (REPO / path).read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if stripped.startswith(("--", "#")) or stripped.startswith('"') and stripped.endswith('"'):
            continue
        if path.endswith((".ms", ".mcr")):
            line = re.sub(r"--.*$", "", line)
        out.append(line)
    return out


class Doors(unittest.TestCase):
    def test_every_place_that_turns_text_into_code_is_known(self):
        found = {}
        for path in tracked(".py", ".ms", ".mcr"):
            if path.startswith(("tests/", "tools/")):
                continue
            hits = [line.strip() for line in code_lines(path) if DOOR.search(line)]
            if hits:
                found[path] = hits
        self.assertEqual(
            {p: len(h) for p, h in found.items()},
            {p: n for p, (n, _) in KNOWN.items()},
            "a place that turns text into code was added or removed:\n"
            + "\n".join("%s: %s" % (p, h) for p, hs in found.items() for h in hs),
        )

    def test_no_class_name_is_run_as_code(self):
        core = "\n".join(code_lines("package/OpenScene/openscene_core.ms"))
        self.assertEqual(re.findall(r"execute\s+(\w+)", core), ["code"])
        self.assertIn("fn oscn_classNamed", core)


class FakeRuntime(types.SimpleNamespace):
    def __getattr__(self, name):
        return None


def load_maxlink():
    """maxlink with a stand-in for pymxs: enough to build the list of changes of a setup."""
    fake = types.ModuleType("pymxs")
    fake.runtime = FakeRuntime()
    sys.modules.setdefault("pymxs", fake)
    from openscene import maxlink

    return maxlink


class FileNames(unittest.TestCase):
    def setUp(self):
        self.maxlink = load_maxlink()
        from openscene import model

        self.model = model

    def actions(self, s, rs_default=None):
        refused = []
        acts = self.maxlink.actions(
            s, self.maxlink.Scene(), lambda card: [], None, False, rs_default=rs_default, refused=refused
        )
        return acts, refused

    def test_render_override_names_that_are_paths_are_left_out_and_said(self):
        s = self.model.empty_setup(1)
        s["rs_override"] = {"enabled": True, "set": {"ok_pass": 5, "a.controller.script": "x", "obj": {"x": 1}}}
        acts, refused = self.actions(s)
        self.assertIn(("rs", "ok_pass", 5), acts)
        self.assertFalse([a for a in acts if a[0] == "rs" and a[1] != "ok_pass"])
        self.assertEqual(sorted(refused), ["Render Override: a.controller.script", "Render Override: obj"])

    def test_post_production_takes_only_its_own_settings(self):
        s = self.model.empty_setup(1)
        s["post"] = {"enabled": True, "cats": {"bloom": {"props": {"bloomGlare_enabled": True, "evil.path": 1}}}}
        acts, refused = self.actions(s)
        self.assertIn(("rs", "bloomGlare_enabled", True), acts)
        self.assertEqual(refused, ["Post-Production: evil.path"])

    def test_a_tone_mapping_operator_class_that_is_not_one_is_not_made(self):
        self.assertIsNone(self.maxlink.new_operator('Box()); deleteFile "x"; (Box'))
        self.assertIsNone(self.maxlink.new_operator("Teapot"))

    def test_scripts_of_a_setup_become_actions_that_review_can_take_out(self):
        s = self.model.empty_setup(1)
        s["snippet"].update(enabled=True, pre_setup="print 1", pre_render="print 2")
        acts, _ = self.actions(s)
        self.assertIn(("code", "print 1"), acts)
        self.assertIn(("renderscripts", "", "", "print 2", ""), acts)


if __name__ == "__main__":
    unittest.main()
