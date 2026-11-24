# SPDX-License-Identifier: GPL-3.0-or-later
"""What runs when 3ds Max starts, from the bundle's start-up script (openmanager_bundle.ms): the settings of the
versions before are carried over (folders.carry_over), what older installs left is removed (the copies the .mzp
installers of OpenScene and of OpenManager 0.x put in the user's folders, and an OpenScene.bundle; their settings
stay), the toolbar is placed the first time, and the MAXScript Listener says what was done. It must work without an
interface too (3dsmaxbatch, render nodes): no Qt here.
"""

import dataclasses
import os
import re
import shutil
from pathlib import Path

from . import __version__, folders, toolbar

HERE = os.path.dirname(os.path.abspath(__file__))
# For tests only: a folder that stands for the folders where the versions before left files, each one a folder of
# the same name inside it (OLD_PLACES), so that a test, or a 3ds Max started for one, never reads or removes the
# person's own.
TEST_OLD_FOLDERS = "OPENMANAGER_TEST_OLD_FOLDERS"
# 3ds Max's folders (getDir) where the versions before left files, and Autodesk's folder of plug-in bundles
USER_FOLDERS = ("userScripts", "userMacros", "userStartupScripts", "userIcons")
OLD_PLACES = ("plugcfg",) + USER_FOLDERS + ("ApplicationPlugins",)


@dataclasses.dataclass(frozen=True)
class Mzp:
    """What the .mzp installer of a version before copied into 3ds Max's user folders. Only these files, and each
    one only when it is that version's own: the scripts folder when it holds `package` (files of that version's
    alone), the macro and the start-up script when they hold `says`, the icons by their exact names."""

    name: str
    scripts: str  # in userScripts
    package: tuple
    macro: str  # in userMacros
    startup: str  # in userStartupScripts
    says: tuple  # (in the macro, in the start-up script)
    icon: re.Pattern  # in userIcons\Dark and userIcons\Light


MZPS = (
    Mzp(
        "OpenScene.mzp",
        "OpenScene",
        (("openscene", "window.py"),),
        "OpenScene.mcr",
        "OpenScene_startup.ms",
        ("macroScript OpenScene", "oscn_startupCheck"),
        re.compile(r"OpenScene_\d+\.png", re.IGNORECASE),
    ),
    Mzp(
        "the OpenManager.mzp of 0.x",
        "OpenManager",
        (("openmanager", "window.py"), ("omgr_core.ms",)),
        "OpenManager.mcr",
        "OpenManager_startup.ms",
        ("macroScript OpenManager", "omgr_startupCheck"),
        re.compile(r"OpenManager_\d+\.png", re.IGNORECASE),
    ),
)

# OpenScene's bundle, in ApplicationPlugins (the launcher replaces OpenManager.bundle itself when it updates): taken
# only when its PackageContents.xml has the ProductCode OpenScene had.
OLD_BUNDLE = "OpenScene.bundle"
OLD_BUNDLE_CODE = re.compile(r'ProductCode\s*=\s*"\{1DE32304-98D8-46E2-B9E7-BBEDA0AE3FA9\}"', re.IGNORECASE)


def old_install(scripts, macros, startup, icons, mzp):
    """The files that `mzp` (one of MZPS) installed, given 3ds Max's user folders."""
    found = []
    folder = os.path.join(scripts, mzp.scripts)
    if all(os.path.isfile(os.path.join(folder, *part)) for part in mzp.package):
        found.append(folder)
    for path, says in zip((os.path.join(macros, mzp.macro), os.path.join(startup, mzp.startup)), mzp.says, strict=True):
        if os.path.isfile(path) and _holds(path, says):
            found.append(path)
    for theme in ("Dark", "Light"):
        theme_dir = os.path.join(icons, theme)
        if os.path.isdir(theme_dir):
            found += [os.path.join(theme_dir, n) for n in sorted(os.listdir(theme_dir)) if mzp.icon.fullmatch(n)]
    return found


def old_bundle(plugins):
    """[OpenScene.bundle] in the folder of plug-in bundles `plugins` when it is OpenScene's own, else []."""
    folder = os.path.join(plugins, OLD_BUNDLE)
    if _inside(HERE, folder):
        return []  # the bundle this runs from: never
    path = os.path.join(folder, "PackageContents.xml")
    return [folder] if os.path.isfile(path) and _holds(path, OLD_BUNDLE_CODE) else []


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


def old_places(rt, environ=None):
    """{name in OLD_PLACES: folder}: where 3ds Max and Windows have them (ApplicationPlugins in %APPDATA%\\Autodesk,
    left out without APPDATA), or, with TEST_OLD_FOLDERS, inside that folder."""
    environ = os.environ if environ is None else environ
    if environ.get(TEST_OLD_FOLDERS):
        return {name: str(Path(environ[TEST_OLD_FOLDERS]) / name) for name in OLD_PLACES}
    places = {name: str(rt.getDir(rt.Name(name))) for name in OLD_PLACES if name != "ApplicationPlugins"}
    if environ.get("APPDATA"):
        places["ApplicationPlugins"] = str(Path(environ["APPDATA"]) / "Autodesk" / "ApplicationPlugins")
    return places


def remove_old_installs(places):
    """Removes what older installs left in `places` (old_places). Returns lines for the MAXScript Listener."""
    lines = []
    if all(n in places for n in USER_FOLDERS):
        for mzp in MZPS:
            old = old_install(*(places[n] for n in USER_FOLDERS), mzp)
            if old:
                lines.append("removed what %s installed in 3ds Max's user folders (its settings stay)" % mzp.name)
                lines += ["could not remove " + f for f in remove(old)]
    if "ApplicationPlugins" in places:
        old = old_bundle(places["ApplicationPlugins"])
        if old:
            lines.append("removed %s from %s (its settings stay)" % (OLD_BUNDLE, places["ApplicationPlugins"]))
            lines += ["could not remove " + f for f in remove(old)]
        elif os.path.isdir(os.path.join(places["ApplicationPlugins"], OLD_BUNDLE)):
            lines.append("left %s as it is: it is not OpenScene's own" % OLD_BUNDLE)
    return lines


def run():
    """Called by the bundle's start-up script. Never raises: a failure is said in the Listener."""
    from pymxs import runtime as rt

    lines, notes = [], []
    try:
        places = old_places(rt)
    except Exception as error:  # noqa: BLE001 - nothing of the versions before is looked at; said in the Listener
        places = {}
        lines.append("the folders of 3ds Max could not be read: %s" % error)
    try:
        carried = folders.carry_over(places.get("plugcfg"))
        folders.use(carried)
        notes += folders.report(carried)
    except Exception as error:  # noqa: BLE001 - start-up goes on without the old settings; said in the Listener
        notes.append("settings of the versions before not copied: %s" % error)
    try:
        notes += remove_old_installs(places)
    except Exception as error:  # noqa: BLE001 - the old copies only stay; said in the Listener
        notes.append("what older installs left was not removed: %s" % error)
    rt.oscn_settingsDir = str(folders.settings_dir() or "")
    try:
        placed = toolbar.place()
        if placed:
            lines.append(placed)
    except Exception as error:  # noqa: BLE001 - the button can still be placed by hand; said in the Listener
        lines.append("toolbar not placed: %s" % error)
    print("OpenManager %s: %s" % (__version__, "; ".join(lines) if lines else "ready"))
    for note in notes:
        print("OpenManager: " + note)


def _holds(path, says):
    """Whether the start of a file (1 MB) has this text or matches this pattern."""
    try:
        with open(path, "rb") as f:
            text = f.read(1 << 20).decode("utf-8", "replace")
    except OSError:
        return False
    return bool(says.search(text)) if isinstance(says, re.Pattern) else says in text


def _inside(path, folder):
    """Whether `path` is `folder` or inside it."""
    try:
        return Path(os.path.realpath(path)).is_relative_to(os.path.realpath(folder))
    except (OSError, ValueError):
        return True
