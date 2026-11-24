# OpenManager

Scene setups and batch rendering for 3ds Max. A **setup** keeps, inside the `.max` file, what one shot of the scene
needs: camera, resolution, frames, sun, dome, environment, layers, objects, lights, XRefs, output path, render
settings, Corona VFB post-production and more. Click a setup and the scene follows; **Batch Render** renders every
ticked setup, one after the other. A plug-in that lives inside **3ds Max**, written in Python (the Python and Qt that
come with 3ds Max) and MAXScript: no separate program and no account.

OpenManager 3 is the plug-in that was called OpenScene up to version 2.2.2, and it replaces OpenManager 0.x, whose
code is archived in [OpenManager-Legacy](https://github.com/Open3D-Suite/OpenManager-Legacy).

> Status: early (v3.0.0).
> What each version adds: [CHANGELOG.md](CHANGELOG.md).

**3ds Max:** 2025 or newer, on Windows. OpenScene 2.x was used on 3ds Max 2026.3 with Corona 14. Version 3.0.0 has not
been through the real test in 3ds Max yet, so no version is listed as tested; 2025, 2026 and 2027 should work.

**Renderers:** Corona (every card), V-Ray and V-Ray GPU (tables included); FStorm, Redshift and Arnold with less
testing.

## Install

The easy way, with the [Open3D Launcher](https://github.com/Open3D-Suite/Open3D-Launcher/releases/latest): click
**Install** next to OpenManager, with 3ds Max closed. It puts OpenManager in `%APPDATA%\Autodesk\ApplicationPlugins`
as a plug-in bundle (every 3ds Max from 2025 on loads it), tells you when a new version is out and updates it.

By hand: each release of this repository has the bundle as a zip, `openmanager-<version>-windows-x64-3dsmax.zip`.
With 3ds Max closed, unzip it, copy the `OpenManager.bundle` folder into `%APPDATA%\Autodesk\ApplicationPlugins\`
and start 3ds Max. To remove it, delete that folder with 3ds Max closed.

- The first start adds an **OpenManager** toolbar with the button, floating: drag it where you want it. Nothing is
  added when a toolbar already has the button. The action is also in *Customize > Customize User Interface*, **Group:
  Main UI**, **Category: OpenManager**, to put it on another toolbar or in a menu.
- The **`.mzp` is retired**: OpenScene up to 2.2.2 came as `OpenScene.mzp`, and OpenManager up to 0.3.0
  as `OpenManager.mzp`. The first start of the bundle removes what they installed in 3ds Max's user folders, and
  an `OpenScene.bundle` in `ApplicationPlugins`: only their own files, said in the MAXScript Listener (your
  settings stay and are carried over). A button of OpenScene, on its toolbar or on one of yours, then opens
  OpenManager, and a button of OpenManager 0.x keeps working: it is the same action.
- Setups are saved **inside the `.max` file** (the `OpenScene_Dat` attribute of the root node, the name it has had
  since OpenScene). Installing or removing OpenManager never touches them.

OpenManager keeps its settings in `%APPDATA%\Open3D\OpenManager` (one set for every 3ds Max) and everything else it
writes (HDRI previews, the backup of the interface file made before the toolbar is added, the thumbnails, exports and
presets of a scene not saved yet) in `%LOCALAPPDATA%\Open3D\OpenManager`; delete those folders too for a clean
removal.

**Coming from OpenManager 0.x or OpenScene:** the first start copies, once, the settings and HDRI previews of
OpenManager 0.x (in the same folders, under names of their own: `OpenManager.json`...), of OpenScene 3
(`%APPDATA%\Open3D\OpenScene`, `%LOCALAPPDATA%\Open3D\OpenScene`) or of OpenScene 2.x (the `plugcfg` folder of
3ds Max), whichever were changed last, and leaves the old files as they were. The scripts 0.x trusted stay
trusted. The MAXScript Listener says what was copied, and what has no counterpart here.

## Use

Open it with the **OpenManager** button. Make a setup with **+** (empty), the camera button (the scene as it is now)
or one per camera, switch on the cards you need, and set what each one changes. Click another setup to apply it.

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
  write or choose in OpenManager on this computer runs without asking.
- **Setups OpenManager 0.x saved in a `.max`** are read and converted, every card, and so are those another
  scene manager saved; the MAXScript Listener says what could not be taken. Their data stays in the file as
  it was, and once the file is saved with OpenManager's own setups, nothing is asked again.
- Setup and output presets are `.osp` files (`.smp` files exported earlier open too).
- **Double-click a card's colour bar** to fold it to the bar; again to unfold it.

The interface is in English only.

## If something goes wrong

Copy what the **MAXScript Listener** (F11) shows: OpenManager's lines start with `OpenManager`.

Known limits are in [docs/audit.md](docs/audit.md). Post-Production / VFB works with Corona only, and so does the
`.cxr` output (render elements and the LightMix go inside the one `.cxr`).

## Development

- `package/OpenManager/` is what goes in the bundle: the Python package `openmanager/`, the MAXScript library
  `openmanager_core.ms` and the file-open check `OpenManager_startup.ms`. `package/OpenManager.mcr` is the macro and
  `bundle/openmanager_bundle.ms` the bundle's start-up script.
- `python tools/build.py` writes `dist/OpenManager.bundle` (plain Python 3, nothing to install): it checks the
  MAXScript files (`tools/check_ms.py`), draws the icons and writes `PackageContents.xml` with the version.
- `tools\check.ps1` runs every check: it needs Python 3.11 or newer and the ruff that `ruff.toml` names. The tests
  need no 3ds Max: `python -I tests/run.py`.
- `python -I tools/repo.py package` runs the checks, builds the bundle and writes the release zip to `dist/`.
- `python tools/make_props.py` writes `props.json`, the tables of the Property Selector, from `tools/props_source.py`.
- What the security review needs: [docs/security-review.md](docs/security-review.md).

## License

Copyright (C) 2026 Daniel Castellanos and OpenManager contributors.

OpenManager is free software under the GNU General Public License, version 3 or later (`GPL-3.0-or-later`). See
[`LICENSE`](LICENSE). OpenScene up to 2.2.2 was published under the MIT licence; copies of those versions keep it.

OpenManager is an independent project, not affiliated with, sponsored or endorsed by Autodesk, Chaos or any other
maker. 3ds Max is a trademark of Autodesk, Inc.; Corona and V-Ray are trademarks of Chaos Software; FStorm, Redshift,
Arnold and the other product names belong to their owners and are named only to say what OpenManager works with. The
icons of the interface are drawn at run time with Windows' own symbol font (not redistributed) and shapes of its own.
