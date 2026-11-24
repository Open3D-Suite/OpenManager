# SPDX-License-Identifier: GPL-3.0-or-later
"""The first start: the toolbar added to the interface file, the copy the old .mzp installer left, and the
whole start-up in a stand-in 3ds Max, on the fake old folders of startup.TEST_OLD_FOLDERS."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from unittest import mock

import stand_in  # noqa: E402 - tests/ is on the path (tests/run.py)

from openmanager import folders, startup, toolbar

# a made-up interface file, shaped like the ones 3ds Max writes (CRLF, windows inside CUIWindows)
CUIX = (
    '<?xml version="1.0" encoding="utf-8"?>\r\n'
    "<CUIData>\r\n"
    "    <CUIWindows>\r\n"
    '        <Window objectName="Main Toolbar" name="Main Toolbar" type="T" cType="1" toolbarRows="1">\r\n'
    "            <Items>\r\n"
    '                <Item typeID="2" type="CTB_MACROBUTTON" actionID="Other`Other" />\r\n'
    "            </Items>\r\n"
    "        </Window>\r\n"
    "    </CUIWindows>\r\n"
    "</CUIData>\r\n"
)


class Toolbar(unittest.TestCase):
    def test_the_toolbar_is_added_with_the_button_and_the_file_stays_valid(self):
        new = toolbar.with_toolbar(CUIX)
        root = ElementTree.fromstring(new)  # noqa: S314 - a text made by this test
        names = [w.get("objectName") for w in root.iter("Window")]
        self.assertEqual(names, ["Main Toolbar", "OpenManager"])
        self.assertTrue(toolbar.has_button(new))
        self.assertNotIn("\n", new.replace("\r\n", ""))  # its line ends stay CRLF

    def test_removing_it_gives_the_file_back_as_it_was(self):
        self.assertEqual(toolbar.without_toolbar(toolbar.with_toolbar(CUIX)), CUIX)
        self.assertEqual(toolbar.without_toolbar(CUIX), CUIX)

    def test_a_button_the_person_placed_already_is_seen(self):
        self.assertFalse(toolbar.has_button(CUIX))
        self.assertTrue(toolbar.has_button(CUIX.replace("Other`Other", "OpenManager`OpenManager")))

    def test_a_file_without_a_list_of_windows_is_not_changed(self):
        self.assertIsNone(toolbar.with_toolbar("<CUIData></CUIData>"))


class OldInstall(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = temporary.name
        self.dirs = [os.path.join(root, d) for d in ("scripts", "macros", "startup", "icons")]
        for d in self.dirs:
            os.makedirs(d)

    def touch(self, *parts):
        path = os.path.join(*parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("x")
        return path

    def test_only_the_files_of_the_old_install_are_found(self):
        scripts, macros, startup_dir, icons = self.dirs
        self.touch(scripts, "OpenScene", "openscene", "window.py")
        mcr = self.touch(macros, "OpenScene.mcr")
        icon = self.touch(icons, "Dark", "OpenScene_24.png")
        other = [self.touch(macros, "SomeoneElse.mcr"), self.touch(icons, "Dark", "Other_24.png")]
        found = startup.old_install(*self.dirs)
        self.assertEqual(found, [os.path.join(scripts, "OpenScene"), mcr, icon])
        for path in other:
            self.assertNotIn(path, found)

    def test_a_scripts_folder_named_openscene_that_is_not_ours_stays(self):
        scripts = self.dirs[0]
        self.touch(scripts, "OpenScene", "notes.txt")
        self.assertEqual(startup.old_install(*self.dirs), [])

    def test_remove_takes_the_files_and_says_what_it_could_not(self):
        scripts = self.dirs[0]
        path = self.touch(scripts, "OpenScene", "openscene", "window.py")
        folder = os.path.dirname(os.path.dirname(path))
        self.assertEqual(startup.remove([folder]), [])
        self.assertFalse(os.path.exists(folder))
        self.assertEqual(len(startup.remove([os.path.join(scripts, "gone.txt")])), 1)


class StartUp(unittest.TestCase):
    def setUp(self):
        stand_in.install()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.old = self.root / "old"
        variables = {
            "OPEN3D_SETTINGS_DIR": str(self.root / "settings"),
            "OPEN3D_DATA_DIR": str(self.root / "data"),
            startup.TEST_OLD_FOLDERS: str(self.old),
        }
        patcher = mock.patch.dict(os.environ, variables)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(folders.use, folders.Carried())

    def write(self, path, text="x"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_start(self):
        with mock.patch("builtins.print") as said:
            startup.run()
        return [c.args[0] for c in said.call_args_list]

    def test_with_the_test_variable_only_its_folders_are_looked_at(self):
        places = startup.old_places(None)
        self.assertEqual(set(places), set(startup.OLD_PLACES))
        for name, folder in places.items():
            self.assertEqual(Path(folder), self.old / name)

    def test_the_first_start_carries_the_settings_over_and_says_so(self):
        self.write(self.old / "plugcfg" / "OpenScene.json", '{"theme": {"main": "dark"}}')
        printed = self.run_start()
        new = self.root / "settings" / "OpenManager"
        self.assertEqual((new / "settings.json").read_text(encoding="utf-8"), '{"theme": {"main": "dark"}}')
        self.assertTrue(printed[0].startswith("OpenManager 3.0.0: "), printed)
        self.assertIn(
            "OpenManager: settings of OpenScene 2.x: copied 1 files; the old ones are left as they were", printed
        )
        # the next start finds them carried over already
        self.assertNotIn("settings of", " ".join(self.run_start()))


if __name__ == "__main__":
    unittest.main()
