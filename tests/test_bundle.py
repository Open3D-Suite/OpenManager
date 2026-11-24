# SPDX-License-Identifier: GPL-3.0-or-later
"""The bundle 3ds Max loads, as tools/build.py makes it: what 3ds Max needs to load it, the version of the package,
and the codes 3ds Max knows OpenManager by."""

import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import openmanager

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
        self.assertEqual(self.package.get("Name"), openmanager.APP)
        for entry in self.package.iter("ComponentEntry"):
            self.assertEqual(entry.get("AppName"), openmanager.APP)

    def test_it_says_the_version_of_the_package(self):
        self.assertEqual(self.package.get("AppVersion"), openmanager.__version__)
        for entry in self.package.iter("ComponentEntry"):
            self.assertEqual(entry.get("Version"), openmanager.__version__)

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
        # the codes 3ds Max knows OpenManager by, since its 0.x versions: a new one would install it beside the old one
        self.assertEqual(codes["ProductCode"], "{6A36A415-E9A4-4DC7-9B99-1FF6EDB2C661}")
        self.assertEqual(codes["UpgradeCode"], "{757AF74F-AD01-4AEE-A3B6-43D92E4B9053}")

    def test_the_macro_icons_and_package_are_there(self):
        contents = self.bundle / "Contents"
        self.assertTrue((contents / "macroscripts" / "OpenManager.mcr").is_file())
        for theme in ("Dark", "Light"):
            self.assertTrue((contents / "icons" / theme / "OpenManager_24.png").is_file())
        self.assertTrue((contents / "OpenManager" / "openmanager" / "window.py").is_file())
        self.assertTrue((contents / "OpenManager" / "openmanager_core.ms").is_file())

    def test_a_path_with_an_apostrophe_starts_too(self):
        # the folder goes into a line of Python: between double quotes, which a Windows path cannot hold
        for part in ("scripts/openmanager_bundle.ms", "macroscripts/OpenManager.mcr"):
            script = (self.bundle / "Contents" / part).read_text(encoding="utf-8-sig")
            self.assertIn('d = r\\"" + oscn_bundleHome + "\\"', script)

    def test_no_compiled_python_goes_in(self):
        found = [p for p in self.bundle.rglob("*") if p.name == "__pycache__" or p.suffix in (".pyc", ".pyo")]
        self.assertEqual(found, [])

    def test_nothing_of_the_old_mzp_install_goes_in(self):
        names = {p.name for p in self.bundle.rglob("*")}
        self.assertFalse(names & {"install.ms", "mzp.run", "uninstall.ms"})

    def test_the_start_script_finds_the_package_next_to_it(self):
        # openmanager_bundle.ms points oscn_bundleHome at Contents/OpenManager, one folder up from scripts/
        script = (self.bundle / "Contents" / "scripts" / "openmanager_bundle.ms").read_text(encoding="utf-8-sig")
        self.assertIn('"..\\\\OpenManager"', script)
        self.assertTrue(os.path.isdir(self.bundle / "Contents" / "OpenManager"))

    def test_the_macro_reads_a_folder_an_openscene_bundle_never_sets(self):
        # an OpenScene.bundle still installed sets oscn_home in the session this bundle removes it: the macro must not
        # take that folder for this one's
        for part in ("scripts/openmanager_bundle.ms", "macroscripts/OpenManager.mcr"):
            text = (self.bundle / "Contents" / part).read_text(encoding="utf-8-sig")
            code = "\n".join(line.split("--")[0] for line in text.splitlines())
            self.assertIn("oscn_bundleHome", code)
            self.assertNotIn("oscn_home", code)

    def test_the_start_script_takes_away_the_file_open_check_of_0x(self):
        # a start-up script of OpenManager 0.x, left by its .mzp, adds one in the session its files are removed
        script = (self.bundle / "Contents" / "scripts" / "openmanager_bundle.ms").read_text(encoding="utf-8-sig")
        self.assertIn("callbacks.removeScripts id:#omgrStartup", script)


if __name__ == "__main__":
    unittest.main()
