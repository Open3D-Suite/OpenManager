# OpenScene · notes for Claude

Scene-setup and batch-render manager that runs inside 3ds Max 2025+: a Python / PySide6 window (`pymxs`, `qtmax`,
both shipped with Max) plus a MAXScript library. Installed by dragging `OpenScene.mzp` onto a viewport.
GitHub: `AdanCastellanos/OpenScene` (public, MIT, branch `main`).

## Talking to the user
- Always reply in **Spanish** (castellano).
- Repository docs (`README.md`, `AUDITORIA.md`, `CHANGELOG.md`) are in **Spanish**; code, comments, UI text and this
  file are in English.
- The user's own 3ds Max 2026 user folder is `%LOCALAPPDATA%\Autodesk\3dsMax\2026 - 64bit\ENU` (settings in
  `en-US\plugcfg`). It also holds files of other tools: when updating the install there, touch only OpenScene's files
  and the ones of this tool's earlier installs.

## Layout
| path | what |
|---|---|
| `package/OpenScene/openscene/` | Python: `window.py` (main dock, VERSION), `cards.py` / `cards2.py` (cards), `widgets.py`, `dialogs.py`, `maxlink.py` (everything that talks to Max), `model.py` (pure data, no Max or Qt), `external.py` (optional reader of another scene manager's setups), `props.json` (generated) |
| `package/OpenScene/openscene_core.ms` | MAXScript side; every global is prefixed `oscn_` |
| `package/OpenScene/OpenScene_startup.ms`, `package/OpenScene.mcr`, `package/install.ms`, `uninstall.ms` | startup check, macro button, installer, uninstaller |
| `tools/build.py` | draws the icons and builds `OpenScene.mzp` at the root (reproducible: same sources, same file) |
| `tools/props_source.py` → `tools/make_props.py` | the Property Selector tables → `props.json` |

## Rules
- **Never mention the tool's former names or the reference program it was inspired by**, in code, comments, UI, docs,
  commit messages or file names. Refer to it only as "another scene manager". The only allowed traces are the internal
  keys that convert files saved before 2.0.0: the legacy block in `openscene_core.ms` (the arrays `oscn_oldDat`, `oscn_oldMaps`,
  `oscn_oldMix`, two generations of keys, read by `oscn_readOldSetups`), the key list in `OpenScene_startup.ms` and
  `model.OLD_COMPRESSED_PREFIX`.
- **Own work only**: property labels, ranges and defaults are written by us in `tools/props_source.py`. Never copy
  labels, texts, tables or UI wording from other software. Property *names* are the renderers' public API and must
  match exactly.
- Setups are stored on `rootNode` in the `OpenScene_Dat` custom attribute (`oscn_data`, attribID
  `0x4f53cd21, 0x2e6a9b74`) and maps in `OpenScene_Maps` (`0x4f53cd22, 0x2e6a9b75`). Never reuse or change these IDs:
  a scripted attribute redefined with the same ID and other parameters wipes the stored data.
- Card ids, the `props` keys (`card|class|property`) and the settings files are what saved setups and layouts depend
  on: changing them needs a migration.
- The Layers and Objects cards show **one list shared by all setups** (`model.shared_rows`); each setup keeps its own
  values in its own `set`. Adding a row copies it to every setup (`cards.share_rows`, with the scene's current
  values), removing deletes it from all, new setups get the whole list (`window.share_lists`). A row a setup
  doesn't have yet is shown half ticked and is not applied; ticking it creates the entry from the scene.
- Decided by the user: the scene state carries over from one setup to the next (no reset between setups), and Corona
  Interactive is not stopped when a setup is applied (setting `ipr_corona_restart`, off by default).

## Working on it
- Card logic can be tested with real Qt outside Max: a scratch venv with `PySide6-Essentials`, `QT_QPA_PLATFORM=offscreen`,
  stand-in `pymxs` / `qtmax` modules and a small fake window object (`settings`, `setups`, `active()`, `scene`,
  `enabled_rows()`, `changed()`, `locked()`...).
- Nothing can be run inside 3ds Max from here. Check what can be checked: `py_compile` every module, load
  `model.py` / `external.py` standalone and test them, check that every `rt.oscn_*` used in Python is defined in the
  `.ms` files, and say clearly in the reply what still has to be tested in Max.
- **The Bash tool collapses `\\` to `\` even inside quoted heredocs.** Write or edit MAXScript files that contain
  backslashes with the Write / Edit tools, never through a shell heredoc, and check the string escapes afterwards
  (in MAXScript only `\\ \n \t \r \"` are valid).
- After changing `tools/props_source.py`, run `python tools/make_props.py`. After any change in `package/`, run
  `python tools/build.py` and commit the rebuilt `OpenScene.mzp`.

## Updating GitHub
Every push to GitHub includes, up to date:
1. `CHANGELOG.md`: a new entry (or additions to the current one) saying what changes for the user.
2. `CLAUDE.md`: this file, updated with anything new that a future session needs to know.
3. The version in `window.py` (`VERSION`) and `README.md` when it is a release, and the rebuilt `OpenScene.mzp`.

Commit as the repository's existing author name and email (`git log -1 --format='%an <%ae>'`), ending the message
with the Co-Authored-By line. Plain pushes only; ask before anything that rewrites history.
