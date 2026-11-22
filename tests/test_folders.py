# SPDX-License-Identifier: GPL-3.0-or-later
"""Where OpenScene keeps its files, and the settings of the 2.x versions carried over from plugcfg. Every folder is a
temporary one, named by the variables every Open3D app reads."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openscene import folders, open3d_settings


class Folders(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.settings = self.root / "settings"
        self.data = self.root / "data"
        self.plugcfg = self.root / "plugcfg"
        self.plugcfg.mkdir()
        variables = {"OPEN3D_SETTINGS_DIR": str(self.settings), "OPEN3D_DATA_DIR": str(self.data)}
        patcher = mock.patch.dict(os.environ, variables)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_folders_are_named_after_the_app(self):
        self.assertEqual(folders.settings_dir(), self.settings / "OpenScene")
        self.assertEqual(folders.data_dir(), self.data / "OpenScene")
        self.assertEqual(folders.settings_file(folders.SETTINGS), str(self.settings / "OpenScene" / "settings.json"))

    def test_without_any_variable_there_is_no_folder(self):
        with mock.patch.dict(os.environ, clear=True):
            self.assertIsNone(folders.settings_dir())
            self.assertIsNone(folders.settings_file(folders.SETTINGS))
            self.assertIsNone(folders.data_path(folders.HDRI_PREVIEWS))

    def test_asking_for_a_folder_creates_nothing(self):
        folders.settings_file(folders.SETTINGS)
        folders.data_path(folders.HDRI_PREVIEWS)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["plugcfg"])

    def test_write_text_creates_the_folder_and_leaves_no_temporary_file(self):
        target = self.settings / "OpenScene" / "settings.json"
        folders.write_json(str(target), {"a": 1})
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"a": 1})
        self.assertEqual([p.name for p in target.parent.iterdir()], ["settings.json"])

    def test_the_settings_of_2x_are_carried_over_once_under_their_new_names(self):
        (self.plugcfg / "OpenScene.json").write_text('{"theme": {}}', encoding="utf-8")
        (self.plugcfg / "OpenScene_notify.txt").write_text("0", encoding="utf-8")
        done = folders.carry_over_plugcfg(str(self.plugcfg))
        self.assertEqual([(what, r.kind) for what, r in done], [("settings", open3d_settings.COPIED)])
        new = self.settings / "OpenScene"
        self.assertEqual((new / "settings.json").read_text(encoding="utf-8"), '{"theme": {}}')
        self.assertEqual((new / "notify.txt").read_text(encoding="utf-8"), "0")
        # the old files stay as they were
        self.assertTrue((self.plugcfg / "OpenScene.json").is_file())
        # and a second start copies nothing over what the new version already wrote
        (new / "settings.json").write_text("{}", encoding="utf-8")
        self.assertEqual(folders.carry_over_plugcfg(str(self.plugcfg)), [])
        self.assertEqual((new / "settings.json").read_text(encoding="utf-8"), "{}")

    def test_without_old_settings_nothing_is_created(self):
        self.assertEqual(folders.carry_over_plugcfg(str(self.plugcfg)), [])
        self.assertFalse(self.settings.exists())

    def test_the_hdri_previews_go_to_the_data_folder(self):
        old = self.plugcfg / "OpenScene_hdri"
        old.mkdir()
        (old / "a_0123456789.jpg").write_bytes(b"jpg")
        done = folders.carry_over_plugcfg(str(self.plugcfg))
        self.assertEqual([what for what, _ in done], ["HDRI previews"])
        self.assertTrue((self.data / "OpenScene" / "hdri_previews" / "a_0123456789.jpg").is_file())
        self.assertTrue((old / "a_0123456789.jpg").is_file())

    def test_describe_says_what_was_left_out(self):
        r = open3d_settings.CarryOver(open3d_settings.COPIED, files=2, left_out=(("x.json", "in use"),))
        self.assertEqual(folders.describe(r), "copied 2 files, left out: x.json (in use)")


if __name__ == "__main__":
    unittest.main()
