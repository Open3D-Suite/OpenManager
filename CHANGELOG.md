# Changelog

What changed for users in each version of OpenScene, newest first.

## In development

Version 3.0.0: OpenScene follows the rules of the Open3D suite, to be installed and updated by the Open3D launcher.

- **Installed as a plug-in bundle**, `OpenScene.bundle` in `%APPDATA%\Autodesk\ApplicationPlugins`, by the launcher
  or by hand. The `.mzp` installer and the uninstaller are retired: the first start of the bundle removes the copy the
  `.mzp` installed (your settings stay).
- The **OpenScene toolbar** is added at the first start, once, and only when no toolbar has the button yet. The
  interface file is backed up first in OpenScene's data folder and put back if anything fails.
- **Settings move** to `%APPDATA%\Open3D\OpenScene`, one set for every 3ds Max, and the HDRI previews to
  `%LOCALAPPDATA%\Open3D\OpenScene`. The first start copies those of the earlier version from the `plugcfg` folder
  and leaves the old ones as they were.
- **Scripts and render presets that come inside a file are asked about before they run**: the Script Editor, Script
  File and Render Preset cards of a `.max` made on another computer. OpenScene shows what would run and asks, with No
  as the answer Enter gives; a no holds until the window is closed. What you write or choose in OpenScene on this
  computer runs without asking, and so does what you said yes to, until it changes.
- **A file can no longer make OpenScene run code through a name**: the class of an environment map or of a
  tone-mapping operator stored in a setup is checked to be a plain name and looked up among 3ds Max's classes, never
  run. Render Override, Post-Production and LightMix settings take only plain property names and plain values.
- **Setups saved by a newer OpenScene are refused, not guessed at**: they stay in the file as they are, and what you
  change is not saved over them. So do setups that are damaged or bigger than OpenScene reads.
- A value of the wrong kind in a stored setup gets its default instead of breaking the window, and a repeated setup id
  gets a new one.
- **Render Output takes only absolute paths** (a drive or a network share) without `..` and without characters
  Windows refuses: a relative path, or one that steps up, is shown in orange and the render is not saved there.
- **Preset files (`.osp`, `.smp`) are read with the same checks**: one saved by a newer OpenScene, too big or broken is
  refused and the reason is said; an output preset sets only the settings of the Render Output card.
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
