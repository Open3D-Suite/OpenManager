# SPDX-License-Identifier: GPL-3.0-or-later
"""What OpenManager 0.x left, read by OpenManager 3: the setups it kept in a scene, and its settings.

OpenManager 0.x kept a scene's setups on the root node, in the attribute OpenManager_Dat (JSON: "setups", "todo",
"rs_default" and "base"), with setups of the same shape as these: the same cards, ids and keys. They are read and
converted to setups of this version, and the original data is never written: the file keeps OpenManager_Dat as it
was, and once it is saved, the setups of this version (OpenScene_Dat) are the ones read.

What cannot be taken is left out and said: the scene state 0.x kept to put back between setups ("base"; this version
leaves the scene as the setup before left it), and the lasting IDs of nodes and layers, which 0.x wrote in an app
data slot of its own: this version finds those nodes by handle and name, and gives them its own IDs when the file is
saved.

Its settings were in %APPDATA%\\Open3D\\OpenManager, the settings folder of this version too, under names of their
own (SETTINGS_FILE, DEFAULT_FILE, NOTIFY_FILE), with its HDRI previews in HDRI in the data folder. folders.carry_over
copies them once into this version's files, through settings(): what has the same meaning is taken, checked to be of
the right kind; the scripts 0.x trusted are trusted here too (a file by its contents now; a script by the digest 0.x
kept, in TRUSTED_CODE, until it is seen: trust.trusted_before); what has no counterpart is said. The files of 0.x
are never written.

No pymxs and no Qt: the tests load this module as it is.
"""

import copy
import json

from . import model, trust

KEY = "OpenManager_Dat"  # the root node's attribute with the setups
MAPS_KEY = "OpenManager_Maps"  # the maps 0.x held so that 3ds Max keeps them: read, never changed
MIX_PREFIX = "OM_EnvMix"  # the maps 0.x made to mix the tabs of the Environment card
NAME = "OpenManager 0.x"

SETTINGS_FILE = "OpenManager.json"  # its settings, the scripts it trusted among them
DEFAULT_FILE = "OpenManager_default.json"  # what Settings > Save as default kept
NOTIFY_FILE = "OpenManager_notify.txt"  # "0": don't offer to open the window for a file to convert
HDRI = "OpenManager_hdri"  # its HDRI previews, in the data folder; their names are those of this version
# The settings key with the scripts 0.x trusted ("code:" and the SHA-256 of their text), trusted once they are seen
TRUSTED_CODE = "openmanager0_trusted_code"

LEFT_OUT_BASE = (
    "the scene state %s kept to put back between setups (this version leaves the scene as the setup before left "
    "it)" % NAME
)


def convert(text):
    """The setups OpenManager 0.x kept in a scene, as model.decode gives setups ("setups", "todo", "rs_default",
    "problem"), and "left_out": what was not taken, for the MAXScript Listener. None when the text holds no setups
    of 0.x. The text is only read."""
    if not isinstance(text, str) or not text:
        return None
    if len(text) > model.MAX_STORED:
        return dict(model._refused("the stored setups are bigger than OpenManager reads"), left_out=[])
    if text.startswith((model.COMPRESSED_PREFIX, model.OLD_COMPRESSED_PREFIX)):
        return None  # 0.x never packed its setups
    try:
        data = json.loads(text)
    except ValueError:
        return None
    found = model.from_stored(data)
    if found is None:
        return None
    for s in found["setups"]:
        forget_ids(s)
    found["left_out"] = [LEFT_OUT_BASE] if data.get("base") else []
    return found


def forget_ids(s):
    """Takes out the lasting IDs 0.x gave the nodes and layers of a setup: they are in an app data slot of 0.x, so
    this version would take a node at its handle for another one. The handles and names stay."""
    for ref in model.node_refs(s):
        if isinstance(ref, dict):
            ref.pop("uid", None)
    s["lights"]["uids"] = {}
    for row in s["layers"]["set"]:
        row.pop("uid", None)
    for variant in s["variants"]["set"]:
        variant.pop("uids", None)
    return s


def report(found):
    """Lines for the MAXScript Listener once the setups of 0.x were converted."""
    lines = [
        "OpenManager: converted %d setup(s) that %s kept in this file (%s); they are saved as setups of this "
        "version with the file, and %s's are left as they are." % (len(found["setups"]), NAME, KEY, NAME)
    ]
    lines += ["OpenManager: not taken from %s: %s" % (NAME, what) for what in found.get("left_out") or []]
    return lines


# ---------------------------------------------------------------- settings


def _is_bool(v):
    return isinstance(v, bool)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _ints(v, n):
    return isinstance(v, list) and len(v) == n and all(_is_int(x) for x in v)


def _texts(v):
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _dict_of(v, ok):
    return isinstance(v, dict) and all(isinstance(k, str) and ok(x) for k, x in v.items())


# the settings that mean the same in both versions, and the kind each one must have
SAME = {
    "notify": _is_bool,
    "geometry": lambda v: _ints(v, 4),
    "floating": _is_bool,
    "area": _is_int,
    "visible": lambda v: isinstance(v, list) and all(_is_int(c) and c in model.CARDS for c in v),
    "columns_visible": lambda v: _dict_of(v, _is_bool),
    "column_widths": lambda v: _dict_of(v, _is_int),
    "resolution_presets": lambda v: isinstance(v, list) and all(_ints(p, 2) for p in v),
    "layouts": lambda v: _dict_of(v, lambda cards: _dict_of(cards, lambda p: _ints(p, 4))),
    "enabled_props": lambda v: _dict_of(v, _texts),
    "hdri_folders": _texts,
    "hdri_selected": _is_int,
}
# Settings > Theme and Settings > 3ds Max
THEME = {"main": ("auto", "light", "dark"), "header": ("colored", "default")}
MAX_OPTIONS = {
    "viewport_update_type": _is_int,
    "viewport_refresh": _is_bool,
    "ipr_corona_restart": _is_bool,
    "ipr_vray_resolution": _is_bool,
    "update_time_output_type": _is_bool,
    "animate_camera": _is_bool,
}
SCRIPT_POLICIES = {
    "always": "Always run them",
    "never": "Never run them",
}


def settings(data):
    """The settings of this version that those of 0.x give (`data`: OpenManager.json or OpenManager_default.json, as
    read), and what was not taken, as lines. Only what has the same meaning, and the right kind, is taken."""
    out = {k: copy.deepcopy(data[k]) for k, ok in SAME.items() if k in data and ok(data[k])}
    notes = []
    theme = data.get("theme")
    if isinstance(theme, dict):
        kept = {k: theme[k] for k, allowed in THEME.items() if theme.get(k) in allowed}
        if kept:
            out["theme"] = kept
    options = data.get("max")
    if isinstance(options, dict):
        kept = {k: options[k] for k, ok in MAX_OPTIONS.items() if k in options and ok(options[k])}
        if kept:
            out["max"] = kept
        if options.get("restore_base") is True:
            notes.append("the setting that put the scene back between setups (this version has none)")
        if options.get("scripts") in SCRIPT_POLICIES:
            notes.append(
                'the setting "%s" for the scripts and render presets of a file (this version shows them and asks '
                "first)" % SCRIPT_POLICIES[options["scripts"]]
            )
    trusted = data.get("trusted_scripts")
    if isinstance(trusted, list):
        keys = [k for k in trusted if isinstance(k, str)]
        code = [k for k in keys if k.startswith("code:")]
        if code:
            out[TRUSTED_CODE] = code
        # a file or a render preset was trusted by its path: here by its path and contents, as they are now
        paths = [k.split(":", 1)[1] for k in keys if k.startswith(("file:", "preset:"))]
        digests = [trust.file_digest(p) for p in paths]
        found = [d for d in digests if d]
        if found:
            out["trusted_code"] = trust.remember([], found)
        if len(found) < len(digests):
            notes.append(
                "%d trusted script file(s) or render preset(s) that cannot be read now: they are asked about when a "
                "setup uses them" % (len(digests) - len(found))
            )
    return out, notes
