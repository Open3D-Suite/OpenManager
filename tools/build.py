# SPDX-License-Identifier: GPL-3.0-or-later
"""Builds dist/OpenScene.bundle, the Autodesk ApplicationPlugins bundle that the Open3D launcher installs (or that is
copied into %APPDATA%\\Autodesk\\ApplicationPlugins by hand): checks the MAXScript files, draws the icons, copies
the package and writes PackageContents.xml with the version of openscene/__init__.py.

    python tools/build.py

Plain Python, nothing to install. `python -I tools/repo.py package` runs it and zips the bundle.
"""

import os
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ElementTree
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "package")
BUNDLE_SRC = os.path.join(ROOT, "bundle")
DIST = os.path.join(ROOT, "dist")
ICON_NAME = "OpenScene"
SIZES = (16, 24, 30, 32, 36, 48)

# The bundle's identity for 3ds Max: made once for OpenScene, never changed
PRODUCT_CODE = "{1DE32304-98D8-46E2-B9E7-BBEDA0AE3FA9}"
UPGRADE_CODE = "{017FED04-B7BD-4640-80CE-06ECEE03FE5C}"
SERIES_MIN = "2025"  # Python 3.11 and PySide6
SERIES_MAX = "2099"  # 3ds Max 2027 ignores a bundle without SeriesMax: 2099 sets no limit

# ---------------------------------------------------------------- icon: the puzzle piece, in greys


def _in_round_rect(x, y, x0, y0, x1, y1, r):
    if x < x0 or x > x1 or y < y0 or y > y1:
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _in_circle(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _in_puzzle(x, y):
    """Unit coordinates (0..1). Square body, knobs on top and right, sockets on left and bottom; fills the icon."""
    x = (x - 0.5) / 1.35 + 0.535
    y = (y - 0.5) / 1.35 + 0.445
    body = _in_round_rect(x, y, 0.20, 0.30, 0.68, 0.78, 0.05)
    knob = _in_circle(x, y, 0.44, 0.215, 0.105) or _in_circle(x, y, 0.765, 0.54, 0.105)
    hole = _in_circle(x, y, 0.20, 0.54, 0.085) or _in_circle(x, y, 0.44, 0.78, 0.085)
    return (body or knob) and not hole


# 3ds Max picks the icon set of its theme: silver on the dark interface, graphite on the light one
THEMES = {"Dark": ((0xFF, 0xFF, 0xFF), (0xA4, 0xA4, 0xA4)), "Light": ((0x5C, 0x5C, 0x5C), (0x14, 0x14, 0x14))}


def draw_icon(size, theme="Dark", ss=6):
    c0, c1 = THEMES[theme]
    px = []
    for j in range(size):
        row = []
        for i in range(size):
            cov = 0
            for sj in range(ss):
                for si in range(ss):
                    if _in_puzzle((i + (si + 0.5) / ss) / size, (j + (sj + 0.5) / ss) / size):
                        cov += 1
            t = min(1.0, max(0.0, (i + j) / (2.0 * size)))
            rgb = tuple(int(round(c0[k] + (c1[k] - c0[k]) * t)) for k in range(3))
            row.append(rgb + (int(round(cov * 255.0 / (ss * ss))),))
        px.append(row)
    return px


def write_png(path, px):
    h, w = len(px), len(px[0])
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def build_icons(out):
    for theme in THEMES:
        folder = os.path.join(out, theme)
        os.makedirs(folder, exist_ok=True)
        for s in SIZES:
            write_png(os.path.join(folder, "%s_%d.png" % (ICON_NAME, s)), draw_icon(s, theme))


# ---------------------------------------------------------------- bundle


def read_version():
    with open(os.path.join(PKG, "OpenScene", "openscene", "__init__.py"), encoding="utf-8") as f:
        m = re.search(r'^__version__ = "([^"]+)"', f.read(), re.M)
    if not m:
        raise SystemExit("openscene/__init__.py has no __version__")
    return m.group(1)


# The parts of the bundle, as 3ds Max reads them: the macro, the icon folders of each theme and the start-up script
PARTS = (
    ("macroscripts parts", "./Contents/macroscripts/OpenScene.mcr"),
    ("dark icon paths parts", "./Contents/icons/Dark"),
    ("light icon paths parts", "./Contents/icons/Light"),
    ("post-start-up scripts parts", "./Contents/scripts/openscene_bundle.ms"),
)


def package_contents(version):
    req = '<RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="%s" SeriesMax="%s" />' % (
        SERIES_MIN,
        SERIES_MAX,
    )
    parts = "".join(
        '    <Components Description="%s">\n'
        "        %s\n"
        '        <ComponentEntry AppName="OpenScene" Version="%s" ModuleName="%s" />\n'
        "    </Components>\n" % (desc, req, version, module)
        for desc, module in PARTS
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- SPDX-License-Identifier: GPL-3.0-or-later -->\n"
        "<ApplicationPackage\n"
        '    SchemaVersion="1.0"\n'
        '    AutodeskProduct="3ds Max"\n'
        '    ProductType="Application"\n'
        '    Name="OpenScene"\n'
        '    Description="Scene setups and batch rendering for 3ds Max."\n'
        '    AppVersion="%s"\n'
        '    ProductCode="%s"\n'
        '    UpgradeCode="%s">\n'
        '    <CompanyDetails Name="OpenScene contributors" />\n'
        "    %s\n"
        "%s"
        "</ApplicationPackage>\n" % (version, PRODUCT_CODE, UPGRADE_CODE, req, parts)
    )


def check_bundle(target, version):
    """Refuses a bundle 3ds Max would load wrongly or not at all."""
    # the file build_bundle has just written from package_contents: ours, not XML from someone else
    root = ElementTree.parse(os.path.join(target, "PackageContents.xml")).getroot()  # noqa: S314
    problems = []
    if root.get("AppVersion") != version:
        problems.append("AppVersion is %s, not %s" % (root.get("AppVersion"), version))
    for req in root.iter("RuntimeRequirements"):
        if (req.get("SeriesMin"), req.get("SeriesMax")) != (SERIES_MIN, SERIES_MAX):
            problems.append("RuntimeRequirements without SeriesMin %s and SeriesMax %s" % (SERIES_MIN, SERIES_MAX))
    for entry in root.iter("ComponentEntry"):
        if entry.get("Version") != version:
            problems.append("%s has version %s" % (entry.get("ModuleName"), entry.get("Version")))
        if not os.path.exists(os.path.join(target, entry.get("ModuleName"))):
            problems.append("%s is not in the bundle" % entry.get("ModuleName"))
    if problems:
        raise SystemExit("OpenScene.bundle refused:\n  " + "\n  ".join(problems))


def build_bundle(version, dist=DIST):
    target = os.path.join(dist, "OpenScene.bundle")
    if os.path.isdir(target):
        shutil.rmtree(target)
    contents = os.path.join(target, "Contents")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
    shutil.copytree(os.path.join(PKG, "OpenScene"), os.path.join(contents, "OpenScene"), ignore=ignore)
    build_icons(os.path.join(contents, "icons"))
    os.makedirs(os.path.join(contents, "macroscripts"))
    shutil.copy2(os.path.join(PKG, "OpenScene.mcr"), os.path.join(contents, "macroscripts"))
    os.makedirs(os.path.join(contents, "scripts"))
    shutil.copy2(os.path.join(BUNDLE_SRC, "openscene_bundle.ms"), os.path.join(contents, "scripts"))
    with open(os.path.join(target, "PackageContents.xml"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(package_contents(version))
    check_bundle(target, version)
    return target


def main():
    # a MAXScript mistake only shows when 3ds Max runs the file: never put one in a bundle
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_ms

    if check_ms.main():
        sys.exit("not built: fix the MAXScript problems above first")
    version = read_version()
    print("built %s (%s)" % (build_bundle(version), version))


if __name__ == "__main__":
    main()
