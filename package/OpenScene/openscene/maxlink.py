# SPDX-License-Identifier: GPL-3.0-or-later
"""Everything that talks to 3ds Max: reading the scene, applying a setup, storing setups, rendering."""

import json
import os
import tempfile

import pymxs
from pymxs import runtime as rt

from . import external, model

# What a call into 3ds Max raises through pymxs: a MAXScript error comes as RuntimeError; a renderer or a property
# this 3ds Max does not have, as AttributeError or TypeError; a value it cannot take, as ValueError.
MAX_ERRORS = (RuntimeError, AttributeError, TypeError, ValueError)

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(os.path.dirname(HERE), "openscene_core.ms")
DATA_KEY = "OpenScene_Dat"


def load_core():
    rt.fileIn(CORE)


def _none(v):
    return -1 if v is None else int(v)


# ---------------------------------------------------------------- scene


class Scene(object):
    def __init__(self, data=None):
        d = data or {}
        self.file = d.get("file", "")
        self.folder = d.get("folder", "")
        self.output_dir = d.get("output_dir", "")
        self.engine = d.get("engine", "")
        self.width = d.get("width", 1920)
        self.height = d.get("height", 1080)
        self.active_camera = d.get("active_camera")
        self.env_name = d.get("env_name")
        self.env_class = d.get("env_class")
        self.cameras = d.get("cameras", [])
        self.lights = d.get("lights", [])
        self.maps = d.get("maps", [])
        self.layers = d.get("layers", [])
        self.objects = d.get("objects", [])
        self.object_total = d.get("object_total", len(self.objects))
        self.xrefs = d.get("xrefs", [])
        self._cam = {c["handle"]: c for c in self.cameras}
        self._light = {light["handle"]: light for light in self.lights}
        self._obj = {o["handle"]: o for o in self.objects}

    @property
    def engine_id(self):
        return model.engine_id(self.engine)

    def camera(self, h):
        return self._cam.get(h)

    def light(self, h):
        return self._light.get(h)

    def obj(self, h):
        return self._obj.get(h)

    def add_objects(self, items):
        """Objects read later (the selection added to a setup): known from now on."""
        for o in items:
            if o["handle"] not in self._obj:
                self.objects.append(o)
            self._obj[o["handle"]] = o

    def map(self, cls, name):
        for m in self.maps:
            if m["class"] == cls and m["name"] == name:
                return m
        return None

    def env_is_mix(self):
        return bool(self.env_name) and str(self.env_name).startswith("OSCN_EnvMix")

    def offered_maps(self, keep=None):
        """Maps of the Environment list: what it offers, plus the ones in `keep` so a choice never disappears."""
        keep = keep or []
        return [m for m in self.maps if m.get("offer", True) or (m["class"], m["name"]) in keep]

    def suns(self):
        return [light for light in self.lights if light["kind"] == "sun"]

    def domes(self):
        return [light for light in self.lights if light["kind"] == "dome"]

    def other_lights(self):
        return [light for light in self.lights if light["kind"] == "light"]

    def find_by_name(self, items, name):
        for it in items:
            if it["name"] == name:
                return it
        return None


def read_scene_raw(handles=None):
    """The scene as JSON text; objects only for `handles` (the ones the setups use)."""
    try:
        rt.oscn_sceneRead()  # the next #scene event goes to Python again
    except MAX_ERRORS:
        pass
    return str(rt.oscn_scene(objHandles=sorted(int(h) for h in (handles or []))))


def parse_scene(raw):
    return json.loads(raw, strict=False)  # a stray control character in a name must not stop the read


def nodes_info(handles):
    """Name, layer and visibility of these geometry / shape nodes (the others are left out)."""
    if not handles:
        return []
    return json.loads(str(rt.oscn_nodesInfo([int(h) for h in handles])), strict=False)


def resolve(setup, scene):
    """Handles change when a scene is merged or nodes are re-created: fall back to the stored name."""
    for key, items in (("camera", scene.cameras), ("sun", scene.lights), ("dome", scene.lights)):
        for c in model.entries(setup[key]):
            h = c.get("handle")
            found = None
            if h is not None:
                found = next((x for x in items if x["handle"] == h), None)
            if found is None and c.get("name"):
                found = scene.find_by_name(items, c["name"])
                if found is not None:
                    c["handle"] = found["handle"]
            if found is not None:
                c["name"] = found["name"]


# ---------------------------------------------------------------- values


def _value(prop, v):
    """Stored value -> what the change list carries (hashable). Colors, maps and tone-mapping
    chains travel as tagged tuples and become 3ds Max objects only when applied."""
    cls = prop.get("class")
    name = prop["name"]
    if cls == "Color":
        return ("$color", str(v or "#000000"))
    if cls == "Texturemap":
        return ("$texmap", str(v or ""))
    if cls == "Pipeline":
        return ("$pipeline", v if isinstance(v, str) else json.dumps(v or []))
    if cls == "Date":
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0
    if isinstance(v, bool) or cls == "BooleanClass":
        return bool(v)
    if cls == "Integer" or name == "progressive_timeLimit":
        try:
            return int(round(model.to_max(name, float(v))))
        except (TypeError, ValueError):
            return 0
    if cls == "Float":
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0
    return v if isinstance(v, str) else str(v)


def _to_max(v):
    if isinstance(v, tuple) and v and v[0] == "$color":
        c = v[1].lstrip("#")
        try:
            return rt.Color(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
        except ValueError:
            return rt.Color(0, 0, 0)
    if isinstance(v, tuple) and v and v[0] == "$texmap":
        if not v[1] or "|" not in v[1]:
            return None
        cls, name = v[1].split("|", 1)
        return rt.oscn_findTexmap(cls, name)
    return v


# ---------------------------------------------------------------- tone-mapping chains (Corona colour mapping operators)


def read_pipeline(obj, prop):
    """The chain of operators in obj.prop as a list of {"class", "props"} (texture inputs are left out)."""
    out = []
    try:
        op = rt.getProperty(obj, prop)
    except MAX_ERRORS:
        return out
    guard = 0
    while op is not None and guard < 64:
        guard += 1
        item = {"class": str(rt.classOf(op)), "props": {}}
        nxt = None
        for n in rt.getPropNames(op):
            n = str(n)
            try:
                v = rt.getProperty(op, n)
            except MAX_ERRORS:
                continue
            if n.endswith("_nextOperator"):
                nxt = v
                continue
            if isinstance(v, bool) or isinstance(v, (int, float)) or isinstance(v, str):
                item["props"][n] = v
            elif str(rt.classOf(v)) == "Color":
                item["props"][n] = {"$color": [float(v.r), float(v.g), float(v.b)]}
        out.append(item)
        op = nxt
    return out


def new_operator(cls):
    """A new Corona colour-mapping operator of this class, or None: the class name comes from a setup, so it must be
    an operator's plain name, and it is looked up among 3ds Max's classes, never run as code."""
    if not model.is_tone_operator(cls):
        print("OpenScene: refused a tone-mapping operator of class %r (not an operator's name)" % (cls,))
        return None
    c = getattr(rt, cls, None)
    if c is None or str(rt.classOf(c)) != "MAXClass":
        print("OpenScene: this 3ds Max has no tone-mapping operator %s" % cls)
        return None
    return c()


def set_operator_props(op, cls, props):
    """The values a setup stores for an operator: plain names and plain values only, never the link to the next one."""
    for n, v in (props or {}).items():
        if not model.is_plain_name(n) or n.endswith("_nextOperator"):
            print("OpenScene: refused the setting %r of a %s" % (n, cls))
            continue
        if isinstance(v, dict) and "$color" in v:
            try:
                v = rt.Color(*[float(x) for x in v["$color"]][:3])
            except (TypeError, ValueError):
                continue
        elif not model.is_scalar(v):
            continue
        try:
            rt.setProperty(op, n, v)
        except Exception as ex:  # noqa: BLE001 - one setting 3ds Max refuses must not stop the others; said here
            print("OpenScene: %s.%s -> %s" % (cls, n, ex))


def write_pipeline(obj, prop, chain):
    first = None
    prev = None
    for item in chain:
        op = new_operator(item.get("class"))
        if op is None:
            continue
        set_operator_props(op, item["class"], item.get("props"))
        if prev is not None:
            try:
                rt.setProperty(prev, "colorMappingOperator_nextOperator", op)
            except MAX_ERRORS:
                pass
        first = first or op
        prev = op
    rt.setProperty(obj, prop, first)


# ---------------------------------------------------------------- Post-Production / VFB (Corona)


def _live_operators():
    ops = []
    op = rt.getProperty(rt.renderers.current, "colorMap_pipeline")
    guard = 0
    while op is not None and guard < 64:
        guard += 1
        ops.append(op)
        op = rt.getProperty(op, "colorMappingOperator_nextOperator")
    return ops


def read_post(key, only_active=False):
    """One category of the VFB as it is now, or None when `only_active` and it is off. Tone mapping: the operators
    that are on, each with its values. The others: their renderer settings."""
    r = rt.renderers.current
    if key == "tonemap":
        ops = []
        for item in read_pipeline(r, "colorMap_pipeline"):
            props = {n: v for n, v in item["props"].items() if not n.endswith("_id")}
            if props.get("colorMappingOperator_enabled", True):
                ops.append({"class": item["class"], "props": props})
        return {"ops": ops}
    if key == "lightmix":
        arrays = {}
        for name in (
            "colorMap_lightmixIntensities",
            "colorMap_lightmixColors",
            "colorMap_lightmixEnabledLayers",
            "colormap_lightselect_elementNames",
        ):
            try:
                vals = list(rt.getProperty(r, name) or [])
            except MAX_ERRORS:
                continue
            if name == "colorMap_lightmixColors":
                vals = [[float(c.r), float(c.g), float(c.b)] for c in vals]
            elif name == "colormap_lightselect_elementNames":
                vals = [str(x) for x in vals]
            arrays[name] = vals
        if only_active and not arrays.get("colorMap_lightmixIntensities"):
            return None
        return {"arrays": arrays}
    names = next((n for k, _, n in model.POST_CATS if k == key), [])
    props = {}
    for n in names:
        v = rt.oscn_getRS(n)
        if not (isinstance(v, str) and v == "<none>"):
            props[n] = v
    if only_active:
        switches = [
            n
            for n in names
            if isinstance(props.get(n), bool) and n.endswith(("_enabled", "_enable", "_on", "_blendEnabled"))
        ]
        if not any(props.get(n) for n in switches):
            return None
    return {"props": props} if props else None


def apply_tone(chain):
    """Sets the stored values on the operators of the VFB in place, so everything else about them stays (curves, LUT
    file...). An operator not in the setup is switched off; one the VFB doesn't have is added at the end."""
    live = _live_operators()
    used = []
    for item in chain:
        op = next((o for o in live if str(rt.classOf(o)) == item["class"] and o not in used), None)
        if op is None:
            op = new_operator(item.get("class"))
            if op is None:
                continue
            if live:
                rt.setProperty(live[-1], "colorMappingOperator_nextOperator", op)
            else:
                rt.setProperty(rt.renderers.current, "colorMap_pipeline", op)
            live.append(op)
        used.append(op)
        set_operator_props(op, item["class"], item.get("props"))
    for op in live:
        if op not in used:
            try:
                rt.setProperty(op, "colorMappingOperator_enabled", False)
            except MAX_ERRORS:
                pass


def apply_lightmix(arrays):
    r = rt.renderers.current
    for name, vals in arrays.items():
        if name not in model.LIGHTMIX_ARRAYS or not isinstance(vals, list):
            if name != "colormap_lightselect_elementNames":
                print("OpenScene: refused the LightMix setting %r" % (name,))
            continue
        if name == "colorMap_lightmixColors":
            vals = [rt.Color(*c) for c in vals]
        try:
            rt.setProperty(r, name, vals)
        except MAX_ERRORS as ex:
            print("OpenScene: %s -> %s" % (name, ex))


# ---------------------------------------------------------------- what a setup does


def actions(s, scene, enabled, output_path, rendering, opts=None, rs_default=None, refused=None):
    """The list of changes a setup makes, in order. `enabled(card)` gives the ticked (tab, prop) pairs.
    opts: settings of the window (viewport mode, time output type...). What the setup carries that a setup may not
    set (a name that is not a plain name...) is left out and named in `refused`, when it is a list."""
    opts = opts or {}
    out = []
    props = s.get("props", {})
    refused = refused if refused is not None else []

    def stored(card, tab, p):
        return props.get("%d|%s|%s" % (card, tab["v_class"], p["name"]))

    sn = s.get("snippet", {})
    if sn.get("enabled") and sn.get("pre_setup", "").strip():
        out.append(("code", sn["pre_setup"]))
    rp = s.get("render_preset", {})
    if rp.get("enabled") and rp.get("path"):
        out.append(("preset", rp["path"]))
    ro = s.get("rs_override", {})
    over = ro.get("set") if isinstance(ro.get("set"), dict) else {}
    if ro.get("enabled") and (rs_default or over):
        for k, v in sorted((rs_default or {}).items()):
            if k not in over and model.renderer_value_ok(k, v):
                out.append(("rs", k, v))
        for k, v in sorted(over.items()):
            if model.renderer_value_ok(k, v):
                out.append(("rs", k, v))
            else:
                refused.append("Render Override: %s" % (k,))
    f = s["frames"]
    if f["enabled"]:
        out.append(
            (
                "time",
                int(f["kind"]),
                int(f["single"]),
                int(f["start"]),
                int(f["end"]),
                max(1, int(f["nth"])),
                f["list"],
                bool(rendering or opts.get("update_time_output_type")),
            )
        )
    if s["render_custom"]["enabled"]:
        for t, p in enabled(25):
            v = stored(25, t, p)
            if v is not None:
                out.append(("rs", p["name"], _value(p, v)))
    if rendering:
        out.append(("renderview",))
    c = s["camera"]
    if c["enabled"] and c.get("handle") is not None:
        out.append(
            ("camera", c["handle"], bool(c["locked"]), 2 if rendering else int(opts.get("viewport_update_type", 0)))
        )
        cam = scene.camera(c["handle"])
        cls = cam["class"] if cam else None
        for t, p in enabled(1):
            if model.tab_matches(t, cls):
                v = stored(1, t, p)
                if v is not None:
                    out.append(("node", c["handle"], p["name"], _value(p, v)))
    r = s["resolution"]
    if r["enabled"]:
        out.append(("res", int(r["width"]), int(r["height"])))
    sun = s["sun"]
    if sun["enabled"]:
        suns = model.entries(sun)
        # the suns of the scene go in too: a sun added later is switched off as soon as the scene is read again
        out.append(
            (
                "sun",
                tuple(int(x["handle"]) for x in suns if x.get("handle") is not None),
                tuple(sorted(int(light["handle"]) for light in scene.suns())),
            )
        )
        for i, en in enumerate(suns):
            h = en.get("handle")
            if h is None:
                continue
            light = scene.light(h)
            store = props if i == 0 else en.get("props", {})
            classes = model.light_tabs_classes(light)
            for t, p in enabled(3):
                if any(model.tab_matches(t, c) for c in classes):
                    v = store.get("3|%s|%s" % (t["v_class"], p["name"]))
                    if v is not None:
                        out.append(("node", h, model.light_prop(light, t, p), _value(p, v)))
    dome = s["dome"]
    if dome["enabled"]:
        out.append(
            (
                "dome",
                (int(dome["handle"]),) if dome.get("handle") is not None else (),
                tuple(sorted(int(light["handle"]) for light in scene.domes())),
            )
        )
        if dome.get("handle") is not None:
            light = scene.light(dome["handle"])
            cls = light["class"] if light else None
            for t, p in enabled(4):
                if model.tab_matches(t, cls):
                    v = stored(4, t, p)
                    if v is not None:
                        out.append(("node", dome["handle"], p["name"], _value(p, v)))
    e = s["environment"]
    if e["enabled"]:
        m = scene.map(e.get("cls"), e.get("name")) if e.get("cls") else None
        if model.env_mixing(e, scene.engine_id):
            out.append(("envmix", model.env_mix_items(e, scene.map)))
        elif m:
            sun_h = sun.get("handle") if (sun["enabled"] and m["class"] in model.SKY_CLASSES) else None
            out.append(("env", m["class"], m["name"], _none(sun_h)))
        else:
            out.append(("envoff",))
        # 3ds Max has one environment slot: the tabs are mixed in it (Corona), else the first tab goes in it and the
        # others keep their settings up to date
        for i, en in enumerate(model.entries(e)):
            mm = scene.map(en.get("cls"), en.get("name")) if en.get("cls") else None
            if not mm:
                continue
            store = props if i == 0 else en.get("props", {})
            for _tab, p, link, key_cls in model.env_rows(mm, enabled(6)):
                v = store.get("6|%s|%s" % (key_cls, p["name"]))
                if v is not None:
                    out.append(("map", link["class"], link["name"], p["name"], _value(p, v)))
    bg = s.get("background", {})
    if bg.get("enabled") and int(bg.get("type", 0)) > 0:
        out.append(("background", int(bg["type"]), bg.get("path", "")))
    if output_path is not None:
        if output_path and rendering:
            out.append(("mkdir", output_path))
        out.append(("output", output_path))
    if s["layers"]["enabled"]:
        for layer in s["layers"]["set"]:
            for _, p in enabled(14):
                if p["class"] != "BooleanClass":
                    continue
                n = p["name"]
                if n == "on":
                    v = layer["visible"]
                elif n == "isfrozen":
                    v = layer["freeze"]
                elif n == "renderable":
                    v = layer["render"]
                elif n == "primaryVisibility":
                    v = layer["vcam"]
                elif n in layer.get("extra", {}):
                    v = layer["extra"][n]
                else:
                    continue
                out.append(("layer", layer["name"], n, bool(v)))
    if s["objects"]["enabled"]:
        for o in s["objects"]["set"]:
            for _, p in enabled(23):
                if p["class"] != "BooleanClass":
                    continue
                n = p["name"]
                if n == "isNodeHidden":
                    v = not o["visible"]
                elif n == "renderable":
                    v = o["renderable"]
                elif n in o.get("extra", {}):
                    v = o["extra"][n]
                else:
                    continue
                # isNodeHidden can only be read in 3ds Max; hiding is written through isHidden
                out.append(("node", o["handle"], "isHidden" if n == "isNodeHidden" else n, bool(v)))
    if s["lights"]["enabled"]:
        for h in s["lights"]["set"]:
            for _, p in enabled(26):
                if p["class"] in ("String", "Matrix3"):
                    continue
                v = props.get("26|%s|%s" % (h, p["name"]))
                if v is not None:
                    out.append(("node", h, p["name"], _value(p, v)))
    at = s.get("atmosphere", {})
    if at.get("enabled"):
        for a in at.get("set", []):
            out.append(("atmos", a["name"], bool(a.get("active", True))))
    va = s.get("variants", {})
    if va.get("enabled"):
        for vs in va.get("set", []):
            pick = int(vs.get("value", 1))
            for i, name in enumerate(vs.get("layers", [])):
                out.append(("layer", name, "on", i + 1 == pick))
    el = s.get("elements", {})
    if el.get("enabled"):
        for x in el.get("set", []):
            out.append(("element", x["name"], bool(x.get("enabled", True))))
    po = s.get("post", {})
    if po.get("enabled"):
        cats = po.get("cats") or {}
        if cats:
            for key in model.POST_ORDER:
                c = cats.get(key)
                if not c:
                    continue
                if key == "tonemap":
                    out.append(("posttone", json.dumps(c.get("ops", []), sort_keys=True)))
                elif key == "lightmix":
                    out.append(("postlm", json.dumps(c.get("arrays", {}), sort_keys=True)))
                else:
                    for k, v in sorted(c.get("props", {}).items()):
                        if model.post_setting_ok(key, k) and model.is_scalar(v):
                            out.append(("rs", k, v))
                        else:
                            refused.append("Post-Production: %s" % (k,))
        elif po.get("conf") or po.get("lightmix"):  # stored by an older version
            out.append(("post", po.get("conf", ""), json.dumps(po.get("lightmix") or {}, sort_keys=True)))
    if s["xref"]["enabled"]:
        on = set(s["xref"]["set"])
        for x in scene.xrefs:
            out.append(("xref", x["file"], x["file"] in on))
    sc = s.get("scripts", {})
    pre = sc["pre_render"]["path"] if sc.get("enabled") and sc.get("pre_render", {}).get("enabled") else ""
    post = sc["post_render"]["path"] if sc.get("enabled") and sc.get("post_render", {}).get("enabled") else ""
    pre_code = sn.get("pre_render", "") if sn.get("enabled") else ""
    post_code = sn.get("post_render", "") if sn.get("enabled") else ""
    out.append(("renderscripts", pre or "", post or "", pre_code or "", post_code or ""))
    if sn.get("enabled") and sn.get("post_setup", "").strip():
        out.append(("code", sn["post_setup"]))
    return out


def run(acts, redraw=True):
    """Applies a list of changes in one go, without filling the undo stack."""
    if not acts:
        return
    dialog_open = False
    try:
        dialog_open = bool(rt.renderSceneDialog.isOpen())
        if dialog_open:
            rt.renderSceneDialog.commit()
    except MAX_ERRORS:
        pass
    with pymxs.undo(False):
        for a in acts:
            try:
                _run_one(a)
            except Exception as ex:  # noqa: BLE001 - one bad setting must not stop the rest; it is printed in the Listener
                print("OpenScene: %s -> %s" % (str(a)[:160], ex))
    if dialog_open:
        try:
            rt.renderSceneDialog.update()
        except MAX_ERRORS:
            pass
    if redraw:
        rt.redrawViews()


def _node_prop(h, prop, v):
    if isinstance(v, tuple) and v and v[0] == "$pipeline":
        n = rt.maxOps.getNodeByHandle(h)
        if n is not None:
            write_pipeline(n, prop, json.loads(v[1]) if v[1] else [])
        return
    rt.oscn_setNode(h, prop, _to_max(v))


def _run_one(a):
    k = a[0]
    if k == "time":
        rt.oscn_setTime(a[1], a[2], a[3], a[4], a[5], a[6], setType=a[7])
    elif k == "rs":
        rt.oscn_setRS(a[1], _to_max(a[2]))
    elif k == "renderview":
        rt.oscn_renderView()
    elif k == "camera":
        rt.oscn_setCamera(a[1], a[2], mode=a[3])
    elif k == "node":
        _node_prop(a[1], a[2], a[3])
    elif k == "res":
        rt.oscn_setRes(a[1], a[2])
    elif k == "sun":
        rt.oscn_setLights(False, list(a[1]))
    elif k == "dome":
        rt.oscn_setLights(True, list(a[1]))
    elif k == "env":
        rt.oscn_setEnv(a[1], a[2], a[3])
    elif k == "envmix":
        rt.oscn_setEnvMix([[c, n, float(amt)] for c, n, amt in a[1]])
    elif k == "envoff":
        rt.oscn_envOff()
    elif k == "mkdir":
        rt.oscn_makeDir(a[1])
    elif k == "output":
        rt.oscn_setOutput(a[1])
    elif k == "layer":
        rt.oscn_setLayer(a[1], a[2], a[3])
    elif k == "map":
        rt.oscn_setMap(a[1], a[2], a[3], _to_max(a[4]))
    elif k == "xref":
        rt.oscn_setXref(a[1], a[2])
    elif k == "background":
        rt.oscn_setBackground(a[1], a[2])
    elif k == "atmos":
        rt.oscn_setAtmos(a[1], a[2])
    elif k == "element":
        rt.oscn_setElement(a[1], a[2])
    elif k == "preset":
        rt.oscn_loadPreset(a[1])
    elif k == "post":
        if a[1]:
            path = os.path.join(tempfile.gettempdir(), "oscn_post.conf")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(a[1])
            rt.oscn_postLoad(path)
        lm = json.loads(a[2]) if a[2] else {}
        apply_lightmix(lm if isinstance(lm, dict) else {})
    elif k == "posttone":
        apply_tone(json.loads(a[1]))
    elif k == "postlm":
        apply_lightmix(json.loads(a[1]))
    elif k == "renderscripts":
        rt.oscn_setRenderScripts(a[1], a[2], a[3], a[4])
    elif k == "code":
        rt.oscn_runCode(a[1])


def read_value(kind, a, b, c=None):
    """Current value in the scene, or None. kind: node / map / rs."""
    if kind == "node":
        v = rt.oscn_getNode(a, b)
    elif kind == "map":
        v = rt.oscn_getMap(a, b, c)
    else:
        v = rt.oscn_getRS(a)
    if isinstance(v, str) and v == "<none>":
        return None
    return v


def read_special(kind, a, prop, cls):
    """Colors, maps and tone-mapping chains read from a node (kind node) or the renderer."""
    try:
        obj = rt.maxOps.getNodeByHandle(a) if kind == "node" else rt.renderers.current
        if obj is None:
            return None
        if cls == "Pipeline":
            return json.dumps(read_pipeline(obj, prop))
        v = rt.getProperty(obj, prop)
        if cls == "Color":
            return "#%02x%02x%02x" % (int(v.r), int(v.g), int(v.b))
        if cls == "Texturemap":
            return "" if v is None else "%s|%s" % (rt.classOf(v), v.name)
    except MAX_ERRORS:
        return None
    return None


def texmaps():
    return [x for x in str(rt.oscn_texmaps()).splitlines() if "|" in x]


# ---------------------------------------------------------------- storage inside the .max file


def save_setups(text):
    rt.oscn_saveSetups(text)


def read_setups(first_id):
    """Our own setups (also those saved before 2.0.0, under an old key), else the ones another scene manager saved
    in this file (converted, not changed)."""
    ours = model.decode(rt.oscn_readKey(rt.Name(DATA_KEY)))
    if ours is not None:
        return ours, "ours"
    old = model.decode(str(rt.oscn_readOldSetups()))
    if old is not None:
        rt.oscn_renameOldMixMaps()
        return old, "legacy"
    other = rt.oscn_readKey(rt.Name(external.KEY))
    if other and len(other) > 25:
        conv = external.convert(other, first_id)
        if conv:
            return {"setups": conv, "todo": [], "rs_default": {}}, "external"
    return {"setups": [], "todo": [], "rs_default": {}}, "none"


# ---------------------------------------------------------------- module helpers


def atmospherics():
    return json.loads(str(rt.oscn_atmospherics()))


def elements():
    return json.loads(str(rt.oscn_elements()))


def rs_snapshot():
    return json.loads(str(rt.oscn_rsSnapshot()))


def save_preset(path):
    return bool(rt.oscn_savePreset(path))


def run_code(code):
    rt.oscn_runCode(code)


def snapshot_viewport(path):
    return bool(rt.oscn_snapshotViewport(path))


def snapshot_vfb(path):
    return bool(rt.oscn_snapshotVfb(path))


def batch_view(cam, name, state, preset, out, w, h):
    return bool(rt.oscn_batchView(cam, name, state, preset, out, w, h))


def interactive_running():
    try:
        return int(rt.oscn_isRendering()) != 0
    except MAX_ERRORS:
        return False


def interactive_stop():
    try:
        rt.CoronaRenderer.CoronaFp.stopRender()
    except MAX_ERRORS:
        pass


def interactive_start():
    try:
        rt.CoronaRenderer.CoronaFp.startInteractive()
    except MAX_ERRORS:
        pass


def viewport_camera():
    try:
        c = rt.viewport.getCamera()
        return None if c is None else int(c.inode.handle)
    except MAX_ERRORS:
        return None


def save_copy(path):
    rt.saveMaxFile(path, quiet=True, useNewFile=False)


# ---------------------------------------------------------------- misc


def new_hdri(path):
    return json.loads(str(rt.oscn_newHdri(path)))


def use_hdri(path, cls, name):
    """The map an environment uses for this file (already in the scene, or new)."""
    return json.loads(str(rt.oscn_useHdri(path, cls or "", name or "")))


def set_environment(cls, name):
    return bool(rt.oscn_setEnv(cls, name, -1))


def new_sky():
    return json.loads(str(rt.oscn_newSky()))


def show_in_medit(cls, name):
    return bool(rt.oscn_showInMedit(cls, name))


def selected_layers():
    return [str(x) for x in rt.oscn_selectedLayers()]


def new_camera():
    with pymxs.undo(True, "OpenScene new camera"):
        return int(rt.oscn_newCamera())


def selected_handles():
    return [int(h) for h in rt.oscn_selectedHandles()]


def select_handles(hs):
    rt.oscn_selectHandles(list(hs))


def render():
    return str(rt.oscn_render())


def stop_render():
    rt.oscn_stop()


def canceled():
    return bool(rt.oscn_cancel)


def watch(callback):
    if callback is None:
        rt.oscn_watch(False)
        rt.oscn_notify = None
    else:
        rt.oscn_notify = callback
        rt.oscn_watch(True)


def main_window():
    try:
        import qtmax

        return qtmax.GetQMaxMainWindow()
    except (ImportError, AttributeError, RuntimeError):
        return None


def hdri_preview(src, dst, w=300, h=150):
    """A .jpg picture of an HDRI read by 3ds Max (for HDRIs without a picture next to them)."""
    d = os.path.dirname(dst)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    return bool(rt.oscn_hdriPreview(src, dst, w, h))
