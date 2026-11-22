# SPDX-License-Identifier: GPL-3.0-or-later
"""Every text file of the repository is valid UTF-8 without broken characters, and the MAXScript files carry the
byte order mark 3ds Max needs to read them as UTF-8. And the MAXScript check finds the mistakes 3ds Max only reports
when a script runs."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import check_ms  # noqa: E402 - tools/ is put on the path just above

BINARY = (".png", ".jpg", ".ico", ".zip", ".mzp")


def tracked():
    # S607: git from PATH, to list the files of this repository
    names = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout  # noqa: S607
    return [n for n in names.splitlines() if not n.endswith(BINARY)]


class TextFiles(unittest.TestCase):
    def test_every_text_file_is_utf8_without_broken_characters(self):
        bad = []
        for name in tracked():
            data = (REPO / name).read_bytes()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as error:
                bad.append("%s: not UTF-8 (%s)" % (name, error))
                continue
            if "\ufffd" in text:
                bad.append("%s: holds a broken character" % name)
        self.assertEqual(bad, [])

    def test_maxscript_files_start_with_a_byte_order_mark(self):
        missing = [
            n
            for n in tracked()
            if n.endswith((".ms", ".mcr")) and not (REPO / n).read_bytes().startswith(b"\xef\xbb\xbf")
        ]
        self.assertEqual(missing, [])


class MaxScriptCheck(unittest.TestCase):
    def check(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".ms", delete=False, encoding="utf-8") as f:
            f.write(text)
        try:
            return check_ms.check(f.name)
        finally:
            Path(f.name).unlink()

    def test_a_reserved_word_used_as_a_name_is_found(self):
        # the installer of 2.2.0 and 2.2.1 stopped with "expected name" on `local at = ...`
        self.assertEqual(len(self.check('(\n    local at = findString txt "x"\n)\n')), 1)
        self.assertEqual(self.check('(\n    local closeAt = findString txt "x"\n)\n'), [])

    def test_an_escape_maxscript_does_not_know_is_found(self):
        self.assertEqual(len(self.check('print "D:\\qfolder"\n')), 1)
        self.assertEqual(self.check('print "D:\\\\qfolder\\n"\n'), [])

    def test_the_repository_passes_it(self):
        self.assertEqual(check_ms.main(), 0)


if __name__ == "__main__":
    unittest.main()
