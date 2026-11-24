# SPDX-License-Identifier: GPL-3.0-or-later
"""The question asked before scripts and presets that came with a file run: its safe answer is No. Needs PySide6
(the Python of 3ds Max has it); with a Python without it, these tests are skipped."""

import importlib.util
import os
import subprocess
import sys
import unittest

import stand_in

_START_QT = "from PySide6 import QtWidgets; QtWidgets.QApplication([]).processEvents()"


def qt_starts():
    """Whether Qt can make windows here, tried first in a process of its own: the PySide6 that comes with 3ds Max
    is there outside 3ds Max too, but cannot start without it."""
    if importlib.util.find_spec("PySide6") is None:
        return False
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    try:
        run = subprocess.run([sys.executable, "-I", "-c", _START_QT], env=env, capture_output=True, timeout=30)  # noqa: S603 - this Python, with a fixed line
    except (OSError, subprocess.TimeoutExpired):
        return False
    return run.returncode == 0


HAS_QT = qt_starts()


@unittest.skipUnless(HAS_QT, "Qt cannot make windows with this Python")
class SafeQuestion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        stand_in.install()
        from PySide6 import QtCore, QtTest, QtWidgets

        cls.QtCore, cls.QtTest, cls.QtWidgets = QtCore, QtTest, QtWidgets
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        from openmanager import dialogs

        cls.dialogs = dialogs

    def answer(self, do):
        """Asks, and does `do(box, yes, no)` once the question is up."""
        QtCore, QtWidgets = self.QtCore, self.QtWidgets

        def act():
            box = next(w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, QtWidgets.QMessageBox))
            yes = box.button(QtWidgets.QMessageBox.Yes)
            no = box.button(QtWidgets.QMessageBox.No)
            do(box, yes, no)

        QtCore.QTimer.singleShot(0, act)
        return self.dialogs.ask_safely(None, "OpenManager", "Run them?")

    def test_enter_says_no_even_on_the_yes_button(self):
        def press_enter_on_yes(box, yes, no):
            yes.setFocus()
            self.QtTest.QTest.keyClick(yes, self.QtCore.Qt.Key_Return)

        self.assertFalse(self.answer(press_enter_on_yes))

    def test_escape_says_no(self):
        self.assertFalse(self.answer(lambda box, yes, no: self.QtTest.QTest.keyClick(box, self.QtCore.Qt.Key_Escape)))

    def test_a_click_on_yes_says_yes(self):
        self.assertTrue(self.answer(lambda box, yes, no: yes.click()))

    def test_space_on_yes_says_yes(self):
        def space_on_yes(box, yes, no):
            yes.setFocus()
            self.QtTest.QTest.keyClick(yes, self.QtCore.Qt.Key_Space)

        self.assertTrue(self.answer(space_on_yes))


if __name__ == "__main__":
    unittest.main()
