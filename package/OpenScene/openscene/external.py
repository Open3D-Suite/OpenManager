"""Optional compatibility reader: setups that another scene manager keeps inside a .max (the SceneManager_Dat key
on the root node, base64 JSON), converted to OpenScene setups. Only reads that data, never writes it.

Nothing else depends on this module: deleting it (with its two uses in maxlink.read_setups and the check in
OpenScene_startup.ms) removes the feature.
"""
import base64
import json
import re

from .model import (DEFAULT_HEIGHT, DEFAULT_RATIO, DEFAULT_WIDTH, empty_setup, from_max, layer_entry, new_token,
                    object_entry)

KEY = "SceneManager_Dat"


def _b(v, d=None):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.lower() in ("true", "false"):
        return v.lower() == "true"
    return d


def _n(v, d):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _h(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _props_into(card, lst, out):
    for p in lst or []:
        name, cls = p.get("name"), p.get("v_class")
        if not name or not cls or p.get("value") is None:
            continue
        v = p["value"]
        if isinstance(v, str):
            b = _b(v)
            if b is not None:
                v = b
            else:
                try:
                    v = float(v)
                except ValueError:
                    pass
        if name == "progressive_timeLimit":
            v = from_max(name, _n(v, 0.0))
        out["%d|%s|%s" % (card, cls, name)] = v


def convert(data, first_id):
    """Reads the setups another scene manager keeps in SceneManager_Dat (base64 JSON). The original data is left as it is."""
    try:
        raw = base64.b64decode(data + "=" * (-len(data) % 4))
        lst = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(lst, list):
        return None
    out = []
    for i, v in enumerate(lst):
        g = lambda k: v.get(k) or {}
        s = empty_setup(first_id + i)
        s["render"] = _b(g("render").get("enabled"), True)
        c = v.get("color")
        if isinstance(c, str) and re.match(r"^#[0-9a-fA-F]{6}$", c):
            s["color"] = c.lower()
        s["scenename"] = g("scenename").get("text") or ""
        s["status"] = v.get("status") or "#WIP"
        cam = g("camera")
        s["camera"].update(enabled=_b(cam.get("enabled"), True), handle=_h(cam.get("handle")), locked=_b(cam.get("locked"), False))
        _props_into(1, cam.get("props"), s["props"])
        r = g("resolution")
        s["resolution"].update(enabled=_b(r.get("enabled"), True), width=int(_n(r.get("width"), DEFAULT_WIDTH)),
                               height=int(_n(r.get("height"), DEFAULT_HEIGHT)), ratio=_n(r.get("ratio"), DEFAULT_RATIO),
                               locked=_b(r.get("locked"), False))
        for key, card in (("sun", 3), ("dome", 4)):
            x = g(key)
            s[key].update(enabled=_b(x.get("enabled"), False), handle=_h(x.get("handle")))
            _props_into(card, x.get("props"), s["props"])
        e = g("environment")
        mat = e.get("mat") or {}
        s["environment"].update(enabled=_b(e.get("enabled"), False), cls=mat.get("class") or "", name=mat.get("name") or "")
        _props_into(6, e.get("props"), s["props"])
        f = g("frames")
        s["frames"].update(enabled=_b(f.get("enabled"), False), kind=int(_n(f.get("type"), 0)), single=int(_n(f.get("single"), 0)),
                           start=int(_n(f.get("start"), 0)), end=int(_n(f.get("end"), 100)), nth=int(_n(f.get("nth"), 1)))
        if isinstance(f.get("list"), str):
            s["frames"]["list"] = f["list"]
        s["layers"]["enabled"] = _b(g("layers").get("enabled"), False)
        for l in g("layers").get("set") or []:
            ent = layer_entry(l.get("handle") or l.get("name") or "")
            for p in l.get("props") or []:
                b = _b(p.get("value"))
                n = p.get("name")
                if b is None or n == "name":
                    continue
                key = {"on": "visible", "isfrozen": "freeze", "renderable": "render", "primaryVisibility": "vcam"}.get(n)
                if key:
                    ent[key] = b
                else:
                    ent["extra"][n] = b
            s["layers"]["set"].append(ent)
        s["objects"]["enabled"] = _b(g("objects").get("enabled"), False)
        for o in g("objects").get("set") or []:
            h = _h(o.get("handle"))
            if h is None:
                continue
            ent = object_entry(h, o.get("name") or "")
            for p in o.get("props") or []:
                b = _b(p.get("value"))
                n = p.get("name")
                if b is None or n == "name":
                    continue
                if n == "isNodeHidden":
                    ent["visible"] = not b
                elif n == "renderable":
                    ent["renderable"] = b
                else:
                    ent["extra"][n] = b
            s["objects"]["set"].append(ent)
        s["lights"]["enabled"] = _b(g("lights").get("enabled"), False)
        for l in g("lights").get("set") or []:
            h = _h(l.get("handle"))
            if h is None:
                continue
            s["lights"]["set"].append(h)
            for p in l.get("props") or []:
                if p.get("name") and p.get("name") != "name" and p.get("value") is not None:
                    s["props"]["26|%d|%s" % (h, p["name"])] = p["value"]
        rc = g("renderCustom")
        s["render_custom"]["enabled"] = _b(rc.get("enabled"), False)
        _props_into(25, rc.get("props"), s["props"])
        x = g("xrefScene")
        s["xref"]["enabled"] = _b(x.get("enabled"), False)
        for it in x.get("set") or []:
            on = True
            for p in it.get("props") or []:
                if p.get("name") == "enabled":
                    on = _b(p.get("value"), True)
            if on and it.get("name"):
                s["xref"]["set"].append(re.split(r"[\\/]", it["name"])[-1])
        o = g("output_Common")
        s["output"]["enabled"] = _b(o.get("enabled"), False)
        s["output"]["project_path"] = o.get("projectPath") or ""
        toks = []
        for t in o.get("preset") or []:
            tok = new_token(t.get("type") or "Text")
            if isinstance(t.get("value"), str):
                tok["value"] = t["value"]
            elif isinstance(t.get("value"), (int, float)):
                tok["value"] = str(int(t["value"]))
            if isinstance(t.get("settings"), int):
                tok["digits"] = t["settings"]
            tok["folder"] = bool(t.get("folder"))
            toks.append(tok)
        if toks:
            s["output"]["preset"] = toks
        s["notes"] = g("notes").get("text") or ""
        out.append(s)
    return out
