# Security review

What the review before the Open3D launcher needs from OpenManager: how each rule of the Open3D-SDK's *Security* guide
applies, every place where OpenManager reads something it did not make, and what it writes outside its own folders.
Each line names the code or the test that shows it.

## The rules

### What comes with a file

| Rule | How OpenManager keeps it |
|---|---|
| Nothing that came with a file runs without asking | The Script Editor code, the Script File files and the Render Preset of a setup run only through `SceneManager.review()` (`openmanager/window.py`), which shows what would run and asks, with No as the answer Enter and Escape give. What was written or chosen in this computer's window, or said yes to, is trusted by the digest of its exact text, or of a file's path and contents (`openmanager/trust.py`); a change asks again. A Batch Render and Bake Setups ask once, before they start. The question is `dialogs.ask_safely`: Enter answers No wherever the focus is. A render preset leaves Render Setup's own pre- and post-render scripts as they were (`maxlink.load_preset`), so a preset only brings render settings. Tests: `tests/test_trust.py`, `tests/test_dialogs.py`, `tests/test_security.py`. |
| A name read from a file is never evaluated | Class names (environment maps, the maps below them, tone-mapping operators) are checked to be plain names and looked up among the classes of the kind expected: `oscn_classNamed` in `openmanager_core.ms`, `maxlink.new_operator`. Tests: `tests/test_security.py`, `tests/test_model.py` (`Names`). |
| A file sets only what the interface sets | The properties a card sets are the fixed list of `props.json`, made from `tools/props_source.py`; a setup only holds values for them. Render Override and the default render settings take plain renderer property names with plain values (`model.renderer_value_ok`), Post-Production only the settings of its category (`model.post_setting_ok`), LightMix only its arrays (`model.LIGHTMIX_ARRAYS`), a tone-mapping operator only plain property names (`maxlink.set_operator_props`). Tests: `tests/test_security.py` (`FileNames`). |
| Text never becomes code | Every place that turns text into code is listed in `tests/test_security.py` (`KNOWN`), with the reason it is safe; a new one fails the test. The only `execute` of text is `oscn_runCode`, behind `review()`. |
| What is refused is said | A setting left out is named in the MAXScript Listener and counted in a message of the window (`SceneManager.actions_for`); a script or preset not run too (`SceneManager.review`). |
| Input from files is validated | Setups stored in a `.max` file or a preset: a newer format version is refused, never guessed at; the stored text is bounded (64 MB unpacked, 2000 setups); a value of the wrong kind gets its default; a repeated id gets a new one (`model.decode`, `model.read_preset`, `model.read_output_preset`, `external.convert`, `version0.convert`). Setups OpenManager could not read whole are never written over. The render output path must be absolute, without `..` (`model.is_valid_file_path`). Tests: `tests/test_model.py`. |
| Text files are valid UTF-8 | `tests/test_text_files.py`, which also checks the byte order mark of the MAXScript files. |

### What crosses a network

OpenManager opens no connection, runs no server and downloads nothing. The HDRI Browser lists folders the person adds,
on their own computer or network shares, and reads the images in them.

### Secrets

OpenManager keeps none: no keys, tokens or passwords.

### Nothing of anybody's computer in a published file

`tools\check.ps1` looks for the folder of a Windows user and the words of the author's private list
(`open3d-private-terms.txt`, above the repository, never committed) in every file.

### Dependencies

None beyond the Python, PySide6, `pymxs` and `qtmax` that come with 3ds Max. Dependabot alerts: switched on in the
repository's settings by the author.

### The code and the installation

The bundle installs for the user, in `%APPDATA%\Autodesk\ApplicationPlugins`, without administrator rights. OpenManager
never asks for them and starts no other program.

## Where OpenManager reads what it did not make

| What | Where in the code | What is checked |
|---|---|---|
| Setups stored in a `.max` file (`OpenScene_Dat`, and the keys of the versions before 2.0.0) | `maxlink.read_setups`, `model.decode` | format version, size, kinds of every value, ids; names before they reach 3ds Max (above) |
| Setups OpenManager 0.x stored in a `.max` file (`OpenManager_Dat`) | `maxlink.read_setups`, `version0.convert` | the same checks as this version's own (`model.from_stored`); the lasting IDs it gave nodes are dropped; only read, never written |
| Setups another scene manager stored in a `.max` file (`SceneManager_Dat`) | `external.convert` | size, entries that are not setups skipped, every setup normalized; then as above |
| Setup and output preset files (`.osp`, `.smp`) the person opens | `model.read_preset`, `model.read_output_preset` | size before reading, format version, kinds, token kinds |
| The scene itself (names of cameras, lights, layers, objects, maps) | `oscn_scene` in `openmanager_core.ms` | every name goes out quoted as JSON text (`oscn_quote`) and comes back only as a name to look up |
| Script files and render presets named by a setup | `oscn_preRender` / `oscn_postRender`, `oscn_loadPreset` | run only after `review()` |
| Corona post-production of setups stored by older versions (a VFB `.conf` text) | `maxlink._run_one` (`post`) | written to a temporary file and loaded by Corona as its own settings file: data, not code |
| Images in the HDRI folders the person adds | `cards.HdriCard`, `oscn_hdriPreview` | read by 3ds Max to make a preview |
| 3ds Max's interface file (`.cuix`), at the first start | `openmanager/toolbar.py` | only read to find the button and to add the toolbar |
| OpenManager's own settings | `window.load_settings` | read errors are said; a broken file means the defaults |
| The settings of OpenManager 0.x, OpenScene 3 and OpenScene 2.x, once, at the first start | `folders.carry_over`, `version0.settings` | OpenScene's are copied as they are; 0.x's are converted: only the settings with the same meaning, each of the right kind; the files it trusted are trusted by their contents as they are then |

No clipboard, no command-line arguments, no network.

## What OpenManager writes outside its own folders

| What | Why |
|---|---|
| The setups, in the `.max` file (the `OpenScene_Dat` and `OpenScene_Maps` attributes of the root node) | that is where a setup lives; saved with the file |
| Renders, where each setup's Render Output says | what the person asked for |
| Thumbnails, exports and render presets of a saved scene, in folders next to the `.max` file (`OpenManager_thumbs`, `OpenManager_export`, `OpenManager_presets`) | what the person asked for; a scene not saved yet uses the data folder |
| 3ds Max's interface file (`.cuix`), once, at the first start | to add the OpenManager toolbar; backed up in the data folder first and put back if anything fails (`toolbar.place`) |
| The files of an old `.mzp` install of OpenScene in 3ds Max's user folders, removed at the first start | so the old copy does not run beside the bundle; only those exact files, and the scripts folder only when it holds this package (`startup.old_install`); settings are left |
| `%TEMP%\oscn_post.conf` | the Corona post-production of setups stored by older versions, loaded from there |
| Batch Render views of 3ds Max, `.max` files baked into the export folder | Bake Setups, when the person runs it |

## What OpenManager does not protect against

- A `.max` file can carry code of its own that 3ds Max runs without OpenManager: scripted controllers, persistent
  callbacks, scripted plug-ins. OpenManager neither adds nor removes that.
- A trusted script runs with everything 3ds Max can do. Trust is per computer and per exact text.
- Render settings a setup carries are the renderer's own properties by name: a file can set a renderer's file paths
  (a LUT, say), which the renderer then reads.

## Open points for Open3D's maintainers

- Render output paths come with the file: OpenManager takes only absolute paths without `..`, but any absolute folder.
  Should they be limited to folders the person allowed?
- Render Override takes any plain property name of the renderer, as its Fetch button does. Is that a fixed enough
  list, or should it be the renderer's properties in `props.json` only?
