# SPDX-License-Identifier: GPL-3.0-or-later
"""Small icons drawn at run time: Windows' own symbol font plus a few hand-drawn shapes.
Nothing to ship, sharp at any DPI."""

from PySide6 import QtCore, QtGui

_CACHE = {}
# cacheKey of a glyph icon -> (name, color, size, base size): a theme or icon-size change redraws icons that exist
_ORIGIN = {}

GLYPH = {
    "add": "",
    "delete": "",
    "copy": "",
    "paste": "",
    "camera": "",
    "refresh": "",
    "lock": "",
    "unlock": "",
    "color": "",
    "import": "",
    "export": "",
    "list": "",
    "stop": "",
    "sun": "",
    "globe": "",
    "folder": "",
    "eye": "",
    "hide": "",
    "edit": "",
    "more": "",
    "close": "",
    "filter": "",
    "photo": "",
    "clock": "",
    "layers": "",
    "link": "",
    "bulb": "",
    "save": "",
    "grip": "",
    "menu": "",
    "pick": "",
    "up": "",
    "down": "",
    "expand": "",
    "shrink": "",
    "fetch": "",
    "cube": "",
    "settings": "",
    "note": "",
    "check": "",
    "checklist": "",
    "cards": "",
    "cut": "",
    "select": "",
    "dup": "",
    "transfer": "",
    "text": "",
    "resolution": "",
    "image": "",
    "dome": "",
    "mountain": "",
    "wind": "",
    "swatch": "",
    "sliders": "",
    "preset": "",
    "elements": "",
    "post": "",
    "codefile": "",
    "code": "",
    "view": "",
    "sync": "",
    "bake": "",
    "play": "",
    "pin": "",
    "wand": "",
    "magic": "",
    "gear": "",
    "folderopen": "",
    "minus": "",
}


def _font(px):
    f = QtGui.QFont("Segoe Fluent Icons")
    if not QtGui.QFontInfo(f).exactMatch():
        f = QtGui.QFont("Segoe MDL2 Assets")
    f.setPixelSize(px)
    return f


def glyph(name, color, size=16, base=None):
    """base: the size asked for before the icon-size setting scaled it (to redraw it at another scale)."""
    key = ("g", name, QtGui.QColor(color).rgba(), size, base or size)
    if key in _CACHE:
        return _CACHE[key]
    icon = QtGui.QIcon()
    for scale in (1, 2):
        pm = QtGui.QPixmap(size * scale, size * scale)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.setPen(QtGui.QColor(color))
        p.setFont(_font(int(size * scale * 0.8)))
        p.drawText(pm.rect(), QtCore.Qt.AlignCenter, GLYPH.get(name, name))
        p.end()
        pm.setDevicePixelRatio(scale)
        icon.addPixmap(pm)
    _CACHE[key] = icon
    _ORIGIN[icon.cacheKey()] = (name, QtGui.QColor(color).rgba(), size, base or size)
    return icon


def recolor(icon, old_color, new_color):
    """The same glyph in the new colour, or None when this icon isn't a glyph drawn in old_color."""
    o = _ORIGIN.get(icon.cacheKey())
    if o is None or o[1] != QtGui.QColor(old_color).rgba():
        return None
    return glyph(o[0], new_color, o[2], o[3])


def base_size(icon):
    """The size a glyph icon was asked for (before scaling), or None when it isn't a glyph."""
    o = _ORIGIN.get(icon.cacheKey())
    return o[3] if o else None


def rescale(icon, px):
    """The same glyph drawn at px(base size); None when this icon isn't a glyph."""
    o = _ORIGIN.get(icon.cacheKey())
    if o is None:
        return None
    return glyph(o[0], QtGui.QColor.fromRgba(o[1]), px(o[3]), o[3])


def teapot_path(r):
    """A teapot silhouette inside rect r (body, lid with knob, curved spout, ring handle)."""
    x, y, w, h = r.x(), r.y(), r.width(), r.height()

    def P(fx, fy):
        return QtCore.QPointF(x + w * fx, y + h * fy)

    path = QtGui.QPainterPath()
    path.addEllipse(QtCore.QRectF(P(0.20, 0.36), P(0.80, 0.88)))
    lid = QtGui.QPainterPath()
    lid.addEllipse(QtCore.QRectF(P(0.33, 0.28), P(0.67, 0.44)))
    path = path.united(lid)
    knob = QtGui.QPainterPath()
    knob.addEllipse(P(0.50, 0.22), w * 0.07, h * 0.07)
    path = path.united(knob)
    spout = QtGui.QPainterPath()
    spout.moveTo(P(0.27, 0.52))
    spout.quadTo(P(0.12, 0.54), P(0.02, 0.30))
    spout.lineTo(P(0.12, 0.30))
    spout.quadTo(P(0.17, 0.46), P(0.30, 0.74))
    spout.closeSubpath()
    path = path.united(spout)
    handle = QtGui.QPainterPath()
    handle.addEllipse(QtCore.QRectF(P(0.68, 0.42), P(0.98, 0.76)))
    hole = QtGui.QPainterPath()
    hole.addEllipse(QtCore.QRectF(P(0.75, 0.50), P(0.91, 0.68)))
    return path.united(handle.subtracted(hole)).simplified()


def teapot(color, filled=True, size=18):
    key = ("t", QtGui.QColor(color).rgba(), filled, size)
    if key in _CACHE:
        return _CACHE[key]
    icon = QtGui.QIcon()
    for scale in (1, 2):
        pm = QtGui.QPixmap(size * scale, size * scale)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        path = teapot_path(QtCore.QRectF(0.5, 0.5, size * scale - 1, size * scale - 1))
        c = QtGui.QColor(color)
        if filled:
            p.fillPath(path, c)
        else:
            p.setPen(QtGui.QPen(c, 1.1 * scale))
            p.drawPath(path)
        p.end()
        pm.setDevicePixelRatio(scale)
        icon.addPixmap(pm)
    _CACHE[key] = icon
    return icon


# A stack of three setup cards (x0, y0, x1, y1), the front one first: OpenManager's icon in the Open3D launcher,
# the same shape as the toolbar icons tools/build.py draws (CARDS there)
CARDS = ((0.08, 0.38, 0.68, 0.92), (0.20, 0.23, 0.80, 0.77), (0.32, 0.08, 0.92, 0.62))
CARD_RADIUS, CARD_GAP = 0.08, 0.055


def logo_path(r):
    """The logo inside rect r: the front card whole, and each card behind it only where it shows past a gap."""
    x, y, w, h = r.x(), r.y(), r.width(), r.height()

    def card(c, grow=0.0):
        p = QtGui.QPainterPath()
        rect = QtCore.QRectF(
            x + w * (c[0] - grow), y + h * (c[1] - grow), w * (c[2] - c[0] + 2 * grow), h * (c[3] - c[1] + 2 * grow)
        )
        p.addRoundedRect(rect, w * (CARD_RADIUS + grow), h * (CARD_RADIUS + grow))
        return p

    path = card(CARDS[0])
    for i in (1, 2):
        path = path.united(card(CARDS[i]).subtracted(card(CARDS[i - 1], CARD_GAP)))
    return path


def app_icon(dark=True):
    """The logo: a stack of setup cards in greys, as in the launcher. Silver on dark interfaces, graphite on light."""
    key = ("app", bool(dark))
    if key in _CACHE:
        return _CACHE[key]
    a, b = ("#ffffff", "#a4a4a4") if dark else ("#5c5c5c", "#141414")
    icon = QtGui.QIcon()
    for size in (16, 24, 32, 48, 64):
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        g = QtGui.QLinearGradient(0, 0, size, size)
        g.setColorAt(0, QtGui.QColor(a))
        g.setColorAt(1, QtGui.QColor(b))
        p.fillPath(logo_path(QtCore.QRectF(0, 0, size, size)), QtGui.QBrush(g))
        p.end()
        icon.addPixmap(pm)
    _CACHE[key] = icon
    return icon
