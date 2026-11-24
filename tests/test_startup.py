# SPDX-License-Identifier: GPL-3.0-or-later
"""The first start: the toolbar added to the interface file, and the copy the old .mzp installer left."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree

from openmanager import startup, toolbar

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


if __name__ == "__main__":
    unittest.main()
