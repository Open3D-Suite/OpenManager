# Changelog

What changed for users in each version of OpenManager, newest first. Up to 2.2.2 it was called OpenScene; what
OpenManager 0.x changed is in the CHANGELOG of OpenManager-Legacy.

## 3.0.2 — 2026-11-27

- **Fixed:** 3ds Max could stop with an *EXCEPTION_ACCESS_VIOLATION* when a line, a rectangle or a tape was
  cancelled with a right-click while OpenManager was open: OpenManager no longer reads the scene while an object is
  being created.

## 3.0.1 — 2026-11-26

- **Fixed:** clicking OpenManager's toolbar button said *OpenManager is not installed* from the second start of
  3ds Max on, once the button was on a toolbar. The button now finds OpenManager however early 3ds Max asks it.
- The icon in 3ds Max (the toolbar button and the logo of the window) is now OpenManager's icon in the Open3D
  launcher, a stack of three cards, instead of the puzzle piece.

## 3.0.0 — 2026-11-24

**OpenScene is now OpenManager, and it replaces OpenManager 0.x.** The Open3D launcher offers it as the update of
OpenManager. Everything you see is called OpenManager: the bundle (`OpenManager.bundle`), the toolbar, the action
(*Category: OpenManager*), the window and the lines of the MAXScript Listener, and its folders are
`%APPDATA%\Open3D\OpenManager` and `%LOCALAPPDATA%\Open3D\OpenManager`. Scenes made with OpenScene keep their
setups, which stay where OpenScene saved them.

What a user of OpenManager 0.x keeps:

- **The setups of their scenes.** A `.max` with setups of OpenManager 0.x opens with them, converted, every
  card as 0.x kept it; the file-open check offers to open the window to convert them, a message says how many
  were converted, and the MAXScript Listener says what was not taken. Saving the file adds the setups of this
  version, which are the ones read from then on; those of 0.x stay in the file as they were. Not taken: the
  scene state 0.x kept to put back between setups (this version leaves the scene as the setup before left it),
  and the IDs 0.x gave the nodes and layers of its setups, which are found again by handle and name and get
  IDs of this version when the file is saved. The maps 0.x kept for its setups are found too, and its
  environment mixes are taken for mixes, not offered as environments.
- **Their settings**, copied once, at the first start, from the files 0.x kept in
  `%APPDATA%\Open3D\OpenManager`: the notification switch, the theme, the cards shown and their layout, the
  columns, the place of the window, the resolution presets, the Property Selector ticks, the HDRI folders and
  previews, *Settings > 3ds Max*, and the scripts and render presets 0.x trusted (a file as it is now, a script
  as soon as a setup runs it again). The files of 0.x are left as they were, and this version never reads them
  as its own: its files have other names. Not taken, and said in the MAXScript Listener: putting the scene
  back between setups, and *Always run them* or *Never run them* for the scripts of a file (this version
  shows them and asks).

A user of OpenScene keeps their settings the same way: those of OpenScene 3 (in `%APPDATA%\Open3D\OpenScene`
and `%LOCALAPPDATA%\Open3D\OpenScene`, but for its toolbar's files: the OpenManager toolbar is placed anew) or of
OpenScene 2.x (in `plugcfg`). When both OpenScene and OpenManager 0.x left settings, those changed last are
taken, and the Listener says so. No file is copied over one that is there; a copy that fails leaves that
session on the old settings, and the next start tries again.

Version 3.0.0 also follows the rules of the Open3D suite, to be installed and updated by the Open3D launcher.

- **Installed as a plug-in bundle**, `OpenManager.bundle` in `%APPDATA%\Autodesk\ApplicationPlugins`, by the launcher
  or by hand. The `.mzp` installer and the uninstaller are retired: the first start of the bundle removes what the
  `.mzp` of OpenScene or of OpenManager 0.x installed in 3ds Max's user folders, and an `OpenScene.bundle` in
  `ApplicationPlugins` (your settings stay). Only their own files are taken, and the MAXScript Listener says what
  was removed.
- The **OpenManager toolbar** is added at the first start, once, and only when no toolbar has the button yet. The
  interface file is backed up first in OpenManager's data folder and put back if anything fails. The buttons of
  OpenScene, on its toolbar or on one of your own, open OpenManager instead, and the OpenScene toolbar takes
  OpenManager's name; the buttons of OpenManager 0.x keep working, as the action is the same.
- **Settings move** to `%APPDATA%\Open3D\OpenManager`, one set for every 3ds Max, and the HDRI previews to
  `%LOCALAPPDATA%\Open3D\OpenManager`, where the first start copies those of the versions before (above).
- **Scripts and render presets that come inside a file are asked about before they run**: the Script Editor, Script
  File and Render Preset cards of a `.max` made on another computer. OpenManager shows what would run and asks, with No
  as the answer Enter gives; a no holds until the window is closed. What you write or choose in OpenManager on this
  computer runs without asking, and so does what you said yes to, until it changes.
- **A file can no longer make OpenManager run code through a name**: the class of an environment map or of a
  tone-mapping operator stored in a setup is checked to be a plain name and looked up among 3ds Max's classes, never
  run. Render Override, Post-Production and LightMix settings take only plain property names and plain values.
- **Setups saved by a newer OpenManager are refused, not guessed at**: they stay in the file as they are, and what you
  change is not saved over them. So do setups that are damaged or bigger than OpenManager reads.
- **Setups keep their objects and layers through renames and merges.** Every camera, sun, dome, light, object and
  layer a setup uses gets an ID of its own, stored with it in the scene when the setups are saved, so OpenManager finds
  it again: a renamed layer stays in the Layers and Variants cards (before, it was lost), a renamed object keeps
  working, and nodes merged into another file, which get new handles there, are found by their ID, Lights card
  settings included. A handle that now belongs to another object is never used: an imported setup could otherwise
  change whatever object had the same handle in the new file. A deleted object stays in its setups and is found again
  if it comes back. Setups saved before get their IDs the next time the file is saved.
- **Faster with many maps.** The maps are found by walking from what holds them (the materials, the environment, the
  Material Editors and the texture-map settings of the renderer, cameras and lights), once, instead of going through
  the whole scene once for each kind of map; and a setup looks its maps up in a list made at each read of the scene.
  The map list of the texture-map settings, the Environment card and applying a setup no longer slow down with the
  size of the scene. When several maps share a name, the one with the HDRI or sky in it still wins.
- **Batch Render never renders without saving.**
  - Names are cleaned for Windows: what Windows does not allow in a file name (`: * ? " < > |`) becomes `_`, so a
    camera called `CAM:Bad` saves as `CAM_Bad.png`, and folder names lose the dots and spaces Windows would drop.
  - The Render Output card says what is missing under a red path ("The Camera token has no value (the setup has no
    camera)", "No Extension token"...). Clicking such a setup leaves the scene's own output as it is; before, it
    switched saving off.
  - Before the batch starts, a setup that would save nothing (an incomplete path, or its card off and no output in
    the scene) or whose camera is gone is listed with why and skipped; you render the others or cancel.
  - After each render the file is looked for, and a setup that saved nothing counts as failed. At the end, every
    setup is listed in the MAXScript Listener: saved and where, skipped or failed, and why.
- **A render preset no longer brings the scripts of Render Setup.** A `.rps` file also keeps Render Setup's pre- and
  post-render scripts (*Common > Scripts*), so a preset could set a script that runs at the next render. When
  OpenManager loads a preset, those scripts are left as they were, also when the load fails.
- **Enter always answers No** in the question about scripts and presets, wherever the focus is; Yes takes a click or
  Space on its button.
- **Bake Setups asks once, before it starts**, about the scripts and presets of the setups it applies, as Batch Render
  does, instead of in the middle of the run.
- **A variant decides whether its layers are on**, also after an edit of the Layers card, which before could turn a
  layer of a variant on or off against it until the setup was clicked again.
- Maps saved under a class's older name (V-Ray's `VRayHDRI`, now `VRayBitmap`) are found again.
- A value of the wrong kind in a stored setup gets its default instead of breaking the window, a row of a list that is
  not a row is left out, and a repeated setup id gets a new one.
- **Render Output takes only absolute paths** (a drive or a network share) without `..` and without characters
  Windows refuses: a relative path, or one that steps up, is shown in orange and the render is not saved there.
- **Preset files (`.osp`, `.smp`) are read with the same checks**: one saved by a newer OpenManager, too big or broken is
  refused and the reason is said; an output preset sets only the settings of the Render Output card.
- The repository is now at `github.com/Open3D-Suite/OpenManager`, with the other apps of the suite.
- The licence is now the GNU General Public License, version 3 or later. Versions up to 2.2.2 keep the MIT licence.
- Settings are written whole into a new file that then takes the old one's place, so a crash never leaves them half
  written.

## 2.2.2 — 2026-11-19

- **The installer works again**: the one of 2.2.0 and 2.2.1 stopped as soon as it was dragged in, with *"Syntax
  error: at at, expected name"* (a variable had the name of a word MAXScript keeps for itself), and installed nothing.
- The MAXScript files are checked before the package is built, so that such a mistake never reaches a package again.

## 2.2.1 — 2026-11-19

- **Environment with a Color Correct over the HDRI**: choosing it in OpenScene no longer gives a background of another
  colour (yellow, say). When several maps share a name (maps named after their class, models merged from other files,
  copies), OpenScene could take the Color Correct of a material instead of the one over the HDRI. It now always takes
  the one with the HDRI or the sky below it, and the HDRI's settings (rotation, file...) never go to a material's
  bitmap of the same name.
- The repository is now at `github.com/daniellopezcastellanos/OpenScene`.

## 2.2.0 — 2026-11-18

- **The installer puts the button on a toolbar**: it makes an **OpenScene** toolbar with the button. Nothing is added
  when a toolbar already has it. The interface is backed up before it is changed and put back if anything fails.
- The uninstaller removes that toolbar (a toolbar of your own with the button is left alone).

## 2.1.1 — 2026-11-18

- `.max` files saved with the first versions of the tool (before 1.4) open with their setups and environment mixes
  too; when saved, they move to the new key. Before, only those of 1.4 to 1.6 were converted.

## 2.1.0 — 2026-11-18

- **Layers and Objects: one list for every setup.** The layers and objects added in a setup (with "+" or with fetch)
  are in every other setup, with the state they have in the scene at that moment; from then on each setup keeps its
  own ticks. A layer can be hidden in one setup and visible in another without adding it again.
- A new setup starts with the whole list (and with Layers / Objects on when another setup uses them).
- The rows another setup has but this one does not set yet are shown in italics and half ticked: they are not changed
  when the setup is applied (they stay as the previous setup left them) until you tick a box.
- Removing a row removes it from the list of every setup.
- `.max` files saved before do not change when opened: their lists are joined on screen only.

## 2.0.0 — 2026-11-13

First published version of **OpenScene**.

- Scene setups inside the `.max` file: camera, resolution, frames, sun, dome, environment (several HDRIs or skies
  mixed), layers, objects, lights, XRefs, output, render settings, render elements, Corona VFB post-production,
  scripts, thumbnail, notes and todo.
- **Batch Render** with a check before it starts (a missing camera, paths, two setups writing the same file, scripts
  or presets that do not exist); one failure does not stop the batch; the time of each setup and the time left.
- **`.cxr`** output with Corona: render elements and the LightMix inside the same file.
- **Property Selector** with tables of its own for 3ds Max, Corona, V-Ray, V-Ray GPU and FStorm
  (`tools/props_source.py`).
- Setup and output presets in **`.osp`** files (`.smp` files open too).
- Reads and converts the setups another scene manager saved in the `.max` file (`external.py`).
- Made for big scenes: only the objects the setups use are read, bursts of scene events are grouped, and big setups
  are stored packed inside the `.max` file.
- `.mzp` installer (3ds Max 2025+), uninstaller and MIT licence.
