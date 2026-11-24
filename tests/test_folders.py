# SPDX-License-Identifier: GPL-3.0-or-later
"""Where OpenManager keeps its files, and the files of the versions before it carried over once: OpenScene 3 (its
folders), OpenScene 2.x (plugcfg) and OpenManager 0.x (its files in the same folders, converted). Every folder is a
temporary one, named by the variables every Open3D app reads."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openmanager import folders, open3d_settings, trust, version0

# settings of OpenManager 0.x, as its window wrote them (OpenManager.json)
ZERO_SETTINGS = {
    "notify": False,
    "theme": {"main": "dark", "header": "default"},
    "max": {
        "viewport_update_type": 1,
        "viewport_refresh": False,
        "ipr_corona_restart": True,
        "ipr_vray_resolution": True,
        "update_time_output_type": False,
        "animate_camera": False,
        "restore_base": True,
        "scripts": "always",
    },
    "columns_visible": {"name": True, "camera": False, "id": True},
    "column_widths": {"name": 120, "camera": 90},
    "resolution_presets": [[1920, 1080], [3000, 2000]],
    "geometry": [100, 80, 900, 1000],
    "floating": True,
    "visible": [0, 1, 2, 6, 9],
    "layouts": {"12": {"1": [3, 40, 3, 14]}},
    "enabled_props": {"25": ["CoronaRenderer|progressive_passLimit"]},
    "hdri_folders": ["D:/HDRI/Studio"],
    "hdri_selected": 0,
}


class Folders(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.settings = self.root / "settings"
        self.data = self.root / "data"
        self.new = self.settings / "OpenManager"
        self.new_data = self.data / "OpenManager"
        self.plugcfg = self.root / "plugcfg"
        self.plugcfg.mkdir()
        variables = {"OPEN3D_SETTINGS_DIR": str(self.settings), "OPEN3D_DATA_DIR": str(self.data)}
        patcher = mock.patch.dict(os.environ, variables)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(folders.use, folders.Carried())

    def write(self, path, text, changed=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if changed is not None:
            os.utime(path, (changed, changed))
        return path

    def carry(self):
        return folders.carry_over(str(self.plugcfg))

    def test_the_folders_are_named_after_the_app(self):
        self.assertEqual(folders.settings_dir(), self.settings / "OpenManager")
        self.assertEqual(folders.data_dir(), self.data / "OpenManager")
        self.assertEqual(folders.settings_file(folders.SETTINGS), str(self.new / "settings.json"))

    def test_without_any_variable_there_is_no_folder(self):
        with mock.patch.dict(os.environ, clear=True):
            self.assertIsNone(folders.settings_dir())
            self.assertIsNone(folders.settings_file(folders.SETTINGS))
            self.assertIsNone(folders.data_path(folders.HDRI_PREVIEWS))
            self.assertTrue(folders.carry_over().finished)

    def test_asking_for_a_folder_creates_nothing(self):
        folders.settings_file(folders.SETTINGS)
        folders.data_path(folders.HDRI_PREVIEWS)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["plugcfg"])

    def test_write_text_creates_the_folder_and_leaves_no_temporary_file(self):
        target = self.new / "settings.json"
        folders.write_json(str(target), {"a": 1})
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"a": 1})
        self.assertEqual([p.name for p in target.parent.iterdir()], ["settings.json"])

    def test_this_versions_names_are_not_those_of_0x(self):
        # the settings folder is the one 0.x used: no file of one is ever read as a file of the other
        self.assertFalse(set(folders.SETTINGS_FILES) & set(folders.ZERO_FILES))
        self.assertNotEqual(folders.HDRI_PREVIEWS, version0.HDRI)

    # ------------------------------------------------------------ OpenScene 2.x, in plugcfg

    def test_the_settings_of_openscene_2x_are_carried_over_once_under_their_new_names(self):
        self.write(self.plugcfg / "OpenScene.json", '{"theme": {}}')
        self.write(self.plugcfg / "OpenScene_default.json", '{"visible": [1]}')
        self.write(self.plugcfg / "OpenScene_notify.txt", "0")
        carried = self.carry()
        self.assertEqual([(w, n, r.kind) for w, n, r in carried.done], [("settings", "OpenScene 2.x", "copied")])
        self.assertEqual((self.new / "settings.json").read_text(encoding="utf-8"), '{"theme": {}}')
        self.assertEqual((self.new / "notify.txt").read_text(encoding="utf-8"), "0")
        self.assertTrue(carried.finished)
        # the old files stay as they were
        self.assertTrue((self.plugcfg / "OpenScene.json").is_file())
        # and the next start copies nothing over what this version wrote, nor what it took away
        self.write(self.new / "settings.json", "{}")
        (self.new / "default_layout.json").unlink()
        self.assertEqual(self.carry().done, ())
        self.assertEqual((self.new / "settings.json").read_text(encoding="utf-8"), "{}")
        self.assertFalse((self.new / "default_layout.json").exists())

    def test_without_old_files_only_the_note_of_the_first_start_is_written(self):
        carried = self.carry()
        self.assertEqual((carried.done, carried.notes), ((), ()))
        self.assertEqual([p.name for p in self.new.iterdir()], [folders.CARRIED])
        self.assertFalse(self.data.exists())

    def test_the_hdri_previews_of_2x_go_to_the_data_folder(self):
        old = self.plugcfg / "OpenScene_hdri"
        self.write(old / "a_0123456789.jpg", "jpg")
        carried = self.carry()
        self.assertEqual([what for what, _, _ in carried.done], ["HDRI previews"])
        self.assertTrue((self.new_data / "hdri_previews" / "a_0123456789.jpg").is_file())
        self.assertTrue((old / "a_0123456789.jpg").is_file())

    # ------------------------------------------------------------ OpenScene 3, in its own folders

    def test_the_folders_of_openscene_are_carried_over_but_its_toolbar(self):
        old, old_data = self.settings / "OpenScene", self.data / "OpenScene"
        self.write(old / "settings.json", '{"trusted_code": ["abc"]}')
        self.write(old / "default_layout.json", "{}")
        self.write(old / "notify.txt", "1")
        self.write(old / "toolbar_placed.txt", "1\n")
        self.write(old_data / "hdri_previews" / "sky_0123456789.jpg", "jpg")
        self.write(old_data / "unsaved_scene" / "OpenManager_export" / "a.max", "max")
        self.write(old_data / "interface_backup" / "Default.cuix", "<CUIData/>")
        carried = self.carry()
        self.assertEqual(
            [(w, n) for w, n, _ in carried.done],
            [("settings", "OpenScene"), ("HDRI previews", "OpenScene"), ("files of scenes not saved yet", "OpenScene")],
        )
        self.assertEqual((self.new / "settings.json").read_text(encoding="utf-8"), '{"trusted_code": ["abc"]}')
        self.assertEqual(
            sorted(p.name for p in self.new.iterdir()), sorted(folders.SETTINGS_FILES + (folders.CARRIED,))
        )
        # the OpenManager toolbar is placed anew: it is not OpenScene's
        self.assertFalse((self.new / "toolbar_placed.txt").exists())
        self.assertFalse((self.new_data / "interface_backup").exists())
        self.assertTrue((self.new_data / "unsaved_scene" / "OpenManager_export" / "a.max").is_file())
        self.assertTrue((old / "toolbar_placed.txt").is_file())

    # ------------------------------------------------------------ OpenManager 0.x, in the same folders

    def zero(self, settings=None, changed=None):
        script = self.write(self.root / "scripts" / "before.ms", "print 1")
        data = dict(ZERO_SETTINGS, **(settings or {}))
        data["trusted_scripts"] = [
            trust.old_code_key('print "kitchen"'),
            "file:" + os.path.normcase(os.path.normpath(str(script))),
            "preset:" + os.path.normcase(os.path.normpath(str(self.root / "gone.rps"))),
        ]
        self.write(self.new / "OpenManager.json", json.dumps(data, indent=1), changed)
        self.write(self.new / "OpenManager_default.json", json.dumps({"theme": {"main": "light"}}), changed)
        self.write(self.new / "OpenManager_notify.txt", "0", changed)
        self.write(self.new_data / "OpenManager_hdri" / "sky_0123456789.jpg", "jpg")
        return script

    def test_the_settings_of_0x_are_converted_and_its_files_left_as_they_were(self):
        script = self.zero()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.new.iterdir()}
        carried = self.carry()
        self.assertEqual(
            [(w, n) for w, n, _ in carried.done],
            [("settings", "OpenManager 0.x"), ("HDRI previews", "OpenManager 0.x")],
        )
        st = json.loads((self.new / "settings.json").read_text(encoding="utf-8"))
        for key in ("notify", "columns_visible", "column_widths", "resolution_presets", "geometry", "floating"):
            self.assertEqual(st[key], ZERO_SETTINGS[key], key)
        for key in ("visible", "layouts", "enabled_props", "hdri_folders", "hdri_selected"):
            self.assertEqual(st[key], ZERO_SETTINGS[key], key)
        self.assertEqual(st["theme"], {"main": "dark", "header": "default"})
        self.assertNotIn("restore_base", st["max"])
        self.assertNotIn("scripts", st["max"])
        self.assertEqual(st["max"]["viewport_update_type"], 1)
        self.assertNotIn("trusted_scripts", st)
        # a script file 0.x trusted by its path is trusted by its path and contents; a script by the digest 0.x kept
        self.assertEqual(st["trusted_code"], [trust.file_digest(str(script))])
        self.assertEqual(st[version0.TRUSTED_CODE], [trust.old_code_key('print "kitchen"')])
        self.assertEqual(
            json.loads((self.new / "default_layout.json").read_text(encoding="utf-8")), {"theme": {"main": "light"}}
        )
        self.assertEqual((self.new / "notify.txt").read_bytes(), b"0")
        self.assertTrue((self.new_data / "hdri_previews" / "sky_0123456789.jpg").is_file())
        # what has no counterpart is said
        notes = " | ".join(carried.notes)
        self.assertIn("put the scene back between setups", notes)
        self.assertIn('"Always run them"', notes)
        self.assertIn("1 trusted script file(s) or render preset(s) that cannot be read now", notes)
        # and the files of 0.x are as they were
        for name, (data, changed) in before.items():
            self.assertEqual(((self.new / name).read_bytes(), (self.new / name).stat().st_mtime_ns), (data, changed))

    def test_a_file_that_is_there_is_never_copied_over(self):
        self.zero()
        self.write(self.new / "settings.json", '{"mine": true}')
        carried = self.carry()
        self.assertEqual(carried.done[0][2].files, 2)
        self.assertEqual((self.new / "settings.json").read_text(encoding="utf-8"), '{"mine": true}')
        self.assertTrue((self.new / "default_layout.json").is_file())

    def test_the_settings_changed_last_are_taken(self):
        self.write(self.settings / "OpenScene" / "settings.json", '{"from": "OpenScene"}', changed=1_700_000_000)
        self.zero(changed=1_800_000_000)
        carried = self.carry()
        self.assertEqual(carried.done[0][:2], ("settings", "OpenManager 0.x"))
        self.assertIn("the settings of OpenScene: those of OpenManager 0.x, changed last, were taken", carried.notes)

    def test_openscene_wins_when_its_settings_were_changed_last(self):
        self.zero(changed=1_700_000_000)
        self.write(self.settings / "OpenScene" / "settings.json", '{"from": "OpenScene"}', changed=1_800_000_000)
        carried = self.carry()
        self.assertEqual(carried.done[0][:2], ("settings", "OpenScene"))
        self.assertEqual(json.loads((self.new / "settings.json").read_text(encoding="utf-8")), {"from": "OpenScene"})
        # the HDRI previews of 0.x still come, as OpenScene has none
        self.assertTrue((self.new_data / "hdri_previews" / "sky_0123456789.jpg").is_file())

    def test_settings_of_0x_that_are_not_settings_are_left_out_and_said(self):
        self.write(self.new / "OpenManager.json", "not json")
        carried = self.carry()
        self.assertEqual(carried.done[0][2].files, 0)
        self.assertIn("OpenManager.json", folders.describe(carried.done[0][2]))
        self.assertFalse((self.new / "settings.json").exists())

    # ------------------------------------------------------------ when a copy fails

    def test_a_failed_copy_leaves_the_session_on_the_old_files_and_the_next_start_tries_again(self):
        old = self.write(self.settings / "OpenScene" / "settings.json", '{"from": "OpenScene"}')
        self.write(self.data / "OpenScene" / "hdri_previews" / "sky_0123456789.jpg", "jpg")
        # what stands where the new folders go cannot be written into
        self.settings.mkdir(exist_ok=True)
        self.new.write_text("in the way", encoding="utf-8")
        self.data.mkdir(exist_ok=True)
        self.new_data.write_text("in the way", encoding="utf-8")
        carried = self.carry()
        self.addCleanup(shutil.rmtree, carried.in_use["settings"], True)
        self.assertFalse(carried.finished)
        self.assertEqual([r.kind for _, _, r in carried.done], ["failed", "failed"])
        folders.use(carried)
        self.assertEqual(
            json.loads(Path(folders.settings_file(folders.SETTINGS)).read_text(encoding="utf-8")), {"from": "OpenScene"}
        )
        self.assertEqual(folders.data_path(folders.HDRI_PREVIEWS), str(self.data / "OpenScene" / "hdri_previews"))
        self.assertIn("this session uses the old ones, and the next start tries again", folders.report(carried)[0])
        self.assertEqual(old.read_text(encoding="utf-8"), '{"from": "OpenScene"}')
        # the next start, with the way clear, copies them
        folders.use(folders.Carried())
        self.new.unlink()
        self.new_data.unlink()
        carried = self.carry()
        self.assertTrue(carried.finished)
        self.assertEqual(json.loads((self.new / "settings.json").read_text(encoding="utf-8")), {"from": "OpenScene"})
        self.assertTrue((self.new_data / "hdri_previews" / "sky_0123456789.jpg").is_file())

    def test_report_and_describe_say_what_was_done(self):
        self.write(self.plugcfg / "OpenScene.json", "{}")
        lines = folders.report(self.carry())
        self.assertEqual(lines, ["settings of OpenScene 2.x: copied 1 files; the old ones are left as they were"])
        r = open3d_settings.CarryOver(open3d_settings.COPIED, files=2, left_out=(("x.json", "in use"),))
        self.assertEqual(folders.describe(r), "copied 2 files, left out: x.json (in use)")


class ZeroSettings(unittest.TestCase):
    def test_only_what_has_the_right_kind_is_taken(self):
        out, notes = version0.settings(
            {
                "geometry": [1, 2, 3],
                "visible": [1, 99, "x"],
                "theme": {"main": "pink", "header": "colored"},
                "max": {"viewport_refresh": "yes", "scripts": "ask"},
                "something": "else",
            }
        )
        self.assertEqual(out, {"theme": {"header": "colored"}})
        self.assertEqual(notes, [])


if __name__ == "__main__":
    unittest.main()
