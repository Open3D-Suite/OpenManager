# SPDX-License-Identifier: GPL-3.0-or-later
"""The setups kept in a .max file: what is read back, what is refused, and the names a setup may carry."""

import base64
import json
import unittest
import zlib

from openscene import external, model


def stored(setups, **extra):
    return json.dumps(dict({"format": "openscene", "version": model.FORMAT_VERSION, "setups": setups}, **extra))


class Storing(unittest.TestCase):
    def test_setups_come_back_as_they_were_stored(self):
        s = model.empty_setup(1)
        s["scenename"] = "Kitchen"
        back = model.decode(model.encode([s], todo=[{"text": "lights"}]))
        self.assertEqual(back["setups"][0]["scenename"], "Kitchen")
        self.assertEqual(back["todo"], [{"text": "lights"}])
        self.assertIsNone(back["problem"])

    def test_big_setups_are_packed_and_unpacked(self):
        s = model.empty_setup(1)
        s["layers"]["set"] = [model.layer_entry("layer %d" % i) for i in range(2000)]
        text = model.encode([s])
        self.assertTrue(text.startswith(model.COMPRESSED_PREFIX))
        self.assertEqual(len(model.decode(text)["setups"][0]["layers"]["set"]), 2000)

    def test_setups_saved_before_2_0_0_are_read(self):
        packed = base64.b64encode(zlib.compress(stored([model.empty_setup(3)]).encode("utf-8"))).decode("ascii")
        back = model.decode(model.OLD_COMPRESSED_PREFIX + packed)
        self.assertEqual(back["setups"][0]["id"], 3)

    def test_text_that_is_not_ours_is_not_taken(self):
        self.assertIsNone(model.decode(""))
        self.assertIsNone(model.decode("not json"))
        self.assertIsNone(model.decode(json.dumps({"something": "else"})))


class Refusing(unittest.TestCase):
    """A .max file can come from anyone: what it holds is checked, and what OpenScene cannot take is left alone."""

    def test_a_newer_format_is_refused_not_guessed(self):
        back = model.decode(stored([model.empty_setup(1)]).replace('"version": 1', '"version": 9'))
        self.assertEqual(back["setups"], [])
        self.assertIn("newer OpenScene", back["problem"])

    def test_a_format_version_that_is_not_a_number_is_refused(self):
        back = model.decode(json.dumps({"version": "1", "setups": []}))
        self.assertEqual(back["setups"], [])
        self.assertTrue(back["problem"])

    def test_packed_setups_that_unpack_past_the_limit_are_refused(self):
        bomb = zlib.compress(b"[" + b" " * (model.MAX_STORED + 10) + b"]")
        back = model.decode(model.COMPRESSED_PREFIX + base64.b64encode(bomb).decode("ascii"))
        self.assertEqual(back["setups"], [])
        self.assertIn("bigger", back["problem"])

    def test_damaged_packed_setups_are_refused(self):
        back = model.decode(model.COMPRESSED_PREFIX + "!!not base64!!")
        self.assertEqual(back["setups"], [])
        self.assertIn("damaged", back["problem"])

    def test_too_many_setups_are_cut_and_said(self):
        back = model.decode(stored([{"id": i + 1} for i in range(model.MAX_SETUPS + 5)]))
        self.assertEqual(len(back["setups"]), model.MAX_SETUPS)
        self.assertIn("only the first", back["problem"])

    def test_a_value_of_the_wrong_kind_gets_its_default(self):
        back = model.decode(stored([{"id": 1, "camera": "x", "layers": {"set": 5, "enabled": "yes"}, "render": 1}]))
        s = back["setups"][0]
        self.assertEqual(s["camera"], model.empty_setup(1)["camera"])
        self.assertEqual(s["layers"]["set"], [])
        self.assertIs(s["layers"]["enabled"], False)
        self.assertIs(s["render"], True)

    def test_every_setup_gets_an_id_of_its_own(self):
        back = model.decode(stored([{"id": 3}, {"id": 3}, {"id": "x"}, {"id": 1}, {"id": True}]))
        ids = [s["id"] for s in back["setups"]]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids[0], 3)

    def test_default_render_settings_with_paths_or_objects_are_dropped(self):
        back = model.decode(stored([], rs_default={"ok_value": 2, "a.controller.script": 1, "obj": {"x": 1}}))
        self.assertEqual(back["rs_default"], {"ok_value": 2})


class Names(unittest.TestCase):
    def test_a_plain_name_cannot_reach_another_object_or_run_code(self):
        for good in ("CoronaBitmap", "_x1", "colorMap_pipeline"):
            self.assertTrue(model.is_plain_name(good), good)
        for bad in ("", "1abc", "a.b", 'deleteFile "x"', "a()", "a b", None, 5, "x" * 200):
            self.assertFalse(model.is_plain_name(bad), bad)

    def test_only_operator_classes_make_a_tone_mapping_chain(self):
        self.assertTrue(model.is_tone_operator("FilmicOperatorPlugin"))
        self.assertFalse(model.is_tone_operator("Box"))
        self.assertFalse(model.is_tone_operator("x;OperatorPlugin"))

    def test_render_settings_are_plain_names_with_plain_values(self):
        self.assertTrue(model.renderer_value_ok("progressive_passLimit", 10))
        self.assertFalse(model.renderer_value_ok("a.b", 10))
        self.assertFalse(model.renderer_value_ok("ok", {"$color": [1, 2, 3]}))

    def test_post_production_takes_only_the_settings_of_its_category(self):
        self.assertTrue(model.post_setting_ok("bloom", "bloomGlare_enabled"))
        self.assertFalse(model.post_setting_ok("bloom", "colorMap_pipeline"))
        self.assertFalse(model.post_setting_ok("nope", "bloomGlare_enabled"))


class OtherSceneManager(unittest.TestCase):
    def test_entries_that_are_not_setups_are_skipped(self):
        data = base64.b64encode(json.dumps([5, "x", {"scenename": {"text": "Hall"}}]).encode("utf-8")).decode()
        out = external.convert(data, 1)
        self.assertEqual([s["scenename"] for s in out], ["Hall"])

    def test_too_big_or_broken_data_is_not_read(self):
        self.assertIsNone(external.convert("x" * (model.MAX_STORED + 1), 1))
        self.assertIsNone(external.convert("%%%", 1))
        self.assertIsNone(external.convert(None, 1))


class PresetFiles(unittest.TestCase):
    """A .osp file can come from anyone too: it is read with the same checks as a .max file."""

    def test_exported_setups_are_read_back(self):
        s = model.empty_setup(4)
        s["scenename"] = "Hall"
        self.assertEqual(model.read_preset(model.preset_text([s]))[0]["scenename"], "Hall")

    def test_a_plain_list_of_setups_from_earlier_versions_is_read(self):
        self.assertEqual(len(model.read_preset(json.dumps([{"id": 1}, 5, {"id": 2}]))), 2)

    def test_a_newer_or_broken_preset_is_refused_and_said(self):
        with self.assertRaisesRegex(ValueError, "newer"):
            model.read_preset(json.dumps({"version": 7, "setups": []}))
        with self.assertRaisesRegex(ValueError, "not an OpenScene preset"):
            model.read_preset("{nope")
        with self.assertRaisesRegex(ValueError, "no setups"):
            model.read_preset(json.dumps({"setups": "x"}))
        with self.assertRaisesRegex(ValueError, "bigger"):
            model.read_preset(" " * (model.MAX_STORED + 1))

    def test_an_output_preset_takes_only_the_cards_own_settings(self):
        out = model.read_output_preset(
            json.dumps(
                {
                    "output": {
                        "enabled": "yes",
                        "project_path": "D:/renders",
                        "unknown": 1,
                        "preset": [{"kind": "Camera"}, {"kind": "Evil", "value": "x"}, 5, {"kind": "Text", "value": 3}],
                    }
                }
            )
        )
        self.assertIs(out["enabled"], False)
        self.assertEqual(out["project_path"], "D:/renders")
        self.assertNotIn("unknown", out)
        self.assertEqual([t["kind"] for t in out["preset"]], ["Camera", "Text"])
        self.assertEqual(out["preset"][1]["value"], "_")  # a value of the wrong kind gets the default


class SharedLists(unittest.TestCase):
    def test_the_rows_of_every_setup_make_one_list_in_order(self):
        a, b = model.empty_setup(1), model.empty_setup(2)
        a["layers"]["set"] = [model.layer_entry("A"), model.layer_entry("B")]
        b["layers"]["set"] = [model.layer_entry("B", visible=False), model.layer_entry("C")]
        rows = model.shared_rows([a, b], "layers", "name")
        self.assertEqual([r["name"] for r in rows], ["A", "B", "C"])
        self.assertTrue(rows[1]["visible"])


if __name__ == "__main__":
    unittest.main()
