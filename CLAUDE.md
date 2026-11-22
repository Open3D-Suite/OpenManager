# OpenScene

Scene setups and batch rendering for 3ds Max: a setup, stored inside the `.max` file, says what one shot needs
(camera, resolution, environment, layers, render settings...) and Batch Render renders the ticked ones. One 3ds Max
plug-in, written in Python (Qt, pymxs) and MAXScript; nothing is compiled.

This file holds facts about this repo only, each one checkable in the code, and how we work on it.
Update it in the same commit as a change that makes it old.

## How we work

- **Language.** Talk to the author in their own language (Spanish). Everything written in the repo is in English:
  code, comments, commits, documents, CHANGELOG, releases.
- **The author decides.** A working or design criterion is never decided alone: ask, one question at a time, with 2
  to 4 options, your recommendation and why. What every Open3D app shares (the common files, the shared settings, the
  checks) is decided by Open3D's maintainers, and they approve what enters the Open3D launcher: once the checks and
  the CI pass, after a review of the code, of its security and a real test as a user.
- **The code is the truth.** Check a claim in the code before relying on it.
- **Plan first.** Before a large change, show a plan and wait for the author's OK.
- **Commits.** Small, one step each, with one English sentence in the imperative. A format commit carries no code
  change. A change a user can notice gets its entry in `CHANGELOG.md`, under `## In development`, in the same commit.
  Commit as the repository's author (`git log -1 --format='%an <%ae>'`).
- **Pull requests.** Changes reach `main` through pull requests: work on a branch, the CI passes, someone reviews it,
  then it is merged.
- **Nothing goes out without the author's explicit OK:** no push, no tag, no release. A release stays a draft on
  GitHub, and Open3D's maintainer publishes it. Tags are annotated, `vX.Y.Z`, and pushed one at a time, never with
  `--tags`. Never rewrite published history.
- **Nothing is deleted without asking the author first,** each time.
- **After a change** the plug-in must pass `tools\check.ps1` and load in 3ds Max.
- **Testing in 3ds Max.** A version is not ready until it has been used in 3ds Max as a person would (the list is in
  `docs/audit.md`). Start a 3ds Max of your own and close it without saving; never touch one you did not start;
  never open or save one of the author's scenes.
- **Keep this file true.** No history, no dated notes. Nothing of the author's computer in a published file.

## Layout

- `package/OpenScene/`: what goes in the bundle. `openscene/` is the Python package: `window.py` (the dock),
  `cards.py` / `cards2.py` (the cards), `widgets.py`, `dialogs.py`, `grid.py`, `icons.py`, `maxlink.py` (everything
  that talks to 3ds Max), and the modules without pymxs or Qt that the tests load: `__init__.py` (`__version__`,
  `APP`), `model.py` (setups, stored text, names a setup may carry), `trust.py` (what may run), `folders.py`,
  `toolbar.py`, `startup.py`, `external.py` (setups of another scene manager), `open3d_settings.py` (common file).
  `openscene_core.ms` is the MAXScript side (every global `oscn_`), `OpenScene_startup.ms` the file-open check.
- `package/OpenScene.mcr`: the macro. `bundle/openscene_bundle.ms`: the bundle's post-start-up script.
- `tools/build.py` → `dist/OpenScene.bundle`; `tools/check_ms.py`: the MAXScript check; `tools/props_source.py` →
  `tools/make_props.py` → `openscene/props.json` (the Property Selector tables).
- `tests/`: the tests without 3ds Max; `tests/run.py` runs them. `docs/audit.md`: limits, ideas, the test list in
  3ds Max. `docs/security-review.md`: what the review before the launcher needs.

## Build and check

- `python tools/build.py` writes `dist/OpenScene.bundle`: it runs `tools/check_ms.py` (stops on a problem), copies
  `package/OpenScene` to `Contents/OpenScene`, the macro to `Contents/macroscripts`, draws the icons into
  `Contents/icons/Dark|Light`, and writes `PackageContents.xml` from `__version__`, then checks it.
- `tools\check.ps1` runs every check, and all must pass; it needs Python 3.11 or newer and the ruff that `ruff.toml`
  names. Built in: the version agrees, every `.py`, `.ms`, `.mcr` and `.ps1` has its licence line, no file holds a
  path of somebody's computer. Then, from `tools/repo.toml`: `ruff format --check .`, `ruff check .`,
  `python tools/check_ms.py`, `python -I tests/run.py`. `-Full` adds nothing yet.
- CI: `.github/workflows/check.yml` runs `tools\check.ps1`, without `-Full`, on every push and pull request to `main`,
  on GitHub's Windows runner, with Python 3.11 and 3.13.
- `.editorconfig`, `.gitattributes`, `ruff.toml`, `LICENSE`, `tools/check.ps1`, `tools/repo*.py` and
  `openscene/open3d_settings.py` are Open3D's common files: never change them here. Only the end of `.gitattributes`
  and `ruff.toml`, after `# Specific to this repository.`, is this repo's.
- After changing `tools/props_source.py`, run `python tools/make_props.py` and commit `props.json`.

## Version and release

- The version is `__version__` in `openscene/__init__.py`; the README's status line repeats it, and `tools/build.py`
  writes it into `PackageContents.xml` (`AppVersion` and every `ComponentEntry`). `python -I tools/repo.py version set
  X.Y.Z` writes both places.
- `python -I tools/repo.py package` needs the version's `## X.Y.Z` section in `CHANGELOG.md`, runs the quick checks
  and `tools/build.py`, and writes `dist/openscene-<version>-windows-x64-3dsmax.zip` (with `OpenScene.bundle` at its
  root and `LICENSE` inside it) and `dist/SHA256SUMS.txt`. `release X.Y.Z` makes the tag and then the draft.
- The launcher needs `OpenScene.bundle` at the root of the zip, with the release's version in `PackageContents.xml`.

## Rules of this code

- A bug that is fixed comes with a test that fails without the fix, and new logic comes with its tests.
- Never name the tool's former names or the reference program it was inspired by, in code, comments, UI, docs,
  commits or file names; it is "another scene manager". The only traces allowed are the keys that convert files of
  versions before 2.0.0: `oscn_oldDat`, `oscn_oldMaps`, `oscn_oldMix` in `openscene_core.ms`, the key list in
  `OpenScene_startup.ms`, `model.OLD_COMPRESSED_PREFIX`.
- Own work only: the labels, ranges and defaults of `tools/props_source.py` are written here; property *names* are
  the renderers' API and must match exactly.
- Setups live on `rootNode` in `OpenScene_Dat` (`oscn_data`, attribID `0x4f53cd21, 0x2e6a9b74`), maps in
  `OpenScene_Maps` (`0x4f53cd22, 0x2e6a9b75`). Never reuse or change these IDs: a scripted attribute redefined with
  the same ID and other parameters wipes the data. Card ids, the `props` keys (`card|class|property`) and the setting
  file names need a migration to change; `PackageContents.xml`'s ProductCode and UpgradeCode never change.
- A setup comes inside a file from anyone. Whatever it runs goes through `SceneManager.review()`; a name it carries
  is checked (`model.is_plain_name`, `oscn_classNamed`, never `execute`); stored text goes through `model.decode` /
  `model.read_preset`, which refuse a newer `FORMAT_VERSION`. A new place that turns text into code must be added to
  `tests/test_security.py` with its reason.
- Maps are found by class + name (`oscn_findMap`, through `oscn_mapsNamed` and the cache that every scene read makes
  again from `oscn_allMaps`); names repeat, so the one with an HDRI or sky in it wins, then the one in the
  environment slot, then one in `OpenScene_Maps`.
- Nodes and layers a setup uses carry a lasting ID in their app data (slot `oscn_uidSlot`, "OSID"; never another
  tool's), stamped when the setups are saved (`window.stamp_uids`) and followed by ID, then handle, then name
  (`oscn_resolveNodes`, `model.apply_resolved`, `model.follow_layer_renames`).
- Code ported from OpenManager (GPL-3.0-or-later, Carles Llavata) is rewritten here and listed in `NOTICE`; add to
  it what is ported next. Never bring its property tables or anything that names the reference program.
- Layers and Objects show one list for all setups (`model.shared_rows`, `cards.share_rows`, `window.share_lists`);
  each setup keeps its own values. Decided by the author: the scene state carries over between setups, and Corona
  Interactive is not stopped when a setup is applied (`ipr_corona_restart`, off by default).
- Files: settings in `%APPDATA%\Open3D\OpenScene`, everything else in `%LOCALAPPDATA%\Open3D\OpenScene`, always
  through `folders.py`. The interface is in English only.

## Traps

- MAXScript reserved words cannot be names: `local at = ...` broke the 2.2.0 installer ("expected name").
  `tools/check_ms.py` finds them and bad string escapes (only `\\ \n \t \r \"`).
- The Bash tool collapses `\\` to `\` even in quoted heredocs: write files with backslashes (MAXScript paths, Python
  escapes) with the Write / Edit tools, never through a shell heredoc.
- A `.ms` file that uses a global made by a file it loads declares it `global` before its block, or the name
  compiles as an empty local.
- MAXScript has no call to add a button to a toolbar: `toolbar.py` edits the `.cuix` (UTF-8 with a byte order mark,
  CRLF; keep both) after `cui.saveConfig`, then `cui.loadConfig`.
- 3ds Max loads usermacros before the bundles' macroscripts: the bundle's OpenScene macro wins over an old `.mzp` one.
- In a session without an interface (`3dsmaxbatch`, render nodes) no Qt window can be shown: `startup.run` skips the
  toolbar there.
- pymxs raises a MAXScript error as `RuntimeError`; `maxlink.MAX_ERRORS` is what a call into 3ds Max can raise.
