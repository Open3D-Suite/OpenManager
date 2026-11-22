# SPDX-License-Identifier: GPL-3.0-or-later
"""What runs when 3ds Max starts, from the bundle's start-up script (openscene_bundle.ms): the settings of the 2.x
versions are carried over, the copy that the old .mzp installer put in the user's scripts folders is removed (its
settings stay), the toolbar is placed the first time, and one line in the MAXScript Listener says what was done.
It must work without an interface too (3dsmaxbatch, render nodes): no Qt here.
"""

import os
import shutil

from . import __version__, folders, toolbar

# What the .mzp installer of the 2.x versions copied, relative to 3ds Max's user folders (getDir #userScripts...).
# Only these paths, and the scripts folder only when it holds this package: never anything else of the person's.
OLD_SCRIPTS = "OpenScene"
OLD_MACRO = "OpenScene.mcr"
OLD_STARTUP = "OpenScene_startup.ms"
OLD_ICON_PREFIX = "OpenScene_"


def old_install(scripts, macros, startup, icons):
    """The files of an old .mzp install of OpenScene, given 3ds Max's user folders."""
    found = []
    folder = os.path.join(scripts, OLD_SCRIPTS)
    if os.path.isfile(os.path.join(folder, "openscene", "window.py")):
        found.append(folder)
    for path in (os.path.join(macros, OLD_MACRO), os.path.join(startup, OLD_STARTUP)):
        if os.path.isfile(path):
            found.append(path)
    for theme in ("Dark", "Light"):
        theme_dir = os.path.join(icons, theme)
        if os.path.isdir(theme_dir):
            names = sorted(n for n in os.listdir(theme_dir) if n.startswith(OLD_ICON_PREFIX) and n.endswith(".png"))
            found += [os.path.join(theme_dir, n) for n in names]
    return found


def remove(paths):
    """Removes these files and folders; returns those that could not be removed, with why."""
    failed = []
    for path in paths:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as error:
            failed.append("%s (%s)" % (path, error))
    return failed


def run():
    """Called by the bundle's start-up script. Never raises: a failure is said in the Listener."""
    from pymxs import runtime as rt

    lines = []
    try:
        plugcfg = str(rt.getDir(rt.Name("plugcfg")))
        for what, result in folders.carry_over_plugcfg(plugcfg):
            lines.append("%s of the earlier version: %s" % (what, folders.describe(result)))
    except Exception as error:  # noqa: BLE001 - start-up goes on without the old settings; said in the Listener
        lines.append("settings of the earlier version not copied: %s" % error)
    try:
        user = [str(rt.getDir(rt.Name(n))) for n in ("userScripts", "userMacros", "userStartupScripts", "userIcons")]
        old = old_install(*user)
        if old:
            failed = remove(old)
            lines.append("the copy installed with OpenScene.mzp was removed (its settings stay)")
            lines += ["could not remove " + f for f in failed]
    except Exception as error:  # noqa: BLE001 - the old copy only stays; said in the Listener
        lines.append("the copy installed with OpenScene.mzp was not removed: %s" % error)
    rt.oscn_settingsDir = str(folders.settings_dir() or "")
    try:
        placed = toolbar.place()
        if placed:
            lines.append(placed)
    except Exception as error:  # noqa: BLE001 - the button can still be placed by hand; said in the Listener
        lines.append("toolbar not placed: %s" % error)
    print("OpenScene %s: %s" % (__version__, "; ".join(lines) if lines else "ready"))
