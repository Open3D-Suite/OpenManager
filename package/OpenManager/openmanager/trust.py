# SPDX-License-Identifier: GPL-3.0-or-later
"""Scripts and render presets that a setup runs, and which of them this computer trusts.

A setup lives inside a .max file, and a .max file can come from anyone. What a setup can run (the MAXScript of the
Script Editor card, the files of the Script File card, the render preset of the Render Preset card) runs only once
this computer trusts it: it was written or chosen in this computer's own OpenManager window, or the person said yes
when OpenManager showed it. Trust is kept as a digest of the exact text (and, for a file, of its path and its
contents), so a script changed afterwards, here or by someone else, is asked about again.

No pymxs and no Qt: the tests load this module as it is.
"""

import hashlib
import os

MAX_TRUSTED = 500  # digests kept in the settings; the oldest go first
MAX_FILE = 16 * 1024 * 1024  # a script or preset bigger than this is never run

# the actions of maxlink.actions that run something: ("code", text), ("preset", path),
# ("renderscripts", pre file, post file, pre code, post code)
SNIPPET_TITLES = {
    "pre_setup": "Pre-Setup script",
    "post_setup": "Post-Setup script",
    "pre_render": "Pre-Render script",
    "post_render": "Post-Render script",
}


def code_digest(text):
    return hashlib.sha256(("code\0" + text).encode("utf-8")).hexdigest()


def old_code_key(text):
    """What OpenManager 0.x kept for a script it trusted: "code:" and the SHA-256 of its exact text."""
    return "code:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_digest(path):
    """The digest of a file's path and contents, or None when it cannot be read (it will not run then either)."""
    try:
        if os.path.getsize(path) > MAX_FILE:
            return None
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    h = hashlib.sha256(b"file\0" + os.path.normcase(os.path.abspath(path)).encode("utf-8") + b"\0")
    h.update(data)
    return h.hexdigest()


class Item:
    """One thing a setup would run: what it is (shown to the person), its digest and a short look at it; for a
    script, the key OpenManager 0.x kept when it trusted it (old_key)."""

    def __init__(self, title, digest, preview, old_key=None):
        self.title = title
        self.digest = digest
        self.preview = preview
        self.old_key = old_key

    def __repr__(self):
        return "Item(%r)" % self.title


def _code_preview(text):
    lines = [x for x in text.strip().splitlines() if x.strip()]
    head = lines[0].strip() if lines else ""
    if len(head) > 80:
        head = head[:77] + "..."
    more = " (+%d more lines)" % (len(lines) - 1) if len(lines) > 1 else ""
    return head + more


def items(acts):
    """What these actions would run, one Item each (code that is only blank runs nothing and is left out)."""
    out = []

    def code(title, text):
        if text and text.strip():
            out.append(Item(title, code_digest(text), _code_preview(text), old_code_key(text)))

    def a_file(title, path):
        if path:
            out.append(Item(title, file_digest(path), path))

    for a in acts:
        if a[0] == "code":
            code("Script (Script Editor card)", a[1])
        elif a[0] == "preset":
            a_file("Render preset", a[1])
        elif a[0] == "renderscripts":
            a_file("Pre-Render script file", a[1])
            a_file("Post-Render script file", a[2])
            code(SNIPPET_TITLES["pre_render"], a[3])
            code(SNIPPET_TITLES["post_render"], a[4])
    return out


def allowed_actions(acts, ok):
    """The actions with what may not run taken out: `ok(digest)` says whether a digest may run. A file that cannot be
    read has no digest and never runs. Returns (actions, the Items left out)."""
    out, left_out = [], []

    def keep_code(text):
        if not text or not text.strip():
            return text
        if ok(code_digest(text)):
            return text
        left_out.append(Item("script", code_digest(text), _code_preview(text)))
        return ""

    def keep_file(path):
        if not path:
            return path
        d = file_digest(path)
        if d is not None and ok(d):
            return path
        left_out.append(Item("file", d, path))
        return ""

    for a in acts:
        if a[0] == "code":
            if keep_code(a[1]):
                out.append(a)
        elif a[0] == "preset":
            if keep_file(a[1]):
                out.append(a)
        elif a[0] == "renderscripts":
            out.append(("renderscripts", keep_file(a[1]), keep_file(a[2]), keep_code(a[3]), keep_code(a[4])))
        else:
            out.append(a)
    return out, left_out


def trusted_before(found, old_keys):
    """The digests of the Items `found` that OpenManager 0.x trusted on this computer, by the keys it kept
    (`old_keys`, carried over with its settings): they are trusted here too."""
    keys = {k for k in old_keys if isinstance(k, str)} if isinstance(old_keys, list) else set()
    return [it.digest for it in found if it.old_key and it.old_key in keys and it.digest]


def remember(trusted, digests):
    """The trusted digests with these added at the end (the newest last), at most MAX_TRUSTED."""
    out = [d for d in trusted if d not in digests]
    out += [d for d in dict.fromkeys(digests) if d]
    return out[-MAX_TRUSTED:]


def question(pending):
    """The text of the review question for these Items."""
    lines = ["• %s: %s" % (it.title, it.preview) for it in pending[:12]]
    if len(pending) > 12:
        lines.append("• ...and %d more" % (len(pending) - 12))
    presets = any(it.title == "Render preset" for it in pending)
    return (
        "The setups of this file run scripts or render presets that were not written or chosen in OpenManager on this "
        "computer:\n\n%s\n\nA script can do anything 3ds Max can do. Run them only if you trust where this file comes "
        "from.%s\n\nRun them?"
        % (
            "\n".join(lines),
            " A render preset brings render settings only: the scripts of Render Setup are left as they are."
            if presets
            else "",
        )
    )
