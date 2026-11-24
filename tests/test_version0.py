# SPDX-License-Identifier: GPL-3.0-or-later
"""The setups OpenManager 0.x kept in a scene, read and converted. fixtures/openmanager0_setups.json is the text of
rootNode's OpenManager_Dat as 0.x's own model.encode writes it, made with the code of OpenManager-Legacy."""

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

import stand_in  # noqa: E402 - tests/ is on the path (tests/run.py)

from openmanager import model, version0

STORED = (Path(__file__).absolute().parent / "fixtures" / "openmanager0_setups.json").read_text(encoding="utf-8")


def without_ids(value):
    """A setup of 0.x without the lasting IDs it gave nodes and layers, which are not taken."""
    if isinstance(value, dict):
        return {k: without_ids(v) for k, v in value.items() if k not in ("uid", "uids")}
    if isinstance(value, list):
        return [without_ids(v) for v in value]
    return value


class Setups(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(STORED)
        self.found = version0.convert(STORED)

    def test_every_card_comes_back_as_0x_kept_it(self):
        self.assertIsNone(self.found["problem"])
        self.assertEqual([s["id"] for s in self.found["setups"]], [1, 2])
        for raw, setup in zip(self.raw["setups"], self.found["setups"], strict=True):
            for key, value in raw.items():
                if key == "lights":
                    self.assertEqual(setup[key]["set"], value["set"])
                    self.assertEqual(setup[key]["enabled"], value["enabled"])
                    continue
                self.assertEqual(without_ids(setup[key]), without_ids(value), key)

    def test_what_a_setup_sets_is_there(self):
        s = self.found["setups"][0]
        self.assertEqual(
            (s["camera"]["handle"], s["camera"]["name"], s["camera"]["locked"]), (101, "CAM_Kitchen", True)
        )
        self.assertEqual(s["sun"]["extra"][0]["props"], {"3|CoronaSun|intensity": 0.4})
        self.assertEqual(s["environment"]["extra"][0]["name"], "Sky_Noon")
        self.assertEqual(s["props"]["26|301|intensity"], 12.0)
        self.assertEqual([t["kind"] for t in s["output"]["preset"]], ["Camera", "Text", "Version", "Extension"])
        self.assertEqual(s["post"]["cats"]["bloom"]["props"]["bloomGlare_bloomIntensity"], 2.5)
        self.assertEqual(s["snippet"]["pre_setup"], 'print "kitchen"')
        self.assertEqual(s["variants"]["set"][0]["layers"], ["Sofa_A", "Sofa_B"])

    def test_the_lasting_ids_of_0x_are_left_out(self):
        # they are in an app data slot of 0.x: kept, they would make this version take a node for another one
        for s in self.found["setups"]:
            refs = model.node_refs(s) + s["layers"]["set"]
            self.assertEqual([r for r in refs if "uid" in r], [])
            self.assertEqual(s["lights"]["uids"], {})
            self.assertEqual([v for v in s["variants"]["set"] if "uids" in v], [])
        # and the handles and names stay, to find the nodes again
        self.assertEqual(model.resolve_query(self.found["setups"][:1])[0], [101, "", "CAM_Kitchen"])

    def test_the_todo_list_and_the_default_render_settings_come_too(self):
        self.assertEqual(self.found["todo"], [{"text": "Check the window glass", "done": False}])
        self.assertEqual(self.found["rs_default"], {"progressive_passLimit": 50})

    def test_the_scene_state_0x_kept_is_left_out_and_said(self):
        self.assertEqual(self.found["left_out"], [version0.LEFT_OUT_BASE])
        lines = version0.report(self.found)
        self.assertIn("converted 2 setup(s)", lines[0])
        self.assertIn(version0.LEFT_OUT_BASE, lines[1])
        raw = dict(self.raw)
        del raw["base"]
        found = version0.convert(json.dumps(raw))
        self.assertEqual(found["left_out"], [])
        self.assertEqual(len(version0.report(found)), 1)

    def test_text_that_is_not_setups_of_0x_is_not_taken(self):
        for text in ("", "not json", json.dumps({"something": "else"}), model.COMPRESSED_PREFIX + "eJw=", None):
            self.assertIsNone(version0.convert(text), text)

    def test_setups_too_big_are_refused_and_said(self):
        found = version0.convert(" " * (model.MAX_STORED + 1))
        self.assertEqual(found["setups"], [])
        self.assertIn("bigger than OpenManager reads", found["problem"])

    def test_values_of_the_wrong_kind_get_their_defaults(self):
        # a file can come from anyone: the setups of 0.x go through the same checks as this version's
        raw = copy.deepcopy(self.raw)
        raw["setups"][0]["camera"]["handle"] = [101]
        raw["setups"][0]["layers"]["set"].append("not a row")
        s = version0.convert(json.dumps(raw))["setups"][0]
        self.assertIsNone(s["camera"]["handle"])
        self.assertEqual([r["name"] for r in s["layers"]["set"]], ["Walls", "Sofa_A"])


class FakeMax:
    """pymxs.runtime as read_setups uses it: the root node's attributes, and every call it gets."""

    def __init__(self, **keys):
        self.keys = keys
        self.calls = []

    def Name(self, name):  # noqa: N802 - pymxs' name
        return name

    def oscn_readKey(self, key):  # noqa: N802 - the MAXScript function's name
        self.calls.append(("oscn_readKey", key))
        return self.keys.get(key, "")

    def oscn_readOldSetups(self):  # noqa: N802 - the MAXScript function's name
        self.calls.append(("oscn_readOldSetups",))
        return ""


class Reading(unittest.TestCase):
    def setUp(self):
        stand_in.install()
        from openmanager import maxlink

        self.maxlink = maxlink

    def read(self, **keys):
        fake = FakeMax(**keys)
        with mock.patch.object(self.maxlink, "rt", fake):
            data, source = self.maxlink.read_setups(1)
        return data, source, fake

    def test_a_scene_of_0x_gives_its_setups_and_is_only_read(self):
        data, source, fake = self.read(OpenManager_Dat=STORED)
        self.assertEqual(source, "openmanager0")
        self.assertEqual([s["scenename"] for s in data["setups"]], ["Kitchen_Day", "Kitchen_Night"])
        self.assertEqual({c[0] for c in fake.calls}, {"oscn_readKey"})

    def test_the_setups_of_this_version_win_over_those_of_0x(self):
        ours = model.encode([model.empty_setup(7)])
        data, source, _ = self.read(OpenScene_Dat=ours, OpenManager_Dat=STORED)
        self.assertEqual((source, [s["id"] for s in data["setups"]]), ("ours", [7]))

    def test_the_setups_of_0x_win_over_those_of_another_scene_manager(self):
        _, source, _ = self.read(OpenManager_Dat=STORED, SceneManager_Dat="W10=" * 10)
        self.assertEqual(source, "openmanager0")

    def test_setups_of_0x_that_cannot_be_read_are_said_and_the_next_ones_are_looked_for(self):
        with mock.patch("builtins.print") as said:
            _, source, _ = self.read(OpenManager_Dat=" " * (model.MAX_STORED + 1))
        self.assertEqual(source, "none")
        self.assertIn("were not read", said.call_args[0][0])

    def test_the_environment_mix_of_0x_is_a_mix(self):
        self.assertTrue(self.maxlink.Scene({"env_name": "OM_EnvMix_01"}).env_is_mix())
        self.assertTrue(self.maxlink.Scene({"env_name": "OSCN_EnvMix_01"}).env_is_mix())
        self.assertFalse(self.maxlink.Scene({"env_name": "HDRI_Studio"}).env_is_mix())


if __name__ == "__main__":
    unittest.main()
