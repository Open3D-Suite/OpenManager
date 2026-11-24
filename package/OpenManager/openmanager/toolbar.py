# SPDX-License-Identifier: GPL-3.0-or-later
"""The OpenManager toolbar, put once, at the first start: 3ds Max has no call to add a button to a toolbar (menus
have the 2025+ menu API, toolbars don't), so the interface is saved, a toolbar with the button is added to its
.cuix file (XML, UTF-8 with a byte order mark, CRLF) and the file is loaded again. The file is backed up first in
OpenManager's data folder and put back if anything fails. Nothing is done when a toolbar already has the button.
The buttons of OpenScene's action, which this version replaces, are made OpenManager's instead, where they are, and
the toolbar OpenScene added takes OpenManager's name.

The text functions need neither 3ds Max nor Qt; place() uses pymxs, imported inside it.
"""

import os
import shutil

from . import folders

NAME = "OpenManager"
ACTION = 'actionID="OpenManager`OpenManager"'
_ITEM = (
    '<Item typeID="2" type="CTB_MACROBUTTON" width="0" height="0" controlID="0" macroTypeID="3" '
    'macroType="MB_TYPE_ACTION" actionTableID="647394" imageID="-1" imageName="" ' + ACTION + ' tip="OpenManager" '
    'label="OpenManager" />'
)


# OpenScene's action, whose macro the first start removes with the rest of an OpenScene install, and its toolbar
OLD_ACTION = 'actionID="OpenScene`OpenScene"'
OLD_NAME = "OpenScene"


def with_old_buttons_moved(text):
    """The interface with each button of OpenScene's action running OpenManager's (with its tip and label), and the
    toolbar OpenScene added called OpenManager, unless one is called that already. Only those lines change."""
    lines = text.splitlines(keepends=True)
    taken = f'<Window objectName="{NAME}"' in text
    for i, line in enumerate(lines):
        if OLD_ACTION in line:
            line = line.replace(OLD_ACTION, ACTION)
            line = line.replace(f'tip="{OLD_NAME}"', f'tip="{NAME}"').replace(f'label="{OLD_NAME}"', f'label="{NAME}"')
            lines[i] = line
        elif not taken and f'<Window objectName="{OLD_NAME}" name="{OLD_NAME}"' in line:
            lines[i] = line.replace(
                f'<Window objectName="{OLD_NAME}" name="{OLD_NAME}"', f'<Window objectName="{NAME}" name="{NAME}"'
            )
    return "".join(lines)


def has_button(text):
    """Whether a toolbar (or anything else in the interface) already runs the OpenManager action."""
    return ACTION in text


def with_toolbar(text):
    """The interface with an "OpenManager" toolbar added before the end of its list of windows, with the line ends it
    already uses; None when the text has no list of windows."""
    at = text.find("</CUIWindows>")
    if at < 0:
        return None
    nl = "\r\n" if "\r\n" in text else "\n"
    start = at
    while start > 0 and text[start - 1] == " ":
        start -= 1
    block = (
        f'    <Window objectName="{NAME}" name="{NAME}" type="T" cType="1" toolbarRows="1">{nl}'
        f"            <Items>{nl}"
        f"                {_ITEM}{nl}"
        f"            </Items>{nl}"
        f"        </Window>{nl}"
    )
    return text[:start] + "    " + block + text[start:]


def without_toolbar(text):
    """The interface without the toolbar with_toolbar adds (a toolbar of the person's own is left alone)."""
    s = text.find(f'<Window objectName="{NAME}"')
    if s < 0:
        return text
    e = text.find("</Window>", s)
    if e < 0:
        return text
    stop = e + len("</Window>")
    while s > 0 and text[s - 1] == " ":
        s -= 1
    while stop < len(text) and text[stop] in "\r\n":
        stop += 1
    return text[:s] + text[stop:]


def place(environ=None):
    """At start, once: puts the toolbar, or notes that a toolbar has the button already. Returns what happened, as
    a line for the MAXScript Listener, or None when there was nothing to do."""
    done = folders.settings_file(folders.TOOLBAR_DONE, environ)
    if done is None or os.path.isfile(done):
        return None
    from pymxs import runtime as rt

    if rt.GetQuietMode() or rt.IsNetServer():
        return None  # no interface: 3dsmaxbatch, a render node
    rt.cui.saveConfig()
    path = str(rt.cui.getConfigFile() or "")
    if not path or not os.path.isfile(path):
        return "toolbar not placed: 3ds Max did not say which interface file it uses"
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    moved = with_old_buttons_moved(text)
    if moved == text and has_button(text):
        result = "the OpenManager button is already on a toolbar"
    else:
        new = moved if moved != text else with_toolbar(text)
        if new is None:
            return "toolbar not placed: %s has no list of windows" % path
        backup_dir = folders.data_path(folders.TOOLBAR_BACKUP, environ)
        if backup_dir is None:
            return "toolbar not placed: there is no data folder for the backup of the interface"
        os.makedirs(backup_dir, exist_ok=True)
        backup = os.path.join(backup_dir, os.path.basename(path))
        shutil.copy2(path, backup)
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(new)
            rt.cui.loadConfig(path)
            if f'<Window objectName="{NAME}"' in new:
                rt.cui.showToolbar(NAME)
        except Exception as error:  # noqa: BLE001 - any failure puts the interface back; it is said in the Listener
            shutil.copy2(backup, path)
            rt.cui.loadConfig(path)
            return "toolbar not placed (%s); the interface was put back" % error
        if new is moved:
            result = "the OpenScene buttons now open OpenManager (backup of the interface: %s)" % backup
        else:
            result = 'the "OpenManager" toolbar was added: drag it where you want it (backup: %s)' % backup
    os.makedirs(os.path.dirname(done), exist_ok=True)
    with open(done, "w", encoding="utf-8") as f:
        f.write("1\n")
    return result
