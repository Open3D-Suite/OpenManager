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

import openmanager
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

    def openscene_toolbar(self):
        # what OpenScene's installer and its first start added, the same with its own name
        return toolbar.with_toolbar(CUIX).replace("OpenManager", "OpenScene")

    def test_the_toolbar_of_openscene_becomes_openmanagers_where_it_is(self):
        new = toolbar.with_old_buttons_moved(self.openscene_toolbar())
        root = ElementTree.fromstring(new)  # noqa: S314 - a text made by this test
        self.assertEqual([w.get("objectName") for w in root.iter("Window")], ["Main Toolbar", "OpenManager"])
        item = [i for i in root.iter("Item") if "OpenManager" in (i.get("actionID") or "")][0]
        self.assertEqual((item.get("tip"), item.get("label")), ("OpenManager", "OpenManager"))
        self.assertTrue(toolbar.has_button(new))
        self.assertNotIn("OpenScene", new)
        self.assertNotIn("\n", new.replace("\r\n", ""))  # its line ends stay CRLF
        self.assertEqual(new, toolbar.with_toolbar(CUIX))

    def test_a_button_of_openscene_on_a_toolbar_of_the_persons_own_runs_openmanager(self):
        old = CUIX.replace('actionID="Other`Other"', 'actionID="OpenScene`OpenScene" label="OpenScene"')
        new = toolbar.with_old_buttons_moved(old)
        self.assertIn('actionID="OpenManager`OpenManager" label="OpenManager"', new)
        self.assertIn('<Window objectName="Main Toolbar"', new)
        # and nothing else changes: a file without them stays as it is
        self.assertEqual(toolbar.with_old_buttons_moved(CUIX), CUIX)
        own = CUIX.replace('actionID="Other`Other"', 'actionID="Other`Other" label="OpenScene"')
        self.assertEqual(toolbar.with_old_buttons_moved(own), own)

    def test_with_an_openmanager_toolbar_already_the_one_of_openscene_keeps_its_name(self):
        both = toolbar.with_toolbar(self.openscene_toolbar())
        new = toolbar.with_old_buttons_moved(both)
        root = ElementTree.fromstring(new)  # noqa: S314 - a text made by this test
        names = [w.get("objectName") for w in root.iter("Window")]
        self.assertEqual(names, ["Main Toolbar", "OpenScene", "OpenManager"])
        self.assertNotIn("OpenScene`OpenScene", new)


class OldInstall(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = temporary.name
        self.dirs = [os.path.join(self.root, d) for d in ("scripts", "macros", "startup", "icons")]
        for d in self.dirs:
            os.makedirs(d)
        self.openscene, self.zero = startup.MZPS

    def touch(self, *parts, text="x"):
        path = os.path.join(*parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_only_the_files_of_the_mzp_of_openscene_are_found(self):
        scripts, macros, startup_dir, icons = self.dirs
        self.touch(scripts, "OpenScene", "openscene", "window.py")
        mcr = self.touch(macros, "OpenScene.mcr", text='macroScript OpenScene\n    category:"OpenScene"')
        ms = self.touch(startup_dir, "OpenScene_startup.ms", text="fn oscn_startupCheck = ()")
        icon = self.touch(icons, "Dark", "OpenScene_24.png")
        other = [
            self.touch(macros, "SomeoneElse.mcr"),
            self.touch(icons, "Dark", "Other_24.png"),
            self.touch(icons, "Dark", "OpenScene_logo.png"),
        ]
        found = startup.old_install(*self.dirs, self.openscene)
        self.assertEqual(found, [os.path.join(scripts, "OpenScene"), mcr, ms, icon])
        for path in other:
            self.assertNotIn(path, found)
        self.assertEqual(startup.old_install(*self.dirs, self.zero), [])

    def test_only_the_files_of_the_mzp_of_0x_are_found(self):
        scripts, macros, startup_dir, icons = self.dirs
        self.touch(scripts, "OpenManager", "openmanager", "window.py")
        self.touch(scripts, "OpenManager", "omgr_core.ms")
        mcr = self.touch(macros, "OpenManager.mcr", text="global omgr_home\nmacroScript OpenManager")
        ms = self.touch(startup_dir, "OpenManager_startup.ms", text="fn omgr_startupCheck = ()")
        icons_found = [
            self.touch(icons, theme, "OpenManager_%d.png" % s) for theme in ("Dark", "Light") for s in (16, 24)
        ]
        self.touch(icons, "Dark", "OpenManagerLogo.png")
        found = startup.old_install(*self.dirs, self.zero)
        self.assertEqual(sorted(found), sorted([os.path.join(scripts, "OpenManager"), mcr, ms] + icons_found))

    def test_files_with_the_old_names_that_are_not_the_old_ones_stay(self):
        scripts, macros, startup_dir, _ = self.dirs
        # a folder OpenManager in the scripts without 0.x's package, a macro or a start-up script of another tool
        self.touch(scripts, "OpenManager", "openmanager", "window.py")
        self.touch(scripts, "OpenScene", "notes.txt")
        self.touch(macros, "OpenManager.mcr", text="macroScript SomethingElse")
        self.touch(startup_dir, "OpenScene_startup.ms", text="print 1")
        for mzp in startup.MZPS:
            self.assertEqual(startup.old_install(*self.dirs, mzp), [], mzp.name)

    def test_the_bundle_of_openscene_is_found_only_when_it_is_openscenes(self):
        plugins = os.path.join(self.root, "ApplicationPlugins")
        contents = os.path.join(plugins, "OpenScene.bundle", "PackageContents.xml")
        self.assertEqual(startup.old_bundle(plugins), [])
        self.touch(
            contents, text='<ApplicationPackage Name="OpenScene" ProductCode="{1DE32304-98D8-46E2-B9E7-BBEDA0AE3FA9}">'
        )
        self.assertEqual(startup.old_bundle(plugins), [os.path.dirname(contents)])
        self.touch(
            contents, text='<ApplicationPackage Name="OpenScene" ProductCode="{00000000-0000-0000-0000-000000000000}">'
        )
        self.assertEqual(startup.old_bundle(plugins), [])

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
        self.assertTrue(printed[0].startswith(f"OpenManager {openmanager.__version__}: "), printed)
        self.assertIn(
            "OpenManager: settings of OpenScene 2.x: copied 1 files; the old ones are left as they were", printed
        )
        # the next start finds them carried over already
        self.assertNotIn("settings of", " ".join(self.run_start()))

    def test_the_first_start_removes_what_older_installs_left_and_nothing_else(self):
        bundle = self.old / "ApplicationPlugins" / "OpenScene.bundle"
        self.write(bundle / "PackageContents.xml", 'ProductCode="{1DE32304-98D8-46E2-B9E7-BBEDA0AE3FA9}"')
        self.write(bundle / "Contents" / "OpenScene" / "openscene" / "window.py")
        mine = self.write(self.old / "ApplicationPlugins" / "OpenManager.bundle" / "PackageContents.xml")
        self.write(self.old / "userScripts" / "OpenManager" / "openmanager" / "window.py")
        self.write(self.old / "userScripts" / "OpenManager" / "omgr_core.ms")
        self.write(self.old / "userMacros" / "OpenManager.mcr", "macroScript OpenManager")
        self.write(self.old / "userStartupScripts" / "OpenManager_startup.ms", "fn omgr_startupCheck = ()")
        self.write(self.old / "userMacros" / "OpenScene.mcr", "macroScript OpenScene")
        others = [self.write(self.old / "userMacros" / "Mine.mcr"), self.write(self.old / "userScripts" / "mine.ms")]
        printed = "\n".join(self.run_start())
        self.assertFalse(bundle.exists())
        self.assertEqual(sorted(p.name for p in (self.old / "userMacros").iterdir()), ["Mine.mcr"])
        self.assertEqual([p.name for p in (self.old / "userStartupScripts").iterdir()], [])
        self.assertEqual([p.name for p in (self.old / "userScripts").iterdir()], ["mine.ms"])
        for path in others + [mine]:
            self.assertTrue(path.is_file(), path)
        self.assertIn("removed what OpenScene.mzp installed in 3ds Max's user folders", printed)
        self.assertIn("removed what the OpenManager.mzp of 0.x installed in 3ds Max's user folders", printed)
        self.assertIn("removed OpenScene.bundle from", printed)


if __name__ == "__main__":
    unittest.main()
