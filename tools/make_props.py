# SPDX-License-Identifier: GPL-3.0-or-later
"""Builds openmanager/props.json (the Property Selector table) from tools/props_source.py.

python tools/make_props.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "package", "OpenManager", "openmanager", "props.json")
sys.path.insert(0, HERE)
from props_source import TABLES  # noqa: E402

# card id, tab name, classes it applies to, engine (None = any), table key, class name stored with each value
TABS = [
    (1, "Standard Camera", ["Freecamera", "Targetcamera"], None, "max_standard_cam", "Standard"),
    (1, "Physical Camera", ["Physical"], None, "max_physical_cam", "Physical Camera"),
    (1, "V-Ray Camera", ["VRayPhysicalCamera"], "vray", "vray_cam", "VRayPhysicalCamera"),
    (1, "Corona Camera", ["CoronaCam"], "corona", "corona_cam", "CoronaCam"),
    (1, "Corona Overrides", ["CoronaCam"], "corona", "corona_cam_overrides", "CoronaCam"),
    (1, "FStorm Camera", ["FStormCamera"], "fstorm", "fstorm_cam", "FStormCamera"),
    (3, "V-Ray Sun", ["VRaySun"], "vray", "vray_sun", "VRaySun"),
    (3, "V-Ray Clouds", ["VRaySun"], "vray", "vray_cloud", "VRaySun"),
    (3, "Corona Sun", ["CoronaSun"], "corona", "corona_sun", "CoronaSun"),
    (3, "FStorm Sun", ["FStormSunLight"], "fstorm", "fstorm_sun", "FStormSunLight"),
    (3, "Daylight", ["DaylightAssemblyHead"], None, "max_daylight", "DaylightAssemblyHead"),
    (4, "Bitmap", ["Bitmaptexture"], None, "max_bitmap", "Bitmaptexture"),
    (4, "ColorCorrection", ["Color_Correction"], None, "max_cc", "Color_Correction"),
    (4, "V-Ray Bitmap", ["VRayHDRI"], "vray", "vray_bitmap", "VRayHDRI"),
    (4, "V-Ray Dome", ["VRayLight"], "vray", "vray_dome", "VRayLight"),
    (6, "Bitmap", ["Bitmaptexture"], None, "max_bitmap", "Bitmaptexture"),
    (6, "Default CC", ["Color_Correction"], None, "max_cc", "Color_Correction"),
    (6, "V-Ray Bitmap", ["VRayHDRI"], "vray", "vray_bitmap", "VRayHDRI"),
    (6, "Corona Bitmap", ["CoronaBitmap"], "corona", "corona_bitmap", "CoronaBitmap"),
    (6, "Corona CC", ["CoronaColorCorrect"], "corona", "corona_cc", "CoronaColorCorrect"),
    (6, "Corona Select", ["CoronaSelect"], "corona", "corona_select", "CoronaSelect"),
    (6, "FStorm Bitmap", ["FStormBitmap"], "fstorm", "fstorm_bitmap", "FStormBitmap"),
    (6, "FStorm ColorCorrect", ["FStormColorCorrection"], "fstorm", "fstorm_cc", "FStormColorCorrection"),
    (6, "Corona Sky/Clouds", ["CoronaSky"], "corona", "corona_cloud", "CoronaSky"),
    (14, "Layers", None, None, "max_layers", "Layers"),
    (23, "General", None, None, "max_objects", "Objects"),
    (23, "V-Ray", None, "vray", "vray_objects", "Objects"),
    (25, "V-Ray", ["VRayRenderer"], "vray", "vray_render", "VRayRenderer"),
    (25, "V-Ray GPU", ["VRayGPURenderer"], "vraygpu", "vraygpu_render", "VRayGPURenderer"),
    (25, "Corona", ["CoronaRenderer"], "corona", "corona_render", "CoronaRenderer"),
    (25, "FStorm", ["FStormRenderer"], "fstorm", "fstorm_render", "FStormRenderer"),
    (26, "V-Ray Light", ["VRayLight"], "vray", "vray_light", "VRayLight"),
    (26, "Corona Light", ["CoronaLight"], "corona", "corona_light", "CoronaLight"),
    (26, "FStorm Light", ["FStormLight"], "fstorm", "fstorm_light", "FStormLight"),
]


def tab_props(raw):
    out = []
    for p in raw:
        disp = p.get("display")
        if isinstance(disp, list):
            short, long = (disp + [disp[0]])[:2]
        else:
            short = long = disp or p["name"]
        d = {
            "name": p["name"],
            "class": p.get("class", "Float"),
            "short": short,
            "long": long,
            "value": p.get("value"),
            "enabled": bool(p.get("enabled")),
        }
        for k in ("min", "max", "step"):
            if p.get(k) is not None:
                d[k] = p[k]
        out.append(d)
    return out


def main():
    tabs = []
    for cid, name, cls, engine, key, v_class in TABS:
        props = tab_props(TABLES.get(key, []))
        if not props:
            raise SystemExit("no table for %s" % key)
        tabs.append(
            {
                "id": cid,
                "name": name,
                "cls": cls[0] if cls else None,
                "classes": cls,
                "engine": engine,
                "v_class": v_class,
                "props": props,
            }
        )
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(tabs, f, indent=2)
        f.write("\n")
    print("wrote %s: %d tabs, %d settings" % (OUT, len(tabs), sum(len(t["props"]) for t in tabs)))


if __name__ == "__main__":
    main()
