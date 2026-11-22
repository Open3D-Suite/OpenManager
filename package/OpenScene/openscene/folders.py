# SPDX-License-Identifier: GPL-3.0-or-later
"""Where OpenScene keeps its files, from what every Open3D app shares (open3d_settings).

Its settings go to %APPDATA%\\Open3D\\OpenScene, one set for every 3ds Max, and everything else it writes
(the HDRI previews, the toolbar's backup, the exports of a scene not saved yet) to
%LOCALAPPDATA%\\Open3D\\OpenScene; OPEN3D_SETTINGS_DIR and OPEN3D_DATA_DIR move them. Nothing here creates
them, except carry_over_plugcfg, once, with the settings of the 2.x versions.

No pymxs and no Qt: the tests load this module as it is.
"""

import contextlib
import json
import os
import shutil
import tempfile

from . import APP, open3d_settings

SETTINGS = "settings.json"  # the window: its cards, columns, theme and options
DEFAULT_LAYOUT = "default_layout.json"  # the card layout saved with Settings > Save as default
NOTIFY = "notify.txt"  # "0": don't offer to convert the setups of another scene manager
TOOLBAR_DONE = "toolbar_placed.txt"  # the first start already put the OpenScene toolbar (or found the button)
HDRI_PREVIEWS = "hdri_previews"
UNSAVED = "unsaved_scene"  # thumbnails, exports and presets of a scene that has no folder yet
TOOLBAR_BACKUP = "interface_backup"

# What the 2.x versions kept in the plugcfg folder of each 3ds Max, and its name now
OLD_FILES = {"OpenScene.json": SETTINGS, "OpenScene_default.json": DEFAULT_LAYOUT, "OpenScene_notify.txt": NOTIFY}
OLD_HDRI_PREVIEWS = "OpenScene_hdri"


def settings_dir(environ=None):
    """%APPDATA%\\Open3D\\OpenScene, or OpenScene in the folder OPEN3D_SETTINGS_DIR names; None without either."""
    return open3d_settings.app_settings_dir(APP, environ)


def data_dir(environ=None):
    """%LOCALAPPDATA%\\Open3D\\OpenScene, or OpenScene in the folder OPEN3D_DATA_DIR names; None without either."""
    return open3d_settings.app_data_dir(APP, environ)


def settings_file(name, environ=None):
    """A file of the settings folder, or None when there is no settings folder."""
    folder = settings_dir(environ)
    return None if folder is None else str(folder / name)


def data_path(name, environ=None):
    """A file or folder of the data folder, or None when there is no data folder."""
    folder = data_dir(environ)
    return None if folder is None else str(folder / name)


def write_text(path, text):
    """Writes the whole file into a new one beside it, which then takes its place, so the old one is never left
    half written. Creates its folder. Raises OSError, which the caller tells the person about."""
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(temporary)
        raise


def write_json(path, data):
    write_text(path, json.dumps(data, indent=1) + "\n")


def carry_over_plugcfg(plugcfg, environ=None):
    """Once, at start: the settings 2.x kept in this 3ds Max's plugcfg folder are copied into the settings folder
    and its HDRI previews into the data folder. Only when the new folder does not exist yet; the old files are never
    changed, moved or deleted. Returns [(what, open3d_settings.CarryOver)] for what had something to copy."""
    done = []
    new_settings = settings_dir(environ)
    old = [(f, n) for f, n in OLD_FILES.items() if plugcfg and os.path.isfile(os.path.join(plugcfg, f))]
    if new_settings is not None and old and not os.path.lexists(new_settings):
        # carry_over copies a folder: the old files, under their new names, are put in one first
        with tempfile.TemporaryDirectory(prefix="openscene-") as staging:
            for was, now in old:
                shutil.copy2(os.path.join(plugcfg, was), os.path.join(staging, now))
            done.append(("settings", open3d_settings.carry_over(staging, new_settings)))
    old_previews = os.path.join(plugcfg, OLD_HDRI_PREVIEWS) if plugcfg else None
    new_previews = data_path(HDRI_PREVIEWS, environ)
    if new_previews is not None and old_previews and os.path.isdir(old_previews):
        result = open3d_settings.carry_over(old_previews, new_previews)
        if result.kind != open3d_settings.NOTHING:
            done.append(("HDRI previews", result))
    return done


def describe(result):
    """One line for the MAXScript Listener: what carry_over did."""
    if result.kind == open3d_settings.COPIED:
        text = "copied %d files" % result.files
        if result.left_out:
            text += ", left out: " + ", ".join("%s (%s)" % (name, why) for name, why in result.left_out)
        return text
    if result.kind == open3d_settings.FAILED:
        return "not copied (%s)" % result.reason
    return "nothing to copy"
