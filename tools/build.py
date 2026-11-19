"""Builds OpenScene.mzp (next to the README): draws the icons, then zips the package.

    python tools/build.py

Pure Python, nothing to install.
"""
import os
import struct
import zipfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "package")
ICON_NAME = "OpenScene"
SIZES = (16, 24, 30, 32, 36, 48)


# ---------------------------------------------------------------- icon: just the puzzle piece, in greys

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
            row.append(tuple(int(round(c0[k] + (c1[k] - c0[k]) * t)) for k in range(3)) + (int(round(cov * 255.0 / (ss * ss))),))
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


def build_icons():
    out = os.path.join(PKG, "icons")
    for theme in THEMES:
        folder = os.path.join(out, theme)
        os.makedirs(folder, exist_ok=True)
        for s in SIZES:
            write_png(os.path.join(folder, "%s_%d.png" % (ICON_NAME, s)), draw_icon(s, theme))


# ---------------------------------------------------------------- package

def build_mzp():
    target = os.path.join(ROOT, "OpenScene.mzp")
    if os.path.exists(target):
        os.remove(target)
    # sorted names and a fixed date: the same sources give the same .mzp, so git only sees it change when they do
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(PKG):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for f in sorted(files):
                if f.endswith((".pyc", ".pyo")):
                    continue
                full = os.path.join(base, f)
                info = zipfile.ZipInfo(os.path.relpath(full, PKG).replace(os.sep, "/"), (2025, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                with open(full, "rb") as src:
                    z.writestr(info, src.read())
        # the MIT licence travels with every copy: installed next to the scripts
        info = zipfile.ZipInfo("OpenScene/LICENSE", (2025, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        with open(os.path.join(ROOT, "LICENSE"), "rb") as src:
            z.writestr(info, src.read())
    return target


if __name__ == "__main__":
    # a MAXScript mistake only shows when 3ds Max runs the file: never package one
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_ms
    if check_ms.main():
        sys.exit("not built: fix the MAXScript problems above first")
    build_icons()
    t = build_mzp()
    print("built %s (%d KB)" % (t, os.path.getsize(t) // 1024))
