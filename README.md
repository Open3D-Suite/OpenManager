# OpenScene

Scene setups and batch rendering for 3ds Max. A **setup** keeps, inside the `.max` file, what one shot of the scene
needs: camera, resolution, frames, sun, dome, environment, layers, objects, lights, XRefs, output path, render
settings, Corona VFB post-production and more. Click a setup and the scene follows; **Batch Render** renders every
ticked setup, one after the other. A plug-in that lives inside **3ds Max**, written in Python (the Python and Qt that
come with 3ds Max) and MAXScript: no separate program and no account.

> Status: early (v3.0.0).
> What each version adds: [CHANGELOG.md](CHANGELOG.md).

**3ds Max:** 2025 or newer, on Windows. Version 2.x was used on 3ds Max 2026.3 with Corona 14. Version 3.0.0 has not
been through the real test in 3ds Max yet, so no version is listed as tested; 2025, 2026 and 2027 should work.

**Renderers:** Corona (every card), V-Ray and V-Ray GPU (tables included); FStorm, Redshift and Arnold with less
testing.

## Install

The easy way, once OpenScene is in the [Open3D Launcher](https://github.com/carlesllavata/Open3D/releases/latest):
click **Install** next to OpenScene, with 3ds Max closed. It puts OpenScene in `%APPDATA%\Autodesk\ApplicationPlugins`
as a plug-in bundle (every 3ds Max from 2025 on loads it), tells you when a new version is out and updates it.

By hand: each release of this repository has the bundle as a zip, `openscene-<version>-windows-x64-3dsmax.zip`. With
3ds Max closed, unzip it, copy the `OpenScene.bundle` folder into `%APPDATA%\Autodesk\ApplicationPlugins\` and start
3ds Max. To remove it, delete that folder with 3ds Max closed.

- The first start adds an **OpenScene** toolbar with the button, floating: drag it where you want it. Nothing is added
  when a toolbar already has the button. The action is also in *Customize > Customize User Interface*, **Group: Main
  UI**, **Category: OpenScene**, to put it on another toolbar or in a menu.
- The **`.mzp` is retired**: versions up to 2.2.2 came as `OpenScene.mzp`. If OpenScene was installed with it, the
  first start of the bundle removes that copy (your settings stay and are carried over).
- Setups are saved **inside the `.max` file** (the `OpenScene_Dat` attribute of the root node). Installing or removing
  OpenScene never touches them.

OpenScene keeps its settings in `%APPDATA%\Open3D\OpenScene` (one set for every 3ds Max) and everything else it
writes (HDRI previews, the backup of the interface file made before the toolbar is added, the thumbnails, exports and
presets of a scene not saved yet) in `%LOCALAPPDATA%\Open3D\OpenScene`; delete those folders too for a clean removal.
Version 2.x kept its settings in the `plugcfg` folder of each 3ds Max: the first start copies them, and the HDRI
previews, and leaves the old ones as they were.

## Use

Open it with the **OpenScene** button. Make a setup with **+** (empty), the camera button (the scene as it is now) or
one per camera, switch on the cards you need, and set what each one changes. Click another setup to apply it.

**Cards:** Scene Name, Camera, Resolution, Time Output, Sun (several suns or Daylights in tabs), Lights, HDRI
Browser, Environment (several HDRIs or skies mixed like a LightMix), Dome, Background, Atmosphere, Layers, Objects,
XRef Scenes, Variants, Render Output, Render Settings, Render Override, Render Preset, Render Elements,
Post-Production / VFB (Corona), Script File, Script Editor, Thumbnail, Todo and Notes. Each setting is picked in the
**Property Selector**, and its pencil takes the value from the scene.

- **Layers and Objects share one list across setups**: a row added in one setup is in all of them, and each setup
  keeps its own ticks (hidden in one, visible in another). A half-ticked row is on the list but this setup does not
  set it yet; ticking it does. Removing a row removes it from every setup.
- **A setup changes only what its cards set**: what it does not set stays as the previous setup left it.
- **Scripts and render presets that come inside a file** (the Script Editor, Script File and Render Preset cards of a
  `.max` made elsewhere) are shown and asked about before they run, with **No** as the answer Enter gives. What you
  write or choose in OpenScene on this computer runs without asking.
- Setups another scene manager saved in a `.max` are read and converted; once the file is saved with OpenScene's own,
  nothing is asked again.
- Setup and output presets are `.osp` files (`.smp` files exported earlier open too).
- **Double-click a card's colour bar** to fold it to the bar; again to unfold it.

The interface is in English only.

## If something goes wrong

Copy what the **MAXScript Listener** (F11) shows: OpenScene's lines start with `OpenScene`.

Known limits are in [docs/audit.md](docs/audit.md). Post-Production / VFB works with Corona only, and so does the
`.cxr` output (render elements and the LightMix go inside the one `.cxr`).

## Development

- `package/OpenScene/` is what goes in the bundle: the Python package `openscene/`, the MAXScript library
  `openscene_core.ms` and the file-open check `OpenScene_startup.ms`. `package/OpenScene.mcr` is the macro and
  `bundle/openscene_bundle.ms` the bundle's start-up script.
- `python tools/build.py` writes `dist/OpenScene.bundle` (plain Python 3, nothing to install): it checks the MAXScript
  files (`tools/check_ms.py`), draws the icons and writes `PackageContents.xml` with the version.
- `tools\check.ps1` runs every check: it needs Python 3.11 or newer and the ruff that `ruff.toml` names. The tests
  need no 3ds Max: `python -I tests/run.py`.
- `python -I tools/repo.py package` runs the checks, builds the bundle and writes the release zip to `dist/`.
- `python tools/make_props.py` writes `props.json`, the tables of the Property Selector, from `tools/props_source.py`.
- What the security review needs: [docs/security-review.md](docs/security-review.md).

## License

Copyright (C) 2026 Daniel Castellanos and OpenScene contributors.

OpenScene is free software under the GNU General Public License, version 3 or later (`GPL-3.0-or-later`). See
[`LICENSE`](LICENSE). Versions up to 2.2.2 were published under the MIT licence; copies of those keep it.

OpenScene is an independent project, not affiliated with, sponsored or endorsed by Autodesk, Chaos or any other
maker. 3ds Max is a trademark of Autodesk, Inc.; Corona and V-Ray are trademarks of Chaos Software; FStorm, Redshift,
Arnold and the other product names belong to their owners and are named only to say what OpenScene works with. The
icons of the interface are drawn at run time with Windows' own symbol font (not redistributed) and shapes of its own.
