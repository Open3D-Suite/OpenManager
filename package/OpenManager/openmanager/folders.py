# SPDX-License-Identifier: GPL-3.0-or-later
"""Where OpenManager keeps its files, from what every Open3D app shares (open3d_settings), and the files of the
versions before it, carried over once.

Its settings go to %APPDATA%\\Open3D\\OpenManager, one set for every 3ds Max, and everything else it writes
(the HDRI previews, the toolbar's backup, the exports of a scene not saved yet) to
%LOCALAPPDATA%\\Open3D\\OpenManager; OPEN3D_SETTINGS_DIR and OPEN3D_DATA_DIR move them. These are the folders
OpenManager 0.x used too: its files there have names of their own (version0.SETTINGS_FILES, version0.HDRI), which
are never read as this version's.

At start, before the settings are read, carry_over takes the settings of the versions before, once (the file CARRIED
says it was done): those of OpenScene 3 (its folders, named OpenScene, in the same two places), of OpenScene 2.x (the
plugcfg folder of 3ds Max) or of OpenManager 0.x (converted by version0.settings), whichever were changed last; and
the HDRI previews and the files of scenes not saved yet. No file is copied over one that is there, and every old file
is left as it was. When a copy fails, that session goes on with the old files (the settings, as they would have been
copied, from a temporary folder: never written into the old ones), and the next start tries again.

No pymxs and no Qt: the tests load this module as it is.
"""

import contextlib
import dataclasses
import json
import os
import stat
import tempfile
import time
from pathlib import Path

from . import APP, open3d_settings, version0

SETTINGS = "settings.json"  # the window: its cards, columns, theme and options
DEFAULT_LAYOUT = "default_layout.json"  # the card layout saved with Settings > Save as default
NOTIFY = "notify.txt"  # "0": don't offer to convert the setups of another scene manager
TOOLBAR_DONE = "toolbar_placed.txt"  # the first start already put the OpenManager toolbar (or found the button)
CARRIED = "carried_over.txt"  # the first start carried over the files of the versions before (or found none)
HDRI_PREVIEWS = "hdri_previews"
UNSAVED = "unsaved_scene"  # thumbnails, exports and presets of a scene that has no folder yet
TOOLBAR_BACKUP = "interface_backup"
SETTINGS_FILES = (SETTINGS, DEFAULT_LAYOUT, NOTIFY)  # what is taken from the versions before

# OpenScene 3, before it was called OpenManager: the same files, in folders called OpenScene in the same two places.
# Its toolbar's files (TOOLBAR_DONE, TOOLBAR_BACKUP) are not taken: the OpenManager toolbar is placed anew.
OPENSCENE = "OpenScene"
# What the 2.x versions of OpenScene kept in the plugcfg folder of each 3ds Max, and its name now
OLD_FILES = {"OpenScene.json": SETTINGS, "OpenScene_default.json": DEFAULT_LAYOUT, "OpenScene_notify.txt": NOTIFY}
OLD_HDRI_PREVIEWS = "OpenScene_hdri"
# What OpenManager 0.x kept in the same settings folder, and its name now
ZERO_FILES = {
    version0.SETTINGS_FILE: SETTINGS,
    version0.DEFAULT_FILE: DEFAULT_LAYOUT,
    version0.NOTIFY_FILE: NOTIFY,
}
# The folders of the data folder that are carried over, and what they hold, for the MAXScript Listener
DATA_FOLDERS = ((HDRI_PREVIEWS, "HDRI previews"), (UNSAVED, "files of scenes not saved yet"))

# This session: what is read from another folder because its copy failed ("settings", or a name of DATA_FOLDERS).
_in_use = {}


def settings_dir(environ=None):
    """%APPDATA%\\Open3D\\OpenManager, or OpenManager in the folder OPEN3D_SETTINGS_DIR names; None without either.
    In a session whose carry-over of the settings failed, the folder they are read from instead."""
    if environ is None and "settings" in _in_use:
        return _in_use["settings"]
    return open3d_settings.app_settings_dir(APP, environ)


def data_dir(environ=None):
    """%LOCALAPPDATA%\\Open3D\\OpenManager, or OpenManager in the folder OPEN3D_DATA_DIR names; None without either."""
    return open3d_settings.app_data_dir(APP, environ)


def settings_file(name, environ=None):
    """A file of the settings folder, or None when there is no settings folder."""
    folder = settings_dir(environ)
    return None if folder is None else str(folder / name)


def data_path(name, environ=None):
    """A file or folder of the data folder, or None when there is no data folder. In a session whose carry-over of
    that folder failed, the old one."""
    if environ is None and name in _in_use:
        return str(_in_use[name])
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


# ---------------------------------------------------------------- the files of the versions before


@dataclasses.dataclass
class Source:
    """A version before this one, and what of it is on this computer: `files`, {name now: old file}, and
    `folders`, {name now: old folder}. `convert(name now, bytes)` gives (bytes, notes); None copies them as they are."""

    name: str
    files: dict
    folders: dict
    convert: object = None


@dataclasses.dataclass(frozen=True)
class Carried:
    """What carry_over did. `done`: (what, the version it came from, open3d_settings.CarryOver) for each copy tried;
    `notes`: what was not taken, as lines; `in_use`: what this session reads from another folder because its copy
    failed; `finished`: nothing failed, so it is not tried again."""

    done: tuple = ()
    notes: tuple = ()
    in_use: dict = dataclasses.field(default_factory=dict)
    finished: bool = False


def sources(plugcfg=None, environ=None):
    """The versions before this one whose files are on this computer, in the order that wins a tie: OpenScene 3 (in
    the folders OPEN3D_SETTINGS_DIR and OPEN3D_DATA_DIR give), OpenScene 2.x (in `plugcfg`, the plugcfg folder of the
    3ds Max that runs), OpenManager 0.x (in this version's own folders)."""
    found = []
    old_settings = open3d_settings.app_settings_dir(OPENSCENE, environ)
    old_data = open3d_settings.app_data_dir(OPENSCENE, environ)
    found.append(
        Source(
            OPENSCENE,
            {n: old_settings / n for n in SETTINGS_FILES} if old_settings else {},
            {n: old_data / n for n, _ in DATA_FOLDERS} if old_data else {},
        )
    )
    if plugcfg:
        found.append(
            Source(
                "OpenScene 2.x",
                {now: Path(plugcfg) / was for was, now in OLD_FILES.items()},
                {HDRI_PREVIEWS: Path(plugcfg) / OLD_HDRI_PREVIEWS},
            )
        )
    settings = open3d_settings.app_settings_dir(APP, environ)
    data = open3d_settings.app_data_dir(APP, environ)
    found.append(
        Source(
            version0.NAME,
            {now: settings / was for was, now in ZERO_FILES.items()} if settings else {},
            {HDRI_PREVIEWS: data / version0.HDRI} if data else {},
            _from_version0,
        )
    )
    for source in found:
        source.files = {n: p for n, p in source.files.items() if _is_file(p)}
        source.folders = {n: p for n, p in source.folders.items() if os.path.isdir(p)}
    return [s for s in found if s.files or s.folders]


def carry_over(plugcfg=None, environ=None):
    """Once, at start, before the settings are read: the files of the versions before, into the folders of this one
    (see the top of this module). Returns a Carried; it never raises for a folder or a file."""
    settings = open3d_settings.app_settings_dir(APP, environ)
    data = open3d_settings.app_data_dir(APP, environ)
    if settings is None or _exists(settings / CARRIED):
        return Carried(finished=True)
    found = sources(plugcfg, environ)
    done, notes, in_use = [], [], {}
    with_settings = [s for s in found if s.files]
    chosen = max(with_settings, key=lambda s: (_last_change(s.files.values()), -found.index(s)), default=None)
    if chosen is not None:
        contents, left_out, said = _contents(chosen)
        notes += said
        outcome = _place(settings, contents, left_out)
        if outcome.kind == open3d_settings.FAILED:
            in_use["settings"] = _session_copy(contents)
        if outcome.kind != open3d_settings.NOTHING:
            done.append(("settings", chosen.name, outcome))
        # OpenScene 3 copied those of 2.x at its own first start: only another program's are worth a line
        notes += [
            "the settings of %s: those of %s, changed last, were taken" % (other.name, chosen.name)
            for other in with_settings
            if (other.convert is None) != (chosen.convert is None)
        ]
    for name, what in DATA_FOLDERS if data is not None else ():
        holders = [s for s in found if name in s.folders]
        source = chosen if chosen in holders else next(iter(holders), None)
        if source is None:
            continue
        outcome = open3d_settings.carry_over(source.folders[name], data / name)
        if outcome.kind == open3d_settings.FAILED:
            in_use[name] = source.folders[name]
        if outcome.kind != open3d_settings.NOTHING:
            done.append((what, source.name, outcome))
    finished = not any(outcome.kind == open3d_settings.FAILED for _, _, outcome in done)
    if finished:
        took = ", ".join("%s of %s" % (what, name) for what, name, _ in done) or "nothing"
        try:
            settings.mkdir(parents=True, exist_ok=True)
            _write_new(settings / CARRIED, ("Carried over from the versions before: %s.\n" % took).encode("utf-8"))
        except FileExistsError:
            pass  # another start of 3ds Max carried them over at the same time
        except OSError as error:
            notes.append("could not note that the files of the versions before were carried over (%s)" % error)
            finished = False
    return Carried(tuple(done), tuple(dict.fromkeys(notes)), in_use, finished)


def use(carried):
    """This session reads what carry_over could not copy from where it was."""
    _in_use.clear()
    _in_use.update({k: v for k, v in carried.in_use.items() if v is not None})


def report(carried):
    """What carry_over did, as lines for the MAXScript Listener."""
    lines = []
    for what, name, outcome in carried.done:
        line = "%s of %s: %s" % (what, name, describe(outcome))
        if outcome.kind == open3d_settings.FAILED:
            line += "; this session uses the old ones, and the next start tries again"
        elif outcome.kind == open3d_settings.COPIED:
            line += "; the old ones are left as they were"
        lines.append(line)
    return lines + ["not carried over: " + note for note in carried.notes]


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


def _from_version0(name, raw):
    """A settings file of OpenManager 0.x as this version's: its notification switch as it is, its settings through
    version0.settings. ValueError when the file is not what 0.x writes."""
    if name == NOTIFY:
        return (b"0" if raw.strip()[:1] == b"0" else b"1"), []
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError("not settings of %s (%s)" % (version0.NAME, error)) from error
    if not isinstance(data, dict):
        raise ValueError("not settings of %s" % version0.NAME)
    settings, notes = version0.settings(data)
    return (json.dumps(settings, indent=1) + "\n").encode("utf-8"), notes


def _contents(source):
    """The settings files of this version that `source` gives: ({name: bytes}, [(old file, why it was not taken)],
    notes)."""
    contents, left_out, notes = {}, [], []
    for name, path in source.files.items():
        try:
            raw = path.read_bytes()
            if source.convert is None:
                contents[name] = raw
            else:
                contents[name], said = source.convert(name, raw)
                notes += ["%s: %s" % (source.name, line) for line in said]
        except (OSError, ValueError) as error:
            left_out.append((path, str(error)))
    return contents, left_out, notes


def _place(folder, contents, left_out):
    """Puts each file of `contents` in `folder`, which it creates, unless something has its name there already.
    A CarryOver: COPIED with how many were put, NOTHING when none was, or FAILED when one could not be written."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return open3d_settings.CarryOver(open3d_settings.FAILED, reason="couldn't create %s (%s)" % (folder, error))
    placed = 0
    for name, data in contents.items():
        if _exists(folder / name):
            continue
        try:
            _write_new(folder / name, data)
        except FileExistsError:
            continue  # put there meanwhile: never written over
        except OSError as error:
            return open3d_settings.CarryOver(open3d_settings.FAILED, reason="couldn't write %s (%s)" % (name, error))
        placed += 1
    if not placed and not left_out:
        return open3d_settings.CarryOver(open3d_settings.NOTHING)
    return open3d_settings.CarryOver(open3d_settings.COPIED, files=placed, left_out=tuple(left_out))


def _write_new(path, data):
    """Writes a new file whole into a temporary one beside it, which then takes its name. FileExistsError when
    something has the name: nothing is written over."""
    temporary = path.with_name("%s.carry-%d-%d.tmp" % (path.name, os.getpid(), time.time_ns()))
    with open(temporary, "xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    try:
        if _exists(path):
            raise FileExistsError(str(path))
        os.rename(temporary, path)  # on Windows it never replaces a file that is there
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(temporary)
        raise


def _session_copy(contents):
    """A temporary folder with the settings as they would have been copied, for a session whose copy failed; None
    when even that cannot be written (the session then has the defaults)."""
    try:
        folder = Path(tempfile.mkdtemp(prefix="OpenManager-settings-"))
        for name, data in contents.items():
            (folder / name).write_bytes(data)
    except OSError:
        return None
    return folder


def _exists(path):
    """Whether something has the name `path`; when that cannot be told, it counts as there, and is never touched."""
    try:
        os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        return False
    except (OSError, ValueError):
        return True
    return True


def _is_file(path):
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except (OSError, ValueError):
        return False


def _last_change(paths):
    """When the newest of these files was changed (nanoseconds); 0 when none can be read."""
    times = []
    for path in paths:
        with contextlib.suppress(OSError, ValueError):
            times.append(os.lstat(path).st_mtime_ns)
    return max(times, default=0)
