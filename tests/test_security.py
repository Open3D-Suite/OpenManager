# SPDX-License-Identifier: GPL-3.0-or-later
"""Every place where OpenManager turns text into code, listed here: a new one makes this test fail until it is looked
at and added, with the reason it is safe. And the names a setup read from a file carries are checked before they
reach 3ds Max (maxlink.actions, with a small stand-in for pymxs)."""

import json
import re
import subprocess
import unittest
from pathlib import Path
from unittest import mock

import stand_in  # noqa: E402 - tests/ is on the path (tests/run.py)

REPO = Path(__file__).absolute().parent.parent

# What turns text into code: MAXScript's execute, fileIn and python.Execute, the render preset loader, Python's
# eval / exec and pymxs' rt.execute. Not a macro's `on execute do` handler, nor the exec() of a Qt dialog.
DOOR = re.compile(
    r"(?<![\w.])execute\s*[\(\"']|(?<![\w.])execute\s+(?!do\b)\w|python\.Execute|\bfileIn\b|renderPresets\.Load"
    r"|(?<![\w.])eval\(|(?<![\w.])exec\(|rt\.execute"
)

# file -> (how many doors, why each is safe)
KNOWN = {
    "bundle/openmanager_bundle.ms": (2, "python.Execute of the bundle's own folder; fileIn of its own start-up script"),
    "package/OpenManager.mcr": (1, "python.Execute of the bundle's own folder (oscn_home), set by the bundle"),
    "package/OpenManager/openmanager/maxlink.py": (1, "fileIn of openmanager_core.ms, next to the package"),
    "package/OpenManager/openmanager_core.ms": (
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
        core = "\n".join(code_lines("package/OpenManager/openmanager_core.ms"))
        self.assertEqual(re.findall(r"execute\s+(\w+)", core), ["code"])
        self.assertIn("fn oscn_classNamed", core)


def load_maxlink():
    """maxlink with a stand-in for pymxs: enough to build the list of changes of a setup."""
    stand_in.install()
    from openmanager import maxlink

    return maxlink


class FileNames(unittest.TestCase):
    def setUp(self):
        self.maxlink = load_maxlink()
        from openmanager import model

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

    def test_a_tone_mapping_operator_is_made(self):
        # 3ds Max says an operator's class is a MAXClass of the kind ReferenceTarget
        class Max:
            MAXClass = object()

            def isKindOf(self, c, kind):
                return kind is self.MAXClass and callable(c)

            def classOf(self, c):
                return "ReferenceTarget" if c is self.FilmicOperatorPlugin else "GeometryClass"

            def FilmicOperatorPlugin(self):
                return "an operator"

            def BoxOperatorPlugin(self):
                return "a box"

        fake = Max()
        fake.FilmicOperatorPlugin = fake.FilmicOperatorPlugin
        with mock.patch.object(self.maxlink, "rt", fake):
            self.assertEqual(self.maxlink.new_operator("FilmicOperatorPlugin"), "an operator")
            self.assertIsNone(self.maxlink.new_operator("BoxOperatorPlugin"))
            self.assertIsNone(self.maxlink.new_operator("MissingOperatorPlugin"))

    def test_a_tone_mapping_operator_class_that_is_not_one_is_not_made(self):
        self.assertIsNone(self.maxlink.new_operator('Box()); deleteFile "x"; (Box'))
        self.assertIsNone(self.maxlink.new_operator("Teapot"))

    def test_a_variant_decides_whether_its_layers_are_on(self):
        # the window sends only the changes that are new: an edit of the Layers card alone must not win over a variant
        s = self.model.empty_setup(1)
        s["layers"] = {"enabled": True, "set": [self.model.layer_entry("Sofa_A"), self.model.layer_entry("Walls")]}
        s["variants"] = {"enabled": True, "set": [{"name": "Sofa", "value": 2, "layers": ["Sofa_A", "Sofa_B"]}]}
        on_row = [({"v_class": "Layer"}, {"name": "on", "class": "BooleanClass"})]
        acts = self.maxlink.actions(s, self.maxlink.Scene(), lambda card: on_row if card == 14 else [], None, False)
        sets = [a for a in acts if a[0] == "layer" and a[2] == "on"]
        self.assertEqual(
            sets, [("layer", "Walls", "on", True), ("layer", "Sofa_A", "on", False), ("layer", "Sofa_B", "on", True)]
        )

    def test_rows_of_a_file_that_are_not_rows_never_break_a_setup(self):
        # as read from a file: through model.decode, which keeps only rows of the right shape
        stored = {
            "id": 1,
            "variants": {"enabled": True, "set": [{"layers": [{"x": 1}, "A"]}, "junk"]},
            "layers": {"enabled": True, "set": [5, {"name": "Walls"}, {"visible": True}]},
            "objects": {"enabled": True, "set": [{"handle": "x"}, {"handle": 7}]},
            "lights": {"enabled": True, "set": [3, "x", True]},
        }
        s = self.model.decode(json.dumps({"version": 1, "setups": [stored]}))["setups"][0]
        self.assertEqual([x["name"] for x in s["layers"]["set"]], ["Walls"])
        self.assertEqual([x["handle"] for x in s["objects"]["set"]], [7])
        self.assertEqual(s["lights"]["set"], [3])
        acts = self.maxlink.actions(s, self.maxlink.Scene(), lambda card: [], None, False)
        self.assertIn(("layer", "A", "on", False), acts)  # the variant picks its first entry, which is not a name

    def test_a_render_preset_never_changes_the_scripts_of_render_setup(self):
        # a .rps file keeps Render Setup's pre- and post-render scripts too: loading one must not set them
        maxlink = self.maxlink

        class Max:
            scripts = [False, "", False, ""]

            def oscn_renderSetupScripts(self):
                return list(self.scripts)

            def oscn_setRenderSetupScripts(self, v):
                self.scripts = list(v)

            def oscn_loadPreset(self, path):
                self.scripts = [True, "D:/someone/else.ms", True, "D:/someone/after.ms"]
                return True

        fake = Max()
        with mock.patch.object(maxlink, "rt", fake):
            self.assertTrue(maxlink.load_preset("D:/look.rps"))
        self.assertEqual(fake.scripts, [False, "", False, ""])

    def test_render_setup_scripts_are_put_back_when_the_load_fails(self):
        maxlink = self.maxlink

        class Max:
            scripts = [True, "D:/mine.ms", False, ""]

            def oscn_renderSetupScripts(self):
                return list(self.scripts)

            def oscn_setRenderSetupScripts(self, v):
                self.scripts = list(v)

            def oscn_loadPreset(self, path):
                self.scripts = [False, "", True, "D:/other.ms"]
                raise RuntimeError("MAXScript exception")

        fake = Max()
        with mock.patch.object(maxlink, "rt", fake), self.assertRaises(RuntimeError):
            maxlink.load_preset("D:/look.rps")
        self.assertEqual(fake.scripts, [True, "D:/mine.ms", False, ""])

    def test_scripts_of_a_setup_become_actions_that_review_can_take_out(self):
        s = self.model.empty_setup(1)
        s["snippet"].update(enabled=True, pre_setup="print 1", pre_render="print 2")
        acts, _ = self.actions(s)
        self.assertIn(("code", "print 1"), acts)
        self.assertIn(("renderscripts", "", "", "print 2", ""), acts)


if __name__ == "__main__":
    unittest.main()
