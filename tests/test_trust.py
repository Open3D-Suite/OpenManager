# SPDX-License-Identifier: GPL-3.0-or-later
"""What a setup runs (scripts, script files, render presets) runs only once this computer trusts it."""

import os
import tempfile
import unittest

from openmanager import trust


class Trust(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = temporary.name

    def a_file(self, name, text):
        path = os.path.join(self.folder, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_every_kind_of_thing_a_setup_runs_is_found(self):
        pre = self.a_file("pre.ms", 'print "pre"')
        preset = self.a_file("look.rps", "preset")
        acts = [("code", 'print "a"'), ("res", 1920, 1080), ("preset", preset), ("renderscripts", pre, "", "x = 1", "")]
        titles = [it.title for it in trust.items(acts)]
        self.assertEqual(
            titles, ["Script (Script Editor card)", "Render preset", "Pre-Render script file", "Pre-Render script"]
        )

    def test_blank_code_runs_nothing_and_is_not_asked_about(self):
        self.assertEqual(trust.items([("code", "  \n "), ("renderscripts", "", "", "", "")]), [])

    def test_what_is_not_trusted_is_taken_out_and_the_rest_stays(self):
        preset = self.a_file("look.rps", "preset")
        acts = [
            ("code", "trusted"),
            ("code", "not trusted"),
            ("preset", preset),
            ("res", 1, 2),
            ("renderscripts", "", "", "not trusted either", "trusted"),
        ]
        ok = {trust.code_digest("trusted")}
        out, left_out = trust.allowed_actions(acts, lambda d: d in ok)
        self.assertEqual(out, [("code", "trusted"), ("res", 1, 2), ("renderscripts", "", "", "", "trusted")])
        self.assertEqual(len(left_out), 3)

    def test_a_trusted_file_that_changes_is_asked_about_again(self):
        path = self.a_file("pre.ms", 'print "a"')
        before = trust.file_digest(path)
        self.a_file("pre.ms", 'deleteFile "x"')
        self.assertNotEqual(trust.file_digest(path), before)

    def test_the_same_text_in_another_file_is_another_thing(self):
        a = self.a_file("a.ms", "same")
        b = self.a_file("b.ms", "same")
        self.assertNotEqual(trust.file_digest(a), trust.file_digest(b))

    def test_a_file_that_cannot_be_read_never_runs(self):
        missing = os.path.join(self.folder, "missing.ms")
        self.assertIsNone(trust.file_digest(missing))
        out, left_out = trust.allowed_actions([("preset", missing)], lambda d: True)
        self.assertEqual(out, [])
        self.assertEqual(len(left_out), 1)

    def test_the_trusted_list_keeps_the_newest_and_has_a_limit(self):
        kept = trust.remember([], ["d%d" % i for i in range(trust.MAX_TRUSTED + 10)])
        self.assertEqual(len(kept), trust.MAX_TRUSTED)
        self.assertEqual(kept[-1], "d%d" % (trust.MAX_TRUSTED + 9))
        self.assertEqual(trust.remember(["a", "b"], ["a"]), ["b", "a"])

    def test_the_question_names_what_would_run(self):
        items = trust.items([("code", 'print "hello"\nprint "two"')])
        text = trust.question(items)
        self.assertIn('print "hello" (+1 more lines)', text)
        self.assertIn("Run them?", text)


if __name__ == "__main__":
    unittest.main()
