# Audit

How OpenManager holds up with big scenes, the limits it has, the improvements proposed (by impact), and what has to be
tried in 3ds Max before a release. What touches MAXScript and the window can only be seen inside 3ds Max.

## Big scenes and Batch Render

### What is already made for big scenes

| Point | How it works |
|---|---|
| Reading the scene | Only the objects the setups use are read (`oscn_nodesInfo`); the selection is read when "+" is pressed. No cap on objects. |
| Reading again when the window is back in focus | Each read is timed and the shortest wait is `max(0.8 s, 20 × what it took)`. A read longer than 1 s is said in the Listener. |
| Bursts of events (`#nodeCreated` in a merge of 10 000 nodes) | Only the first of each burst reaches Python; the others wait for the next read. |
| Texture maps | `oscn_texmaps` goes through the maps once (O(n)). |
| Setups stored in the `.max` file | Above 32 KB they are stored with zlib + base64: 50 setups × 2000 layers go from 10 MB to 0.43 MB. |
| Layers card | Lookups by dictionary; the filter waits 180 ms after the last key. |
| Small cards | They grow until their content fits, without a scroll bar; those with tables have one. |

### Batch Render

- **A check before it starts**: a camera that is gone, an incomplete path, `.cxr` without Corona, **two setups writing
  the same file**, a pre/post script or `.rps` preset that does not exist. It lists them and you decide.
- **What the batch would run is asked about once, before it starts**: scripts and presets that came with the file.
- **One setup that fails does not stop the batch**: it is noted, the next one goes on, and a summary lists the
  failures at the end.
- The time of each setup in the Listener, the **time left** in the progress bar and the total time at the end.
- **`.cxr`** output: with Corona, the render elements and the LightMix go inside the file (not one `.cxr` per element).

## Limits

1. **The state carries over from one setup to the next.** A card that is off does not put the scene back: it stays as
   the previous setup left it. If setup A hides a layer and setup B has Layers off, B renders with that layer hidden.
   It is on purpose (a setup or a region can be rendered again without touching the rest), but worth knowing in long
   batches.
2. **Everything runs on 3ds Max's main thread.** Reading the scene, applying setups and making HDRI previews block
   the interface.
3. **One call per change.** 2000 layers × 4 properties = 8000 pymxs calls when a setup is applied (about 0.5 to 1 s).
   They could go in one MAXScript call.
4. **Every read of the scene walks the maps once** (`oscn_allMaps`: materials, environment, editors, the settings of
   the renderer, cameras and lights). Much faster than a pass per class, but it still grows with the number of
   materials and lights. A map nothing points to is found the slow way, once.
5. **IDs are stamped when the setups are saved**: a node merged before its setups were ever saved is found by its
   name only, and only when one node has it.
6. **No undo**: a setup is applied with undo off. Ctrl+Z does not take it back.
7. **Render elements renamed with the output only with Corona, Redshift and FStorm** (`name_element.ext`). V-Ray's
   separate channels (VRayRawImage / *Separate render channels*) are not touched.
8. **Time Output changes the scene's `animationRange`** for good.
9. **HDRI previews**: `openBitmap` of a 60 MB HDRI freezes 3ds Max for a few seconds per file (automatic up to 60 MB).

## Improvements proposed

### High

1. **An optional base state**: store the state of layers, lights, environment and render once, and put it back before
   each setup of the batch ("reset between setups"), keeping today's behaviour as the default.
2. **Apply in one call**: send the list of changes as JSON to one MAXScript function. Much faster with many layers or
   objects.
3. **A cache of maps by name** in MAXScript (class|name → map, emptied by scene events) for `oscn_findMap`.
4. **A render log on disk** in the data folder: setup, path, time, error. Useful on render farms and the morning
   after.
5. **Save the `.max` file before the batch**, and freeze viewport redraws while a setup is applied.

### Medium

6. **Differences between setups**: pick two and see what changes (camera, layers, settings).
7. **`Frame` / `Pass` tokens** and **a subfolder per setup** in Render Output. And **JPG + CXR**: the beauty as a JPG
   and the multi-layer CXR at once.
8. **Send to Deadline / Backburner**: one job per setup with its baked `.max` file (Bake already makes them).
9. **Search and filter in the setup list** (by name, camera, status) and **groups or folders** of setups.
10. **Status in the list** (`status` is in the model but not shown): WIP, Review, Final.
11. **Undo of "apply setup"**: keep the state before and go back with a button.
12. **V-Ray channels**: the path of *Separate render channels* and of VRayRawImage with the same tokens.

### Small

13. The total frame count of the batch, and an estimate from the last time per frame.
14. A warning when the output disk is low on space before the batch starts.
15. Export or import the **card layout** to share it with the team.

## What to try in 3ds Max

Before a release, on the package of the release, in a 3ds Max started for the test, with `OPEN3D_SETTINGS_DIR` and
`OPEN3D_DATA_DIR` pointed at a scratch folder, on a new test scene:

1. **The bundle**: unzip it into `ApplicationPlugins`, start 3ds Max. The Listener says `OpenManager <version>: ...`, the
   OpenManager macro opens the window, the icon shows in both themes.
2. **The toolbar at the first start**: on an interface without the button, an "OpenManager" toolbar appears, floating;
   restart: no second one, and its button still opens the window (in 3.0.0 it said "not installed" then). On an
   interface that has the button already: nothing is added. The backup is in the data folder. On an interface with the
   OpenScene toolbar (or an OpenScene button on a toolbar of one's own): the button opens OpenManager and the toolbar
   is called OpenManager, with no second one.
3. **Settings of the versions before**: with the files of OpenManager 0.x in the settings folder
   (`OpenManager.json` with trusted scripts, `OpenManager_default.json`, `OpenManager_notify.txt`, and
   `OpenManager_hdri` in the data folder), the first start converts them: the theme, the card layout and the
   HDRI folders are the same, a script 0.x trusted runs without asking, the Listener says what was not taken,
   and the files of 0.x are unchanged. The same with the folders of OpenScene 3, or a `plugcfg\OpenScene.json`
   of 2.x; with both programs' settings, those changed last are taken. A second start copies nothing.
4. **Older installs**: with OpenScene 2.x or OpenManager 0.x installed by its `.mzp` in the user folders, or an
   `OpenScene.bundle` in `ApplicationPlugins`, the first start removes them (the Listener says what), files of
   one's own beside them stay, and the button keeps working. An `OpenScene.bundle` started in the same session
   leaves the OpenManager button working.
5. **Scripts that come with a file**: a `.max` made on another computer with Script Editor code and a render preset:
   applying a setup asks first, Enter answers No and nothing runs; yes runs them and they are not asked again; after
   editing the code it is asked again. A batch asks once, before it starts.
6. **A scene of OpenManager 0.x**: a `.max` saved with setups by OpenManager 0.x: opening it with the window
   closed offers to open it; the setups are there, every card as in 0.x, a message says how many were
   converted and the Listener what was not taken; applying them works; after saving and opening again, the
   setups of this version are read and nothing is asked; OpenManager 0.x's data is still in the file.
7. **A file saved by a newer OpenManager** (format version above 1): a message says why the setups were not read, and
   saving the scene leaves them as they were.
8. **CXR**: Corona with render elements (LightMix, Z-depth...) and the `.cxr` Extension token: one `.cxr`, no separate
   files per element, that opens in the Corona Image Editor with every layer. With V-Ray: the path shows in orange and
   the check before the batch says so.
9. **Render Output** with a relative path or `..`: shown in orange, nothing is written.
10. **Small cards** without a setup active: no vertical scroll bar on Time Output, Resolution, Scene Name, Dome...;
   switch Time Output between Single, Range and List.
11. A scene with more than 5000 objects: an object made last, added to Objects, is not *(missing)*.
12. A merge of a big scene with the window open: it freezes no longer than the merge.
13. A batch with a broken setup (a script path that does not exist...): the batch goes on and the summary lists it.
14. Save and open again a `.max` file with many setups or layers: they read back (packed).
15. **Shared Layers / Objects**: a layer added in one setup is in the others; hidden in one, it stays visible in
    another when that one is applied; a new setup has the whole list; removing it removes it from all.
16. **A `.max` file with setups from before 2.0.0**: it opens with its setups and environment mixes; saved and opened
    again, they are still there (under the new key).
17. **An environment Color Correct over an HDRI** in a scene where a material has a Color Correct of the same name:
    choosing it in the Environment card gives the HDRI's background, not the material's colour.
18. **Drawing in a viewport** with the window open: start a line, a rectangle and a tape and cancel each with a
    right-click, several times: 3ds Max does not stop (in 3.0.1 it could close with an access violation), and
    once the object is made or cancelled the cards show the scene as it is.
