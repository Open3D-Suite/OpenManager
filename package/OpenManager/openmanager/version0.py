# SPDX-License-Identifier: GPL-3.0-or-later
"""What OpenManager 0.x left, read by OpenManager 3: the setups it kept in a scene.

OpenManager 0.x kept a scene's setups on the root node, in the attribute OpenManager_Dat (JSON: "setups", "todo",
"rs_default" and "base"), with setups of the same shape as these: the same cards, ids and keys. They are read and
converted to setups of this version, and the original data is never written: the file keeps OpenManager_Dat as it
was, and once it is saved, the setups of this version (OpenScene_Dat) are the ones read.

What cannot be taken is left out and said: the scene state 0.x kept to put back between setups ("base"; this version
leaves the scene as the setup before left it), and the lasting IDs of nodes and layers, which 0.x wrote in an app
data slot of its own: this version finds those nodes by handle and name, and gives them its own IDs when the file is
saved.

No pymxs and no Qt: the tests load this module as it is.
"""

import json

from . import model

KEY = "OpenManager_Dat"  # the root node's attribute with the setups
MAPS_KEY = "OpenManager_Maps"  # the maps 0.x held so that 3ds Max keeps them: read, never changed
MIX_PREFIX = "OM_EnvMix"  # the maps 0.x made to mix the tabs of the Environment card
NAME = "OpenManager 0.x"

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
