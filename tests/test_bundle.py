# SPDX-License-Identifier: GPL-3.0-or-later
"""The bundle 3ds Max loads, as tools/build.py makes it: what 3ds Max needs to load it, the version of the package,
and the codes made once for OpenScene."""

import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import openscene

REPO = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import build  # noqa: E402 - tools/ is put on the path just above

GUID = re.compile(r"\{[0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12}\}", re.IGNORECASE)


class Bundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.bundle = Path(build.build_bundle(build.read_version(), dist=cls.scratch.name))
        # S314: the file read is the one build_bundle has just written, not data from outside
        cls.package = ElementTree.parse(cls.bundle / "PackageContents.xml").getroot()  # noqa: S314

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_it_is_this_app(self):
        self.assertEqual(self.package.get("Name"), openscene.APP)
        for entry in self.package.iter("ComponentEntry"):
            self.assertEqual(entry.get("AppName"), openscene.APP)

    def test_it_says_the_version_of_the_package(self):
        self.assertEqual(self.package.get("AppVersion"), openscene.__version__)
        for entry in self.package.iter("ComponentEntry"):
            self.assertEqual(entry.get("Version"), openscene.__version__)

    def test_every_3ds_max_from_2025_on_loads_it(self):
        # 3ds Max 2025 has Python 3.11, the oldest this code runs on; 3ds Max 2027 ignores a bundle without SeriesMax
        requirements = list(self.package.iter("RuntimeRequirements"))
        self.assertTrue(requirements)
        for requirement in requirements:
            self.assertEqual((requirement.get("SeriesMin"), requirement.get("SeriesMax")), ("2025", "2099"))

    def test_every_part_is_in_the_bundle(self):
        entries = list(self.package.iter("ComponentEntry"))
        self.assertEqual(len(entries), 4)
        for entry in entries:
            self.assertTrue((self.bundle / entry.get("ModuleName")).exists(), entry.get("ModuleName"))

    def test_its_codes_are_made_for_it_and_never_change(self):
        codes = {name: self.package.get(name) for name in ("ProductCode", "UpgradeCode")}
        for name, code in codes.items():
            self.assertTrue(GUID.fullmatch(code or ""), f"{name} is {code}, not a GUID in braces")
        self.assertNotEqual(codes["ProductCode"].upper(), codes["UpgradeCode"].upper())
        # the codes 3ds Max knows OpenScene by: a new one would install it beside the old one
        self.assertEqual(codes["UpgradeCode"], "{017FED04-B7BD-4640-80CE-06ECEE03FE5C}")

    def test_the_macro_icons_and_package_are_there(self):
        contents = self.bundle / "Contents"
        self.assertTrue((contents / "macroscripts" / "OpenScene.mcr").is_file())
        for theme in ("Dark", "Light"):
            self.assertTrue((contents / "icons" / theme / "OpenScene_24.png").is_file())
        self.assertTrue((contents / "OpenScene" / "openscene" / "window.py").is_file())
        self.assertTrue((contents / "OpenScene" / "openscene_core.ms").is_file())

    def test_no_compiled_python_goes_in(self):
        found = [p for p in self.bundle.rglob("*") if p.name == "__pycache__" or p.suffix in (".pyc", ".pyo")]
        self.assertEqual(found, [])

    def test_nothing_of_the_old_mzp_install_goes_in(self):
        names = {p.name for p in self.bundle.rglob("*")}
        self.assertFalse(names & {"install.ms", "mzp.run", "uninstall.ms"})

    def test_the_start_script_finds_the_package_next_to_it(self):
        # openscene_bundle.ms points oscn_home at Contents/OpenScene, one folder up from scripts/
        script = (self.bundle / "Contents" / "scripts" / "openscene_bundle.ms").read_text(encoding="utf-8-sig")
        self.assertIn('"..\\\\OpenScene"', script)
        self.assertTrue(os.path.isdir(self.bundle / "Contents" / "OpenScene"))


if __name__ == "__main__":
    unittest.main()
