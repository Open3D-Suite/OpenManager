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


def puzzle_path(r):
    """Puzzle piece filling rect r: a square body, knobs on top and right, sockets on left and bottom."""
    k = 1.35  # the piece spans 0.67 of the drawing below
    x, y, w, h = r.x(), r.y(), r.width() * k, r.height() * k
    ox, oy = r.width() * 0.5 - w * 0.535, r.height() * 0.5 - h * 0.445

    def u(fx, fy):
        return QtCore.QPointF(x + ox + w * fx, y + oy + h * fy)

    body = QtGui.QPainterPath()
    body.addRoundedRect(QtCore.QRectF(u(0.20, 0.30), u(0.68, 0.78)), w * 0.05, h * 0.05)
    knob = QtGui.QPainterPath()
    knob.addEllipse(u(0.44, 0.215), w * 0.105, h * 0.105)
    body = body.united(knob)
    knob = QtGui.QPainterPath()
    knob.addEllipse(u(0.765, 0.54), w * 0.105, h * 0.105)
    body = body.united(knob)
    hole = QtGui.QPainterPath()
    hole.addEllipse(u(0.20, 0.54), w * 0.085, h * 0.085)
    body = body.subtracted(hole)
    hole = QtGui.QPainterPath()
    hole.addEllipse(u(0.44, 0.78), w * 0.085, h * 0.085)
    return body.subtracted(hole)


def app_icon(dark=True):
    """The logo: just the puzzle piece in greys. Silver on dark interfaces, graphite on light ones."""
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
        p.fillPath(puzzle_path(QtCore.QRectF(0, 0, size, size)), QtGui.QBrush(g))
        p.end()
        icon.addPixmap(pm)
    _CACHE[key] = icon
    return icon
