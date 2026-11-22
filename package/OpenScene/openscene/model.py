"""Setups, the property table and the render-output path builder.

Pure Python (no 3ds Max, no Qt) so it can be tested on its own.
"""
import base64
import copy
import datetime
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_RATIO = 1.778
DEFAULT_FRAME_LIST = "1,3,5-12"
DEFAULT_DATE_FORMAT = "YYYYMMDD"

RESOLUTION_PRESETS = [
    (320, 240), (720, 486), (640, 480), (800, 600), (1280, 720),
    (1920, 1080), (2560, 1440), (3840, 2160), (5120, 2880), (7680, 4320),
]
EXTENSIONS = [".jpg", ".png", ".tif", ".tga", ".bmp", ".exr", ".cxr"]
# formats only one renderer can write (.cxr: Corona's own multilayer file, render elements and LightMix inside)
ENGINE_ONLY_EXT = {".cxr": "corona"}
# formats that carry the render elements inside the main file: no separate file per element
MULTILAYER_EXT = (".cxr",)


def output_ext(path):
    return os.path.splitext(path or "")[1].lower()


def output_problem(path, engine):
    """Why this output path can't be written with this renderer, or None."""
    need = ENGINE_ONLY_EXT.get(output_ext(path))
    if need and engine != need:
        return "%s files can only be saved with %s" % (output_ext(path), need.capitalize())
    return None
DATE_FORMATS = ["YYYYMMDD", "YYYY-MM-DD", "MMDDYYYY", "MM-DD-YYYY", "YYMMDD", "YY-MM-DD", "MMDDYY", "MM-DD-YY"]
TOKEN_TYPES = [
    "Camera", "Date", "Date (Folder)", "Extension", "FileName (Full)", "FileName (Filtered)",
    "FileVersion", "Folder", "Index", "PcName", "SceneName", "Text", "UserName", "Version",
]
SKY_CLASSES = ["VRaySky", "CoronaSky", "FStormSky", "RS_Physical_Sky", "Physical_Sun___Sky_Environment"]

# cards: id -> (title, header tint, has on/off switch, has copy/paste, has property selector)
CARDS = {
    0: ("Setup List", None, False, False, False),
    1: ("Camera", "lavender", True, True, True),
    2: ("Resolution", "lavender", True, True, False),
    7: ("Time Output", "lavender", True, True, False),
    15: ("Scene Name", "lavender", False, True, False),
    3: ("Sun", "yellow", True, True, True),
    26: ("Lights", "yellow", True, True, True),
    28: ("HDRI Browser", "yellow", False, False, False),
    6: ("Environment", "yellow", True, True, True),
    4: ("Dome", "yellow", True, True, True),
    8: ("Background", "blue", True, True, False),
    20: ("Atmosphere", "blue", True, True, False),
    14: ("Layers", "teal", True, True, True),
    23: ("Objects", "teal", True, True, True),
    16: ("XRef Scenes", "teal", True, True, False),
    30: ("Variants", "teal", True, True, False),
    9: ("Render Output", "green", True, True, False),
    25: ("Render Settings", "orange", True, True, True),
    19: ("Render Override", "orange", True, True, False),
    18: ("Render Preset", "orange", True, True, False),
    21: ("Render Elements", "orange", True, True, False),
    29: ("Post-Production / VFB", "purple", True, True, False),
    17: ("Script File", "sky", True, True, False),
    22: ("Script Editor", "sky", True, True, False),
    31: ("Thumbnail", "gold", False, False, False),
    13: ("Todo", "gold", False, False, False),
    12: ("Notes", "gold", False, True, False),
}
# order of the side bar (a change of tint starts a new group) and of the "Cards" menu
CARD_ORDER = [1, 2, 7, 15, 3, 26, 28, 6, 4, 8, 20, 14, 23, 16, 30, 9, 25, 19, 18, 21, 29, 17, 22, 31, 13, 12]
DEFAULT_VISIBLE = [0, 1, 2, 15, 3, 28, 6, 14, 23, 9, 25]
# engines a card works with (empty = all)
CARD_ENGINES = {4: ["vray", "vraygpu", "redshift"], 26: ["vray", "vraygpu", "corona", "fstorm"],
                25: ["vray", "vraygpu", "corona", "fstorm"], 19: ["vray", "vraygpu", "corona", "fstorm"],
                21: ["vray", "vraygpu", "corona", "fstorm"], 29: ["corona"]}
# setup key holding the on/off switch of each card
CARD_KEY = {1: "camera", 2: "resolution", 7: "frames", 3: "sun", 26: "lights", 4: "dome", 6: "environment",
            14: "layers", 23: "objects", 16: "xref", 9: "output", 25: "render_custom", 8: "background",
            20: "atmosphere", 30: "variants", 19: "rs_override", 18: "render_preset", 21: "elements",
            29: "post", 17: "scripts", 22: "snippet"}
# smallest size of each card in grid units (columns, rows); a row is about 11 px
MIN_SIZE = {0: (6, 20), 9: (6, 20), 22: (6, 20), 1: (3, 10), 2: (3, 10), 7: (3, 10), 15: (3, 10), 3: (3, 10),
            6: (3, 10), 8: (3, 10), 18: (3, 10)}
# default places [x, y, w, h]: 12 columns (wide window) and 6 columns (narrow)
LAYOUT_LG = {0: [0, 0, 6, 40], 15: [0, 40, 3, 10], 1: [3, 40, 3, 14], 7: [0, 50, 3, 12], 2: [3, 54, 3, 10],
             9: [0, 64, 6, 20], 3: [6, 0, 3, 20], 28: [9, 0, 3, 30], 6: [6, 20, 3, 30], 4: [9, 30, 3, 20],
             26: [9, 50, 3, 20], 14: [6, 50, 3, 24], 23: [9, 70, 3, 20], 16: [6, 74, 3, 20], 30: [9, 90, 3, 20],
             8: [0, 84, 3, 10], 20: [3, 84, 3, 20], 25: [6, 94, 3, 20], 19: [9, 110, 3, 24], 18: [6, 114, 3, 10],
             21: [6, 124, 3, 20], 29: [9, 134, 3, 30], 17: [0, 104, 3, 20], 22: [0, 124, 6, 22], 31: [3, 104, 3, 20],
             13: [0, 146, 3, 20], 12: [3, 146, 3, 20]}
LAYOUT_MD = {0: [0, 0, 6, 34], 15: [0, 34, 3, 10], 1: [3, 34, 3, 14], 7: [0, 44, 3, 12], 2: [3, 48, 3, 10],
             3: [0, 58, 3, 14], 28: [3, 58, 3, 30], 6: [0, 72, 3, 30], 4: [3, 88, 3, 20], 26: [3, 108, 3, 20],
             14: [0, 102, 3, 24], 23: [3, 128, 3, 20], 16: [0, 126, 3, 20], 30: [3, 148, 3, 20], 9: [0, 168, 6, 20],
             8: [0, 188, 3, 10], 20: [3, 188, 3, 20], 25: [0, 198, 3, 20], 19: [3, 208, 3, 24], 18: [0, 218, 3, 10],
             21: [0, 228, 3, 20], 29: [3, 232, 3, 30], 17: [0, 248, 3, 20], 22: [0, 268, 6, 22], 31: [3, 262, 3, 20],
             13: [0, 290, 3, 20], 12: [3, 290, 3, 20]}
BACKGROUND_TYPES = ["Gradient", "Solid", "Environment", "Custom file"]


def engine_id(name):
    for n, i in (("V-Ray", "vray"), ("Corona", "corona"), ("Arnold", "arnold"), ("FStorm", "fstorm"), ("Redshift", "redshift")):
        if n in (name or ""):
            return i
    return None


def parse_number(text):
    """What a person types in a number box: ".5", "-.5", ",5", "1,25", "2." are numbers too. None if it isn't one."""
    t = (text or "").strip().replace(" ", "").replace(",", ".")
    if t.startswith("+"):
        t = t[1:]
    if t in ("", "-", ".", "-."):
        return None
    if t.startswith("."):
        t = "0" + t
    elif t.startswith("-."):
        t = "-0" + t[1:]
    try:
        return float(t)
    except ValueError:
        return None


# ---------------------------------------------------------------- what a setup read from a file may name

# A setup comes inside a .max file, possibly made by someone else: the names it carries are checked before they reach
# 3ds Max. A class or property name is a plain name, never a path into other objects and never code.
_PLAIN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}")
LIGHTMIX_ARRAYS = ("colorMap_lightmixIntensities", "colorMap_lightmixColors", "colorMap_lightmixEnabledLayers")


def is_plain_name(text):
    """Letters, digits and underscores, not starting with a digit: a name that cannot reach another object."""
    return isinstance(text, str) and _PLAIN.fullmatch(text) is not None


def is_tone_operator(cls):
    """A Corona colour-mapping operator class (ToneMappingOperatorPlugin...): the only classes a tone-mapping chain
    may make."""
    return is_plain_name(cls) and cls.endswith("OperatorPlugin")


def is_scalar(v):
    return isinstance(v, (bool, int, float, str))


def renderer_value_ok(name, v):
    """A render setting a setup may carry (Render Override, the default render settings): a renderer property of its
    own, by a plain name, with a plain value, as the Fetch buttons take them."""
    return is_plain_name(name) and is_scalar(v)


def post_setting_ok(key, name):
    """A setting of the Post-Production card: only those its category lists."""
    names = next((n for k, _, n in POST_CATS if k == key), ())
    return name in names


# ---------------------------------------------------------------- property table

_TABS = None


def all_tabs():
    global _TABS
    if _TABS is None:
        with open(os.path.join(HERE, "props.json"), "r", encoding="utf-8") as f:
            _TABS = json.load(f)
    return _TABS


def tabs_for(card, engine):
    return [t for t in all_tabs() if t["id"] == card and (t.get("engine") in (None, engine))]


def tab_matches(tab, cls):
    """Is this Property Selector tab for objects of class cls?"""
    if not cls:
        return False
    return cls in (tab.get("classes") or []) or tab.get("cls") == cls


def prop_key(tab, prop):
    return "%s|%s" % (tab["v_class"], prop["name"])


def default_enabled(card):
    if card == 6:
        return ["CoronaBitmap|uAngle", "CoronaBitmap|uvwOffset.y", "CoronaBitmap|output.output_amount",
                "CoronaSky|intensityMultiplier", "CoronaSky|HorizonBlur", "CoronaSky|altitude",
                "CoronaSky|cloudsEnable", "CoronaSky|cloudsSeed", "CoronaSky|cloudsContrailsStrength"]
    out = []
    for t in all_tabs():
        if t["id"] == card:
            out.extend(prop_key(t, p) for p in t["props"] if p.get("enabled"))
    return out


def enabled_rows(card, engine, enabled_keys):
    """(tab, prop) pairs ticked for a card, in table order."""
    on = set(enabled_keys)
    rows = []
    for t in tabs_for(card, engine):
        for p in t["props"]:
            if prop_key(t, p) in on:
                rows.append((t, p))
    return rows


# Daylight: controller.solar_date counts days from June 21 of the current year (what the Motion panel shows)
def solar_base(today=None):
    return datetime.date((today or datetime.date.today()).year, 6, 21)


def solar_to_date(v, today=None):
    try:
        return solar_base(today) + datetime.timedelta(days=int(round(float(v or 0))))
    except (TypeError, ValueError, OverflowError):
        return solar_base(today)


def date_to_solar(d, today=None):
    return float((d - solar_base(today)).days)


# ---------------------------------------------------------------- more than one sun / environment in a setup

def entries(block):
    """The tabs of a Sun / Environment card: the block itself, then its extra entries."""
    return [block] + list(block.get("extra") or [])


def entry_store(s, block, i):
    """Where tab i keeps its settings: the first one in the setup's props, the others in their own."""
    if i <= 0:
        return s["props"]
    return block["extra"][i - 1].setdefault("props", {})


def new_env_entry():
    return {"cls": "", "name": "", "props": {}, "on": True, "amount": 1.0}


def env_mixing(block, engine):
    """Several environment tabs are added together in the environment slot (like a LightMix): Corona, two tabs or more."""
    return engine == "corona" and len(entries(block)) > 1 and bool(block.get("mix", True))


def env_mix_items(block, find_map):
    """(class, name, intensity) of the tabs that go in the mix: chosen, found in the scene and on."""
    out = []
    for en in entries(block):
        m = find_map(en.get("cls"), en.get("name")) if en.get("cls") else None
        if m and en.get("on", True):
            try:
                a = float(en.get("amount", 1.0))
            except (TypeError, ValueError):
                a = 1.0
            out.append((m["class"], m["name"], round(max(0.0, a), 4)))
    return tuple(out)


def env_rows(m, enabled_rows_):
    """Ticked settings of an environment map and of every map linked below it: (tab, prop, link, key class).
    A second map of the same class (two bitmaps under a select) gets its own key."""
    rows = []
    seen = {}
    for link in (m.get("chain") or [m]):
        cls = link["class"]
        n = seen.get(cls, 0)
        seen[cls] = n + 1
        key_cls = cls if n == 0 else "%s@%s" % (cls, link["name"])
        for t, p in enabled_rows_:
            if t["v_class"] == cls:
                rows.append((t, p, link, key_cls))
    return rows


def light_tabs_classes(l):
    """Classes whose tabs apply to a sun: a Daylight shows its own tab and the one of the sun inside it."""
    if not l:
        return []
    return [c for c in (l.get("class"), l.get("sun_class")) if c]


def light_prop(l, tab, prop):
    """Property path on the node: settings of the sun inside a Daylight go through .sun"""
    if l and l.get("sun_class") and tab_matches(tab, l.get("sun_class")) and not tab_matches(tab, l.get("class")):
        return "sun." + prop["name"]
    return prop["name"]


# ---------------------------------------------------------------- Post-Production / VFB (Corona)

# category: title and the renderer settings it holds; the first one turns the category on in the VFB
POST_CATS = [
    ("bloom", "Bloom and Glare", ["bloomGlare_enabled", "bloomGlare_bloomIntensity", "bloomGlare_glareIntensity", "bloomGlare_threshold",
                                  "bloomGlare_size", "bloomGlare_colorIntensity", "bloomGlare_colorShift", "bloomGlare_streakCount",
                                  "bloomGlare_rotation", "bloomGlare_streakBlur"]),
    ("sharpen", "Sharpening / Blurring", ["sharpening_blurring_enable", "sharpening_amount", "sharpening_radius", "blurring_radius"]),
    ("denoise", "Denoising", ["denoise_blendEnabled", "denoise_blendAmount"]),
    ("auto", "Auto Adjust", ["autoAdjust_on", "autoAdjust_expOn", "autoAdjust_expStrength", "autoAdjust_wbOn", "autoAdjust_wbStrength"]),
    ("lens", "Lens Effects", ["lensEffects_peripheralGrating_enabled", "lensEffects_peripheralGrating_strength",
                              "lensEffects_occlusion_enabled", "lensEffects_occlusion_ratio",
                              "lensEffects_scratches_enabled", "lensEffects_scratches_strength",
                              "lensEffects_dust_enabled", "lensEffects_dust_strength"]),
]
POST_ORDER = ["tonemap", "lightmix", "bloom", "sharpen", "denoise", "auto", "lens"]
POST_TITLES = dict([("tonemap", "Tone Mapping"), ("lightmix", "LightMix")] + [(k, t) for k, t, _ in POST_CATS])
POST_OPERATORS = {
    "SimpleExposureOperatorPlugin": "Simple Exposure", "PhotographicExposureOperatorPlugin": "Photographic Exposure",
    "ContrastOperatorPlugin": "Contrast", "SaturationOperatorPlugin": "Saturation", "FilmicOperatorPlugin": "Filmic",
    "AdvancedFilmicOperatorPlugin": "Advanced Filmic", "ReinhardOperatorPlugin": "Highlight Compression",
    "WhiteBalanceOperatorPlugin": "White Balance", "WhiteBalanceImprovedOperatorPlugin": "White Balance",
    "GreenMagentaTintOperatorPlugin": "Green-Magenta Tint", "TintOperatorPlugin": "Tint", "ToneCurveOperatorPlugin": "Tone Curve",
    "CurvesOperatorPlugin": "Curves", "LiftGammaGainOperatorPlugin": "Lift Gamma Gain", "VignetteOperatorPlugin": "Vignette",
    "LutOperatorPlugin": "LUT", "AcesOtOperatorPlugin": "ACES OT",
}
POST_RANGE = {"simpleExposure": (-10, 10), "contrast": (0, 10), "saturation": (-1, 1), "highlightCompression": (1, 99),
              "colorTemperature": (1000, 20000), "greenMagentaTint": (-1, 1), "opacity": (0, 1), "richShadows": (0, 1),
              "highlights": (-1, 1), "lights": (-1, 1), "darks": (-1, 1), "shadows": (-1, 1), "intensity": (0, 2), "falloff": (0, 2),
              "lift": (0, 2), "gamma": (0, 5), "gain": (0, 5), "toeStrength": (0, 1), "toeLength": (0, 1),
              "shoulderStrength": (0, 1), "shoulderLength": (0, 1), "shoulderAngle": (0, 1),
              "bloomIntensity": (0, 100), "glareIntensity": (0, 100), "threshold": (0, 100), "size": (0, 100),
              "colorIntensity": (0, 1), "colorShift": (0, 1), "streakCount": (1, 8), "rotation": (0, 360), "streakBlur": (0, 1),
              "amount": (0, 10), "radius": (0, 10), "blendAmount": (0, 1), "expStrength": (0, 1), "wbStrength": (0, 1),
              "strength": (0, 2), "ratio": (0, 1)}


def post_label(name):
    """colorMappingOperator_highlightCompression -> Highlight Compression; bloomGlare_size -> Size."""
    leaf = name.split("_")[-1]
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", leaf[:1].upper() + leaf[1:])


def post_range(name, value=None):
    leaf = name.split("_")[-1]
    lo, hi = POST_RANGE.get(leaf, (0, 10))
    try:
        v = float(value)
        lo, hi = min(lo, v), max(hi, v)
    except (TypeError, ValueError):
        pass
    return lo, hi


# 3ds Max keeps the time limit in milliseconds, the card shows minutes
def to_max(name, v):
    return v * 60000.0 if name == "progressive_timeLimit" else v


def from_max(name, v):
    return v / 60000.0 if name == "progressive_timeLimit" else v


# ---------------------------------------------------------------- setups

def new_token(kind):
    value = {"Extension": ".jpg", "Date": DEFAULT_DATE_FORMAT, "Date (Folder)": DEFAULT_DATE_FORMAT,
             "Version": "1", "Text": "_"}.get(kind, "")
    return {"kind": kind, "value": value, "digits": 3 if kind in ("Index", "Version") else 1, "folder": kind == "Folder"}


def empty_setup(sid):
    return {
        "id": sid,
        "color": "#ffffff",
        "render": True,
        "scenename": "",
        "camera": {"enabled": True, "handle": None, "name": "", "locked": False},
        "resolution": {"enabled": True, "width": DEFAULT_WIDTH, "height": DEFAULT_HEIGHT, "ratio": DEFAULT_RATIO, "locked": False},
        "sun": {"enabled": False, "handle": None, "name": "", "extra": []},
        "dome": {"enabled": False, "handle": None, "name": ""},
        "environment": {"enabled": False, "cls": "", "name": "", "extra": [], "mix": True, "on": True, "amount": 1.0},
        "frames": {"enabled": False, "kind": 0, "single": 0, "start": 0, "end": 100, "nth": 1, "list": DEFAULT_FRAME_LIST},
        "layers": {"enabled": False, "set": []},
        "objects": {"enabled": False, "set": []},
        "lights": {"enabled": False, "set": []},
        "xref": {"enabled": False, "set": []},
        "output": {"enabled": False, "project_path": "", "preset": [new_token("Camera"), new_token("Extension")]},
        "render_custom": {"enabled": False},
        "background": {"enabled": False, "type": 0, "path": ""},
        "atmosphere": {"enabled": False, "set": []},
        "variants": {"enabled": False, "set": []},
        "elements": {"enabled": False, "set": []},
        "render_preset": {"enabled": False, "path": ""},
        "rs_override": {"enabled": False, "set": {}},
        "post": {"enabled": False, "conf": "", "lightmix": {}, "cats": {}},
        "scripts": {"enabled": False, "pre_render": {"enabled": False, "path": ""}, "post_render": {"enabled": False, "path": ""}},
        "snippet": {"enabled": False, "pre_setup": "", "post_setup": "", "pre_render": "", "post_render": ""},
        "thumbnail": "",
        "notes": "",
        "status": "#WIP",
        "props": {},
    }


def _same_kind(default, v):
    """Whether a stored value has the kind of the default it stands for: a number for a number (whole or not), a
    switch for a switch, a text for a text, a list for a list, a group for a group."""
    if isinstance(default, bool):
        return isinstance(v, bool)
    if isinstance(default, (int, float)):
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if default is None:
        return v is None or (isinstance(v, (int, float, str)) and not isinstance(v, bool))
    return isinstance(v, type(default))


def normalize(s, sid=None):
    """Fills in anything missing from a stored setup (older versions, hand edits) and replaces a value of the wrong
    kind with its default, so that a file made to break the window cannot."""
    sid = s.get("id", sid) if sid is None else sid
    base = empty_setup(sid if isinstance(sid, int) and not isinstance(sid, bool) else 0)
    for k, v in base.items():
        if k not in s or not _same_kind(v, s[k]):
            s[k] = v
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 not in s[k] or not _same_kind(v2, s[k][k2]):
                    s[k][k2] = copy.deepcopy(v2)
    return s


def layer_entry(name, visible=True, freeze=False, render=True, vcam=True):
    return {"name": name, "visible": visible, "freeze": freeze, "render": render, "vcam": vcam, "extra": {}}


def object_entry(handle, name, visible=True, renderable=True):
    return {"handle": handle, "name": name, "visible": visible, "renderable": renderable, "extra": {}}


def copy_entry(e):
    """A row of the Layers / Objects card for another setup: same values, its own dicts."""
    return dict(e, extra=dict(e.get("extra") or {}))


def shared_rows(setups, key, field):
    """The rows of the Layers (key "layers", field "name") or Objects ("objects", "handle") card are one list for all
    the setups; each setup keeps its own values. This is that list: every row some setup has, in the order they were
    added, as the first entry found for each."""
    seen, out = set(), []
    for s in setups:
        for e in s[key]["set"]:
            k = e.get(field)
            if k is not None and k not in seen:
                seen.add(k)
                out.append(e)
    return out


def ratio(w, h):
    if not h:
        return DEFAULT_RATIO
    return round(w / float(h), 3)


def parse_frame_list(text):
    out = []
    for part in (text or "").split(","):
        p = part.strip()
        if not p:
            continue
        m = re.match(r"^(-?\d+)\s*-\s*(-?\d+)$", p)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b and b - a < 100000:
                out.extend(range(a, b + 1))
        else:
            try:
                out.append(int(p))
            except ValueError:
                pass
    return out


def frame_count(s):
    f = s["frames"]
    if not f["enabled"]:
        return 1
    if f["kind"] == 1:
        return max(1, (f["end"] - f["start"]) // max(1, f["nth"]) + 1) if f["end"] >= f["start"] else 1
    if f["kind"] == 2:
        return len(parse_frame_list(f["list"]))
    return 1


COMPRESSED_PREFIX = "osz1:"
OLD_COMPRESSED_PREFIX = "pzz1:"  # setups saved before 2.0.0
COMPRESS_FROM = 32 * 1024  # bigger than this, the text kept in the .max is zlib + base64 (layer lists shrink ~10x)


# The format of the setups kept in a .max file. A file whose version is newer is refused, never guessed at.
FORMAT_VERSION = 1
MAX_STORED = 64 * 1024 * 1024  # the stored text, unpacked: far more than thousands of setups take
MAX_SETUPS = 2000


def encode(setups, todo=None, extra=None):
    d = {"format": "openscene", "version": FORMAT_VERSION, "setups": setups, "todo": todo or []}
    d.update(extra or {})
    text = json.dumps(d, separators=(",", ":"))
    if len(text) > COMPRESS_FROM:
        import zlib
        text = COMPRESSED_PREFIX + base64.b64encode(zlib.compress(text.encode("utf-8"), 6)).decode("ascii")
    return text


def _unpack(packed):
    """zlib data, unpacked up to MAX_STORED bytes; ValueError when it is broken or bigger."""
    import zlib

    try:
        d = zlib.decompressobj()
        raw = d.decompress(base64.b64decode(packed, validate=True), MAX_STORED)
    except (ValueError, zlib.error) as error:
        raise ValueError("the stored setups are damaged") from error
    if d.unconsumed_tail:
        raise ValueError("the stored setups are bigger than OpenScene reads")
    return raw.decode("utf-8")


def _refused(why):
    """What decode gives for setups it does not read: none, and why. The window keeps them as they are in the file."""
    return {"setups": [], "todo": [], "rs_default": {}, "problem": why}


def decode(text):
    """Stored text -> {"setups": [...], "todo": [...], "rs_default": {...}, "problem": None}, or None when it isn't
    ours. Setups it cannot take (a newer format, too big, damaged) come back as none, with "problem" saying why."""
    if not text:
        return None
    if len(text) > MAX_STORED:
        return _refused("the stored setups are bigger than OpenScene reads")
    prefix = next((p for p in (COMPRESSED_PREFIX, OLD_COMPRESSED_PREFIX) if text.startswith(p)), None)
    if prefix:
        try:
            text = _unpack(text[len(prefix) :])
        except (ValueError, UnicodeDecodeError) as error:
            return _refused(str(error))
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not (isinstance(data, dict) and isinstance(data.get("setups"), list)):
        return None
    version = data.get("version", 1)
    if not isinstance(version, int) or isinstance(version, bool):
        return _refused("the stored setups have no format version OpenScene knows")
    if version > FORMAT_VERSION:
        return _refused("they were saved by a newer OpenScene (format %d): update OpenScene to use them" % version)
    setups = [normalize(s) for s in data["setups"] if isinstance(s, dict)]
    problem = None
    if len(setups) > MAX_SETUPS:
        problem = "only the first %d of %d setups were read" % (MAX_SETUPS, len(setups))
        setups = setups[:MAX_SETUPS]
    # every setup has an id of its own: a missing or repeated one gets a new one
    seen = set()
    next_id = max([s["id"] for s in setups if s["id"] > 0] + [0]) + 1
    for s in setups:
        if s["id"] <= 0 or s["id"] in seen:
            s["id"] = next_id
            next_id += 1
        seen.add(s["id"])
    todo = data.get("todo")
    rs_default = data.get("rs_default")
    return {
        "setups": setups,
        "todo": [t for t in todo if isinstance(t, dict)] if isinstance(todo, list) else [],
        "rs_default": {k: v for k, v in rs_default.items() if renderer_value_ok(k, v)}
        if isinstance(rs_default, dict)
        else {},
        "problem": problem,
    }


# ---------------------------------------------------------------- output path

def _strip_ext(name):
    i = name.rfind(".")
    if i > 0 and "/" not in name[i:] and "\\" not in name[i:]:
        return name[:i]
    return name


def file_version(name):
    m = re.search(r"(\d+)$", _strip_ext(name))
    return m.group(1) if m else ""


def filtered_file_name(name):
    base = _strip_ext(name)
    ver = file_version(name)
    if not ver:
        return base
    return re.sub(r"^[^0-9A-Za-z]+|[^0-9A-Za-z]+$", "", base[: len(base) - len(ver)])


def format_date(fmt, now=None):
    now = now or datetime.datetime.now()
    f = (fmt or DEFAULT_DATE_FORMAT).replace("YYYY", "%Y").replace("YY", "%y").replace("MM", "%m").replace("DD", "%d")
    return now.strftime(f)


def is_valid_file_path(p):
    return not any(c in p for c in '*?"<>|') and p.count(":") <= 1


def final_path(out, file_name, camera_name, scene_name, index, pc_name, user_name):
    """Project path + the tokens in order; a token with no value stops the build. Returns (path, valid)."""
    path = ""
    ext = ""
    complete = True
    project = (out.get("project_path") or "").strip()
    if project:
        path = project.replace("\\", "/")
        if not path.endswith("/"):
            path += "/"
        for t in out.get("preset", []):
            kind = t.get("kind")
            val = (t.get("value") or "").strip()
            digits = int(t.get("digits") or 1)
            if kind == "Camera":
                piece = camera_name or None
            elif kind == "Version":
                piece = val.zfill(digits) if val else None
            elif kind == "Index":
                piece = str(index + 1).zfill(digits)
            elif kind == "FileName (Full)":
                piece = _strip_ext(file_name) or None
            elif kind == "FileName (Filtered)":
                piece = filtered_file_name(file_name) or None
            elif kind == "FileVersion":
                piece = file_version(file_name) or None
            elif kind == "PcName":
                piece = pc_name or None
            elif kind == "UserName":
                piece = user_name or None
            elif kind == "SceneName":
                piece = (scene_name or "").strip() or None
            elif kind == "Extension":
                ext = t.get("value") or ""
                piece = ext or None
            elif kind == "Date":
                piece = format_date(val)
            elif kind == "Date (Folder)":
                piece = format_date(val) + "/"
            else:  # Text, Folder
                piece = val or None
            if piece is None:
                complete = False
                break
            path += piece
            if t.get("folder") and not path.endswith("/"):
                path += "/"
    else:
        complete = False
    last_slash = path.rfind("/")
    ext_pos = path.rfind(ext) if ext else -1
    valid = complete and bool(path.strip()) and bool(ext) and last_slash + 1 < ext_pos and is_valid_file_path(path)
    return path, valid


# ---------------------------------------------------------------- HDRI folder

THUMB_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
_SEPARATORS = ("_", "-", ".", " ")


def find_thumbnail(stem, images):
    """The preview of an HDRI among {lower-case stem: file name}: the same name; or, as HDRI libraries name them, the
    name without what follows it (bell_park_dawn_16k.hdr -> bell_park_dawn.webp); or the name with something added
    (studio.hdr -> studio_preview.jpg, studio.hdr.jpg). The closest match wins."""
    low = stem.lower()
    if low in images:
        return images[low]
    best, best_len = None, -1
    for name in images:
        if low.startswith(name) and low[len(name):len(name) + 1] in _SEPARATORS and len(name) > best_len:
            best, best_len = name, len(name)
    if best is not None:
        return images[best]
    for name in sorted(images, key=len):
        if name.startswith(low) and name[len(low):len(low) + 1] in _SEPARATORS:
            return images[name]
    return None


def _pictures_in(names, prefix=""):
    images = {}
    # when a stem has several pictures, the first extension of the list wins
    for ext in reversed(THUMB_EXTENSIONS):
        for n in names:
            stem, e = os.path.splitext(n)
            if e.lower() == ext:
                images[stem.lower()] = os.path.join(prefix, n) if prefix else n
    return images


def read_image_thumbnails(folder):
    """This folder only: *.hdr and *.exr with the picture that goes with each one, looked for next to it first and
    then in its sub-folders (thumbs, previews, jpg...)."""
    out = []
    try:
        names = os.listdir(folder)
    except OSError:
        return out
    here = _pictures_in(names)
    below = {}
    for d in sorted(names):
        sub = os.path.join(folder, d)
        if d.startswith(".") or not os.path.isdir(sub):
            continue
        try:
            for k, v in _pictures_in(os.listdir(sub), d).items():
                below.setdefault(k, v)
        except OSError:
            pass
    for ext in (".exr", ".hdr"):
        for n in sorted(x for x in names if x.lower().endswith(ext)):
            raw = os.path.join(folder, n)
            if not os.path.isfile(raw):
                continue
            stem = n[: -len(ext)]
            t = find_thumbnail(stem, here) or find_thumbnail(stem, below)
            out.append({"raw": raw, "name": n, "thumb": os.path.join(folder, t) if t else None})
    return out


def preview_cache_name(raw, size=0, mtime=0.0):
    """File name of the picture made from an HDRI that has none: changes when the HDRI changes."""
    import hashlib
    key = "%s|%d|%d" % (os.path.normcase(os.path.abspath(raw)), int(size), int(mtime))
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(os.path.basename(raw))[0])[:40]
    return "%s_%s.jpg" % (stem, hashlib.md5(key.encode("utf-8")).hexdigest()[:10])


def clone(s, new_id):
    c = copy.deepcopy(s)
    c["id"] = new_id
    return c
