# SPDX-License-Identifier: GPL-3.0-or-later
"""Setups keep their nodes and layers through renames and merges: each reference has a lasting ID, and moves to
where the scene says the node is now."""

import json
import unittest

from openscene import model


def setup_with_refs():
    s = model.empty_setup(1)
    s["camera"].update(handle=10, name="Cam01", uid="c-1")
    s["sun"].update(handle=20, name="Sun", uid="s-1")
    s["objects"]["set"] = [dict(model.object_entry(30, "Sofa"), uid="o-1")]
    s["lights"]["set"] = [40]
    s["lights"]["uids"] = {"40": "l-1"}
    s["props"]["26|40|multiplier"] = 2.0
    return s


class Nodes(unittest.TestCase):
    def test_every_reference_is_asked_for_in_order(self):
        q = model.resolve_query([setup_with_refs()])
        self.assertEqual(
            q,
            [[10, "c-1", "Cam01"], [20, "s-1", "Sun"], [-1, "", ""], [30, "o-1", "Sofa"], [40, "l-1", ""]],
        )

    def test_a_merged_node_is_followed_to_its_new_handle_and_name(self):
        s = setup_with_refs()
        results = [(110, "Cam01"), (20, "Sun"), (-1, ""), (130, "Sofa_merged"), (140, "")]
        self.assertTrue(model.apply_resolved([s], results))
        self.assertEqual((s["camera"]["handle"], s["objects"]["set"][0]["handle"]), (110, 130))
        self.assertEqual(s["objects"]["set"][0]["name"], "Sofa_merged")
        # a light of the Lights card takes its settings and its ID to its new handle
        self.assertEqual(s["lights"]["set"], [140])
        self.assertEqual(s["props"], {"26|140|multiplier": 2.0})
        self.assertEqual(s["lights"]["uids"], {"140": "l-1"})

    def test_a_handle_that_is_another_node_now_is_never_used(self):
        s = setup_with_refs()
        model.apply_resolved([s], [(-2, "Cam01"), (20, "Sun"), (-1, ""), (-2, "Sofa"), (-2, "")])
        self.assertIsNone(s["camera"]["handle"])
        self.assertIsNone(s["objects"]["set"][0]["handle"])
        self.assertEqual(s["lights"]["set"], [40])  # kept, unless the setups were just imported

    def test_imported_setups_drop_a_light_that_is_another_node(self):
        s = setup_with_refs()
        model.apply_resolved([s], [(10, ""), (20, ""), (-1, ""), (30, ""), (-2, "")], strict=True)
        self.assertEqual((s["lights"]["set"], s["props"]), ([], {}))

    def test_a_missing_node_stays_in_its_setup(self):
        s = setup_with_refs()
        self.assertFalse(model.apply_resolved([s], [(-1, ""), (20, "Sun"), (-1, ""), (-1, ""), (-1, "")]))
        self.assertEqual(s["camera"]["handle"], 10)

    def test_an_object_row_waiting_for_its_node_is_kept_when_stored(self):
        stored = {"id": 1, "objects": {"enabled": True, "set": [{"handle": None, "name": "Sofa", "uid": "o-1"}]}}
        s = model.decode(json.dumps({"version": 1, "setups": [stored]}))["setups"][0]
        self.assertEqual(s["objects"]["set"][0]["uid"], "o-1")


class Layers(unittest.TestCase):
    def test_a_renamed_layer_keeps_its_place_in_layers_and_variants(self):
        s = model.empty_setup(1)
        s["layers"]["set"] = [dict(model.layer_entry("Furniture"), uid="ly-1"), model.layer_entry("Walls")]
        s["variants"]["set"] = [{"name": "V", "value": 1, "layers": ["Furniture", "Plants"], "uids": ["ly-1"]}]
        self.assertTrue(model.follow_layer_renames([s], {"ly-1": "Furniture_v2"}))
        self.assertEqual([x["name"] for x in s["layers"]["set"]], ["Furniture_v2", "Walls"])
        self.assertEqual(s["variants"]["set"][0]["layers"], ["Furniture_v2", "Plants"])
        self.assertEqual(s["variants"]["set"][0]["uids"], ["ly-1", ""])  # one ID beside each layer name

    def test_layers_without_an_id_are_left_as_they_are(self):
        s = model.empty_setup(1)
        s["layers"]["set"] = [model.layer_entry("Walls")]
        self.assertFalse(model.follow_layer_renames([s], {"other": "Walls_2"}))


if __name__ == "__main__":
    unittest.main()
