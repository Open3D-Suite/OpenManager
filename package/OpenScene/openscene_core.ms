-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenScene
-- MaxScript side of the tool: reads the scene and changes it for the Python window.
-- Every function is prefixed oscn_ so nothing collides with other scripts.

global oscn_rendering = false
global oscn_cancel = false
global oscn_notify -- set from Python: called with a #name when the scene changes

-- setups live inside the .max file, on a custom attribute of the root node
global oscn_attrDef = attributes oscn_data attribID:#(0x4f53cd21, 0x2e6a9b74)
(
    parameters main
    (
        OpenScene_Dat type:#string default:""
    )
)

-- environment maps the setups use: 3ds Max forgets a map nothing in the scene points to (when another setup replaces
-- it in the environment slot, for instance), so they are held here and saved with the file
global oscn_mapsDef = attributes oscn_maps attribID:#(0x4f53cd22, 0x2e6a9b75)
(
    parameters main
    (
        OpenScene_Maps type:#textureMapTab tabSizeVariable:true
    )
)

fn oscn_keepMap m =
(
    if (m == undefined) do return false
    if (not (isProperty rootNode #OpenScene_Maps)) do custAttributes.add rootNode oscn_mapsDef
    if ((findItem rootNode.OpenScene_Maps m) == 0) do append rootNode.OpenScene_Maps m
    true
)

-- ---------------------------------------------------------------- class names, never run as code

-- a plain name: letters, digits and underscores, not starting with a digit (a class name read from a setup)
fn oscn_isPlainName s =
(
    if (classof s != String or s.count == 0 or s.count > 128) do return false
    local okFirst = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    local ok = okFirst + "0123456789"
    if ((findString okFirst s[1]) == undefined) do return false
    for i = 2 to s.count do if ((findString ok s[i]) == undefined) do return false
    true
)

-- the class of this kind (textureMap, camera...) that has this name, looked up among the classes of that kind without
-- running anything; undefined when the name is not a plain name or no class of that kind has it
fn oscn_classNamed nm kind =
(
    if (not (oscn_isPlainName nm)) do return undefined
    local want = toLower nm
    for c in kind.classes where ((toLower (c as string)) == want) do return c
    -- an older name 3ds Max keeps for a class (VRayHDRI for VRayBitmap): what it holds under that name is read as it
    -- is, nothing is run, and it counts only when it is a class of that kind
    local g = undefined
    try (if (globalVars.isGlobal (nm as name)) do g = globalVars.get (nm as name)) catch()
    if (g != undefined and (try ((classOf g) == kind) catch false)) do return g
    undefined
)

-- a new map or camera of the class with this name, or undefined when 3ds Max has no such class (a renderer missing)
fn oscn_newOf nm kind =
(
    local c = oscn_classNamed nm kind
    if (c == undefined) then undefined else (try (c()) catch undefined)
)

-- ---------------------------------------------------------------- JSON text

fn oscn_quote v =
(
    local s = v as string
    s = substituteString s "\\" "\\\\"
    s = substituteString s "\"" "\\\""
    s = substituteString s "\n" "\\n"
    s = substituteString s "\r" "\\r"
    s = substituteString s "\t" "\\t"
    "\"" + s + "\""
)

fn oscn_bool v = (if v == true then "true" else "false")

fn oscn_join items =
(
    local ss = stringStream ""
    for i = 1 to items.count do
    (
        if i > 1 do format "," to:ss
        format "%" items[i] to:ss
    )
    ss as string
)

-- ---------------------------------------------------------------- what the scene holds

fn oscn_engineName =
(
    local s = (classof renderers.current) as string
    if (matchPattern s pattern:"*V_Ray*" or matchPattern s pattern:"*VRay*") then "V-Ray"
    else if (matchPattern s pattern:"*Corona*") then "Corona"
    else if (matchPattern s pattern:"*FStorm*") then "FStorm"
    else if (matchPattern s pattern:"*Redshift*") then "Redshift"
    else if (matchPattern s pattern:"*Arnold*") then "Arnold"
    else s
)

fn oscn_mapFile m =
(
    local f = ""
    try (f = if (hasProperty m #filename) then m.filename else if (hasProperty m #HDRIMapName) then m.HDRIMapName else "") catch()
    if (f == undefined) then "" else (f as string)
)

-- every map below m (m included): an HDRI in a Corona Bitmap, the Color Correct on top of it, a Corona Select...
global oscn_chainInto
fn oscn_chainInto m found =
(
    if (m != undefined and (findItem found m) == 0) do
    (
        append found m
        local n = 0
        try (n = getNumSubTexmaps m) catch()
        for i = 1 to n do
        (
            local sub = undefined
            try (sub = getSubTexmap m i) catch()
            oscn_chainInto sub found
        )
    )
    found
)
fn oscn_chain m = oscn_chainInto m #()

fn oscn_isBitmapClass m = (findItem #("CoronaBitmap", "VRayHDRI", "VRayBitmap", "FStormBitmap", "Bitmaptexture", "RS_Bitmap") ((classof m) as string)) > 0

-- 2: an .hdr somewhere in the chain, 1: only an .exr, 0: neither
fn oscn_hdrLevel m =
(
    local best = 0
    for c in (oscn_chain m) where (oscn_isBitmapClass c) do
    (
        local ext = toLower (getFilenameType (oscn_mapFile c))
        if (ext == ".hdr") then best = 2
        else if (ext == ".exr" and best == 0) do best = 1
    )
    best
)

-- the maps that mix the tabs of the Environment card: made and kept by the tool, never offered in its list
fn oscn_isMixMap m = (try (matchPattern m.name pattern:"OSCN_EnvMix*") catch false)

fn oscn_addEnvMap found offer m yes =
(
    if (m == undefined or (oscn_isMixMap m)) do return false
    local i = findItem found m
    if (i == 0) then (append found m; append offer yes)
    else if yes do offer[i] = true
)

-- maps sitting in the Material Editors (compact slots and Slate views): not always seen as part of the scene
fn oscn_editorMaps =
(
    local out = #()
    try (for i = 1 to meditMaterials.count do (local m = meditMaterials[i]; if (superclassof m == textureMap) do appendIfUnique out m)) catch()
    try
    (
        for i = 1 to (sme.GetNumViews()) do
        (
            local v = sme.GetView i
            for j = 1 to (v.GetNumNodes()) do
            (
                local r = undefined
                try (r = (v.GetNode j).reference) catch()
                if (r != undefined and superclassof r == textureMap) do appendIfUnique out r
            )
        )
    )
    catch()
    out
)

-- ---------------------------------------------------------------- every map the scene uses, in one walk

-- Maps are found by walking from what holds them: the materials of the scene, the environment, the Material Editors,
-- the maps the tool keeps, and the texture-map settings of the renderer, cameras and lights. One walk, instead of a
-- getClassInstances for each class, which goes through the whole scene each time (seconds on big scenes).
global oscn_walk
fn oscn_walk m found seen =
(
    if (m == undefined) do return found
    local id = undefined
    try (id = (getHandleByAnim m) as integer) catch()
    if (id == undefined or (HasDictValue seen id)) do return found
    PutDictValue seen id true
    local sc = undefined
    try (sc = superclassof m) catch()
    if (sc == textureMap) then
    (
        append found m
        local n = 0
        try (n = getNumSubTexmaps m) catch()
        for i = 1 to n do (local sub = undefined; try (sub = getSubTexmap m i) catch(); oscn_walk sub found seen)
    )
    else if (sc == material) do
    (
        local n = 0
        try (n = getNumSubMtls m) catch()
        for i = 1 to n do (local sub = undefined; try (sub = getSubMtl m i) catch(); oscn_walk sub found seen)
        n = 0
        try (n = getNumSubTexmaps m) catch()
        for i = 1 to n do (local sub = undefined; try (sub = getSubTexmap m i) catch(); oscn_walk sub found seen)
    )
    found
)

-- the maps in the settings of an object (the renderer, a camera, a light)
fn oscn_walkProps obj found seen =
(
    if (obj == undefined) do return found
    local names = #()
    try (names = getPropNames obj) catch()
    for p in names do
    (
        local v = undefined
        try (v = getProperty obj p) catch()
        if (v != undefined and (try ((superclassof v) == textureMap) catch false)) do oscn_walk v found seen
    )
    found
)

fn oscn_allMaps =
(
    local found = #()
    local seen = Dictionary #integer
    for m in sceneMaterials do oscn_walk m found seen
    oscn_walk environmentMap found seen
    try (oscn_walk renderers.current.environment_texture found seen) catch()
    for m in (oscn_editorMaps()) do oscn_walk m found seen
    try (for i = 1 to meditMaterials.count do oscn_walk meditMaterials[i] found seen) catch()
    try (for m in rootNode.OpenScene_Maps do oscn_walk m found seen) catch()
    oscn_walkProps renderers.current found seen
    for c in cameras where (superclassof c == camera) do oscn_walkProps c found seen
    for lt in lights where (superclassof lt == light) do oscn_walkProps lt found seen
    found
)

-- Maps are looked up by class and name many times while setups are applied: they are kept in a dictionary, made again
-- at every read of the scene (so a map made a moment ago is in it), and each one is checked before it is used.
global oscn_mapCache = undefined

fn oscn_cacheFrom maps =
(
    oscn_mapCache = Dictionary #string
    for m in maps do
    (
        local key = toLower (((classof m) as string) + "|" + m.name)
        if (HasDictValue oscn_mapCache key) then append (GetDictValue oscn_mapCache key) m
        else PutDictValue oscn_mapCache key #(m)
    )
    maps
)

fn oscn_mapOk m c nm = (try (isValidObj m and m.name == nm and (classof m) == c) catch false)

fn oscn_cached key c nm =
(
    if (oscn_mapCache == undefined or not (HasDictValue oscn_mapCache key)) then #()
    else (for m in (GetDictValue oscn_mapCache key) where (oscn_mapOk m c nm) collect m)
)

-- the maps of this class with this name: from the cache; walked again when it has none; and, last, the slow way
-- through every instance of the class, for a map nothing points to
fn oscn_mapsNamed cls nm =
(
    local c = oscn_classNamed cls textureMap
    if (c == undefined or classof nm != String) do return #()
    local key = toLower (cls + "|" + nm)
    local same = oscn_cached key c nm
    if (same.count == 0) do
    (
        oscn_cacheFrom (oscn_allMaps())
        same = oscn_cached key c nm
    )
    if (same.count == 0) do
    (
        try (same = for m in (getClassInstances c) where (m.name == nm) collect m) catch()
        if (same.count > 0) do PutDictValue oscn_mapCache key same
    )
    same
)

-- maps the Environment card knows about, as #(maps, offered). Offered in the list: skies, bitmaps with an .hdr, and
-- colour corrections / selects with such a bitmap linked below. The others (.exr) are kept so a setup using one still works.
global oscn_skyClasses = #("CoronaSky", "VRaySky", "FStormSky", "Physical_Sun___Sky_Environment", "RS_Physical_Sky")

fn oscn_envMaps maps:undefined =
(
    local found = #()
    local offer = #()
    local skies = oscn_skyClasses
    local wanted = #("CoronaBitmap", "VRayHDRI", "VRayBitmap", "FStormBitmap", "Bitmaptexture", "RS_Bitmap", "CoronaColorCorrect", "Color_Correction", "FStormColorCorrection", "CoronaSelect")
    if (maps == undefined) do maps = oscn_cacheFrom (oscn_allMaps())
    for m in maps do
    (
        local cls = (classof m) as string
        if ((findItem skies cls) > 0) then oscn_addEnvMap found offer m true
        else if ((findItem wanted cls) > 0) do
        (
            local lvl = oscn_hdrLevel m
            if (lvl > 0) do oscn_addEnvMap found offer m (lvl == 2)
        )
    )
    if (environmentMap != undefined) do oscn_addEnvMap found offer environmentMap true
    #(found, offer)
)

-- the map of this class with this name. Names are often shared (maps named after their class, models merged from
-- other files, copies), and a Color Correct of a material must never take the place of the one over the HDRI: when
-- several have the name, the one that looks like an environment wins (a sky, or an HDRI in it), then the one in the
-- environment slot now (or linked below it), then one the tool keeps.
fn oscn_findMap cls nm =
(
    local same = oscn_mapsNamed cls nm
    if (same.count == 0) do return undefined
    if (same.count == 1) do return same[1]
    local inEnv = #()
    if (environmentMap != undefined) do oscn_chainInto environmentMap inEnv
    try (local t = renderers.current.environment_texture; if (t != undefined) do oscn_chainInto t inEnv) catch()
    local kept = #()
    try (for k in rootNode.OpenScene_Maps where (k != undefined) do oscn_chainInto k kept) catch()
    local best = same[1]
    local bestScore = -1
    for m in same do
    (
        local score = 0
        if ((findItem oscn_skyClasses ((classof m) as string)) > 0 or (oscn_hdrLevel m) > 0) do score += 4
        if ((findItem inEnv m) > 0) do score += 2
        if ((findItem kept m) > 0) do score += 1
        if (score > bestScore) do (best = m; bestScore = score)
    )
    best
)

fn oscn_isDome l =
(
    local cls = (classof l) as string
    case cls of
    (
        "Skylight": true
        "rsDomeLight": true
        "VRayLight": (try (l.type == 1) catch false)
        "Arnold_Light": (try (l.shapeType == 6) catch false)
        default: false
    )
)

fn oscn_isSun l =
(
    (findItem #("CoronaSun", "FStormSunLight", "rsSunLight", "VRaySun", "Sun_Positioner", "DaylightAssemblyHead") ((classof l) as string)) > 0
)

fn oscn_objectJson o =
(
    local ln = ""
    try (ln = o.layer.name) catch()
    "{\"handle\":" + (o.inode.handle as string) + ",\"name\":" + (oscn_quote o.name) + ",\"class\":" + (oscn_quote (classof o)) + ",\"layer\":" + (oscn_quote ln) + ",\"visible\":" + (oscn_bool (not o.isNodeHidden)) + "}"
)

-- geometry / shapes among these handles (the ones the setups use, or the selection), as a JSON array
fn oscn_nodesInfo hs =
(
    local items = #()
    for h in hs do
    (
        local o = maxOps.getNodeByHandle h
        if (isValidNode o and (superclassof o == GeometryClass or superclassof o == shape)) do append items (oscn_objectJson o)
    )
    "[" + (oscn_join items) + "]"
)

-- the whole scene as one JSON text (one call is much faster than many small ones).
-- Objects: only those whose handles are given (the ones the setups use). Listing every object made each read
-- slow in big scenes and left out everything past the first 5000.
fn oscn_scene objHandles:#() =
(
    local cams = #()
    for c in cameras where (superclassof c == camera) do
    (
        local locked = false
        try (locked = ((getTransformLockFlags c).numberset > 0)) catch()
        append cams ("{\"handle\":" + (c.inode.handle as string) + ",\"name\":" + (oscn_quote c.name) + ",\"class\":" + (oscn_quote (classof c)) + ",\"locked\":" + (oscn_bool locked) + "}")
    )
    local shines = #()
    for l in lights where (superclassof l == light) do
    (
        local cls = (classof l) as string
        local inDaylight = (l.parent != undefined and ((classof l.parent) as string) == "DaylightAssemblyHead")
        if (cls != "Targetobject" and not inDaylight) do
        (
            local kind = if (oscn_isSun l) then "sun" else if (oscn_isDome l) then "dome" else "light"
            append shines ("{\"handle\":" + (l.inode.handle as string) + ",\"name\":" + (oscn_quote l.name) + ",\"class\":" + (oscn_quote cls) + ",\"kind\":\"" + kind + "\"}")
        )
    )
    for h in helpers do
    (
        local cls = (classof h) as string
        if (cls == "DaylightAssemblyHead" or cls == "Sun_Positioner") do
        (
            local sunCls = ""
            try (if (cls == "DaylightAssemblyHead" and h.sun != undefined) do sunCls = (classof h.sun) as string) catch()
            append shines ("{\"handle\":" + (h.inode.handle as string) + ",\"name\":" + (oscn_quote h.name) + ",\"class\":" + (oscn_quote cls) + ",\"sun_class\":" + (oscn_quote sunCls) + ",\"kind\":\"sun\"}")
        )
    )
    local maps = #()
    local envList = oscn_envMaps maps:(oscn_cacheFrom (oscn_allMaps()))
    for i = 1 to envList[1].count do
    (
        local m = envList[1][i]
        local links = #()
        for c in (oscn_chain m) do append links ("{\"name\":" + (oscn_quote c.name) + ",\"class\":" + (oscn_quote (classof c)) + ",\"path\":" + (oscn_quote (oscn_mapFile c)) + "}")
        append maps ("{\"name\":" + (oscn_quote m.name) + ",\"class\":" + (oscn_quote (classof m)) + ",\"path\":" + (oscn_quote (oscn_mapFile m)) + ",\"offer\":" + (oscn_bool envList[2][i]) + ",\"chain\":[" + (oscn_join links) + "]}")
    )
    local lays = #()
    for i = 0 to (LayerManager.count - 1) do
    (
        local ly = LayerManager.getLayer i
        local parentName = ""
        try (local p = ly.getParent(); if (p != undefined) do parentName = p.name) catch()
        append lays ("{\"name\":" + (oscn_quote ly.name) + ",\"visible\":" + (oscn_bool ly.on) + ",\"frozen\":" + (oscn_bool ly.isfrozen) + ",\"render\":" + (oscn_bool ly.renderable) + ",\"parent\":" + (oscn_quote parentName) + "}")
    )
    local total = geometry.count + shapes.count
    local objs = oscn_nodesInfo objHandles
    local xr = #()
    for i = 1 to (xrefs.getXRefFileCount()) do
    (
        local x = xrefs.getXRefFile i
        append xr ("{\"file\":" + (oscn_quote (filenameFromPath x.filename)) + ",\"path\":" + (oscn_quote x.filename) + ",\"enabled\":" + (oscn_bool (not x.disabled)) + "}")
    )
    local active = "null"
    try (local vc = viewport.getCamera(); if (vc != undefined) do active = vc.inode.handle as string) catch()
    local envName = "null"
    local envCls = "null"
    if (environmentMap != undefined) do (envName = oscn_quote environmentMap.name; envCls = oscn_quote (classof environmentMap))
    "{\"file\":" + (oscn_quote maxFileName) + ",\"folder\":" + (oscn_quote maxFilePath) + ",\"output_dir\":" + (oscn_quote (getDir #renderoutput)) \
        + ",\"engine\":" + (oscn_quote (oscn_engineName())) + ",\"width\":" + (renderWidth as string) + ",\"height\":" + (renderHeight as string) \
        + ",\"active_camera\":" + active + ",\"env_name\":" + envName + ",\"env_class\":" + envCls + ",\"object_total\":" + (total as string) \
        + ",\"cameras\":[" + (oscn_join cams) + "],\"lights\":[" + (oscn_join shines) + "],\"maps\":[" + (oscn_join maps) + "],\"layers\":[" + (oscn_join lays) \
        + "],\"objects\":" + objs + ",\"xrefs\":[" + (oscn_join xr) + "]}"
)

-- ---------------------------------------------------------------- lasting IDs of the nodes and layers setups use

-- A merge gives nodes new handles and a rename changes names: every node and layer a setup uses gets an ID of its
-- own in its app data, which travels with it (save, merge, rename). Ported from OpenManager (Carles Llavata),
-- GPL-3.0-or-later. The slot is OpenScene's own ("OSID"), so another tool's IDs are never read as these.
global oscn_uidSlot = 1330858308

fn oscn_uidOf obj = (local u = undefined; try (u = getAppData obj oscn_uidSlot) catch(); if (u == undefined) then "" else (u as string))

-- every node that has an ID, as uid -> the nodes with it (two, when a file was merged twice)
fn oscn_uidIndex =
(
    local d = Dictionary #string
    for o in objects do
    (
        local u = oscn_uidOf o
        if (u != "") do (if (HasDictValue d u) then append (GetDictValue d u) o else PutDictValue d u #(o))
    )
    d
)

-- the ID of each of these nodes, made for one that has none or shares it with another node; "" for a missing node
fn oscn_stampNodes handles =
(
    local index = undefined
    for h in handles collect
    (
        local n = maxOps.getNodeByHandle h
        if (n == undefined) then ""
        else
        (
            if (index == undefined) do index = oscn_uidIndex()
            local u = oscn_uidOf n
            if (u == "" or ((HasDictValue index u) and (GetDictValue index u).count > 1)) do
            (
                u = genGuid()
                setAppData n oscn_uidSlot u
                PutDictValue index u #(n)
            )
            u
        )
    )
)

fn oscn_stampLayers names =
(
    for nm in names collect
    (
        local ly = LayerManager.getLayerFromName nm
        if (ly == undefined) then ""
        else
        (
            local r = ly.layerAsRefTarg
            if ((oscn_uidOf r) == "") do setAppData r oscn_uidSlot (genGuid())
            oscn_uidOf r
        )
    )
)

-- where the nodes of these references are now: refs #(#(handle, uid, name), ...) -> #(#(handle, name), ...). The node
-- at the stored handle is kept when it has the same ID (or the reference has none yet); else the node with that ID;
-- else the only node with that name. -2: the stored handle is another node now; -1: not in the scene.
fn oscn_resolveNodes refs =
(
    local index = undefined
    for r in refs collect
    (
        local h = r[1]
        local uid = r[2]
        local nm = r[3]
        local n = if (h != undefined and h >= 0) then (maxOps.getNodeByHandle h) else undefined
        local found = undefined
        if (n != undefined and (uid == "" or (oscn_uidOf n) == uid)) do found = n
        if (found == undefined and uid != "") do
        (
            if (index == undefined) do index = oscn_uidIndex()
            if (HasDictValue index uid) do found = (GetDictValue index uid)[1]
        )
        if (found == undefined and nm != "") do
        (
            local same = getNodeByName nm all:true
            if (same.count == 1) do found = same[1]
        )
        if (found != undefined) then #(found.inode.handle, found.name)
        else if (n != undefined) then #(-2, nm)
        else #(-1, nm)
    )
)

-- every layer that has an ID, as "uid|name" lines
fn oscn_layerUids =
(
    local ss = stringStream ""
    for i = 0 to (LayerManager.count - 1) do
    (
        local ly = LayerManager.getLayer i
        local u = oscn_uidOf ly.layerAsRefTarg
        if (u != "") do format "%|%\n" u ly.name to:ss
    )
    ss as string
)

-- ---------------------------------------------------------------- reading and writing properties

global oscn_setPath
fn oscn_setPath obj parts idx val =
(
    local key = parts[idx] as name
    if (idx == parts.count) then
    (
        setProperty obj key val
    )
    else
    (
        local sub = getProperty obj key
        oscn_setPath sub parts (idx + 1) val
        -- plain values come back as copies and have to be written back
        if (isKindOf sub Point3 or isKindOf sub Point2 or isKindOf sub Color or isKindOf sub Point4) do setProperty obj key sub
    )
)

global oscn_getPath
fn oscn_getPath obj parts idx =
(
    local sub = getProperty obj (parts[idx] as name)
    if (idx == parts.count) then sub else (oscn_getPath sub parts (idx + 1))
)

-- the Daylight's date and time come as plain numbers from their controller, not as sub-objects
fn oscn_cleanProp prop = (if (matchPattern prop pattern:"controller.solar_*.controller.value") then (substituteString prop ".controller.value" "") else prop)

global oscn_set
fn oscn_set obj prop val =
(
    if (obj == undefined) do return false
    -- 3ds Max takes a Daylight for a group head: its settings are its own
    if (isValidNode obj and isGroupHead obj and ((classof obj) as string) != "DaylightAssemblyHead") then
    (
        for c in obj.children do oscn_set c prop val
    )
    else
    (
        local parts = filterString (oscn_cleanProp prop) "."
        local same = false
        try (same = ((oscn_getPath obj parts 1) == val)) catch()
        if (not same) do (try (oscn_setPath obj parts 1 val) catch (format "OpenScene: % . % -> %\n" obj prop (getCurrentException())))
    )
    true
)

-- returns the value, or the text "<none>" when the object doesn't have it
fn oscn_get obj prop =
(
    if (obj == undefined) do return "<none>"
    try
    (
        local v = oscn_getPath obj (filterString (oscn_cleanProp prop) ".") 1
        case (classof v) of
        (
            BooleanClass: v
            Integer: v
            Integer64: (v as integer)
            Float: v
            Double: (v as float)
            String: v
            default: "<none>"
        )
    )
    catch ("<none>")
)

fn oscn_node h = (if h == undefined then undefined else maxOps.getNodeByHandle h)

fn oscn_setNode h prop val = oscn_set (oscn_node h) prop val
fn oscn_getNode h prop = oscn_get (oscn_node h) prop
fn oscn_setLayer nm prop val = oscn_set (LayerManager.getLayerFromName nm) prop val
fn oscn_setMap cls nm prop val = oscn_set (oscn_findMap cls nm) prop val
fn oscn_getMap cls nm prop = oscn_get (oscn_findMap cls nm) prop
fn oscn_setRS prop val = oscn_set renderers.current prop val
fn oscn_getRS prop = oscn_get renderers.current prop

-- ---------------------------------------------------------------- what a setup does

-- the view locked in the Render Setup dialog (padlock on) as a viewport ID, or 0 when the render follows the active view.
-- rendViewID counts from 1, like viewport.activeViewportID.
fn oscn_lockedView = (if (not rendUseActiveView and rendViewID > 0) then rendViewID else 0)

-- puts the camera in the locked view only: the active view and a maximized layout are left as they were
fn oscn_setCameraInView n id =
(
    local prev = viewport.activeViewportID
    if (id == prev) do (viewport.setCamera n; return true)
    local wasMaxed = (viewport.numViews == 1)
    if wasMaxed do max tool maximize
    local ok = false
    try
    (
        for i = 1 to viewport.numViews while not ok do
        (
            viewport.activeViewport = i
            if (viewport.activeViewportID == id) do ok = true
        )
        if ok do viewport.setCamera n
    )
    catch()
    try (viewport.activeViewportID = prev) catch()
    if wasMaxed do max tool maximize
    if (not ok) do viewport.setCamera n -- the locked view is not in this layout any more
    true
)

-- mode 0: the active viewport; 1: only when it shows a perspective, camera or user view; 2: the locked render view
fn oscn_setCamera h locked mode:0 =
(
    local n = oscn_node h
    if (n == undefined) do return false
    local locked_id = if (mode == 2) then (oscn_lockedView()) else 0
    if (locked_id > 0) then oscn_setCameraInView n locked_id
    else
    (
        local doit = true
        if (mode == 1) do doit = (findItem #(#view_persp_user, #view_camera, #view_iso_user) (viewport.getType())) > 0
        if doit do viewport.setCamera n
    )
    local flags = if locked then #all else #none
    try (setTransformLockFlags n flags) catch()
    try (if (n.target != undefined) do setTransformLockFlags n.target flags) catch()
    true
)

fn oscn_setRes w h =
(
    if (renderWidth != w) do renderWidth = w
    if (renderHeight != h) do renderHeight = h
    true
)

fn oscn_switch obj onOff =
(
    local target = obj
    local cls = (classof obj) as string
    if (cls == "DaylightAssemblyHead" and obj.sun != undefined) then target = obj.sun
    else if (cls == "Sun_Positioner" and obj.parent != undefined) then target = obj.parent
    try
    (
        if (hasProperty target #on) then (if target.on != onOff do target.on = onOff)
        else if (hasProperty target #enabled) do (if target.enabled != onOff do target.enabled = onOff)
    )
    catch()
)

-- switch every sun (or dome) off and the chosen ones on; keep: array of handles (empty = none)
fn oscn_setLights domes keep =
(
    local keepNodes = for h in keep where (h != undefined and h >= 0) collect (oscn_node h)
    keepNodes = for n in keepNodes where (isValidNode n) collect n
    for l in lights where (superclassof l == light) do
    (
        local match = if domes then (oscn_isDome l) else (oscn_isSun l)
        -- the sun inside a Daylight that stays on is switched through its Daylight
        if (match and (findItem keepNodes l) == 0 and (l.parent == undefined or (findItem keepNodes l.parent) == 0)) do oscn_switch l false
    )
    if (not domes) do
    (
        for h in helpers where (((classof h) as string) == "DaylightAssemblyHead" and (findItem keepNodes h) == 0) do oscn_switch h false
    )
    for n in keepNodes do oscn_switch n true
    true
)

fn oscn_isFStorm = (oscn_engineName() == "FStorm")

fn oscn_setEnv cls nm sunHandle =
(
    local m = oscn_findMap cls nm
    if (m == undefined) do return false
    oscn_keepMap m
    if (oscn_isFStorm()) then
    (
        renderers.current.environment_texture_on = true
        renderers.current.environment_texture = m
        environmentMap = undefined
    )
    else
    (
        if (cls == "Physical_Sun___Sky_Environment" and sunHandle != undefined and sunHandle >= 0) do
        (
            local sn = oscn_node sunHandle
            if (sn != undefined) do try (m.sun_position_object = sn) catch()
        )
        if (environmentMap != m) do environmentMap = m
        if (not useEnvironmentMap) do useEnvironmentMap = on
    )
    true
)

-- the n-th map that mixes the environment tabs (a Corona Mix set to Add), made the first time
fn oscn_mixMap n =
(
    local nm = "OSCN_EnvMix_" + (formattedPrint n format:"02d")
    local m = oscn_findMap "CoronaMix" nm
    if (m == undefined) do
    (
        m = CoronaMix()
        m.name = nm
    )
    oscn_keepMap m
    m
)

fn oscn_setIf obj prop v = (if ((getProperty obj prop) != v) do setProperty obj prop v)

-- several environment tabs at once, like a LightMix: items = #(#(class, name, intensity), ...) of the tabs that are on.
-- They are added together through Corona Mix maps (Add), each one multiplied by its intensity.
fn oscn_setEnvMix items =
(
    local maps = #()
    local amounts = #()
    for it in items do
    (
        local m = oscn_findMap it[1] it[2]
        if (m != undefined) do (oscn_keepMap m; append maps m; append amounts (it[3] as float))
    )
    local top = undefined
    if (maps.count == 1 and (abs (amounts[1] - 1.0)) < 0.0001) then top = maps[1]
    else if (maps.count >= 1) do
    (
        for i = 1 to (amax 1 (maps.count - 1)) do
        (
            local mx = oscn_mixMap i
            oscn_setIf mx #mixOperation 0
            oscn_setIf mx #mixAmount 1.0
            oscn_setIf mx #mixInSRgb false
            oscn_setIf mx #texmapBottomOn true
            oscn_setIf mx #texmapBottom (if (i == 1) then maps[1] else top)
            oscn_setIf mx #multiplierBottom (if (i == 1) then amounts[1] else 1.0)
            if (maps.count == 1) then
            (
                oscn_setIf mx #texmapTop undefined
                oscn_setIf mx #texmapTopOn false
                oscn_setIf mx #colorTop (color 0 0 0)
            )
            else
            (
                oscn_setIf mx #texmapTopOn true
                oscn_setIf mx #texmapTop maps[i + 1]
                oscn_setIf mx #multiplierTop amounts[i + 1]
            )
            top = mx
        )
    )
    if (top == undefined) then environmentMap = undefined
    else
    (
        if (environmentMap != top) do environmentMap = top
        if (not useEnvironmentMap) do useEnvironmentMap = on
    )
    true
)

-- a small picture of an HDRI for the quick browser (when there is no .jpg next to it): read by 3ds Max, saved as a .jpg
fn oscn_hdriPreview src dst w h =
(
    local ok = false
    local b = undefined
    local t = undefined
    try
    (
        b = openBitmap src
        if (b != undefined) do
        (
            t = bitmap w h color:black
            copy b t
            t.filename = dst
            save t
            ok = doesFileExist dst
        )
    )
    catch (format "OpenScene: preview of % -> %\n" src (getCurrentException()))
    try (if (t != undefined) do close t) catch()
    try (if (b != undefined) do close b) catch()
    ok
)

fn oscn_envOff =
(
    environmentMap = undefined
    if (oscn_isFStorm()) do
    (
        try (renderers.current.environment_texture_on = false) catch()
        try (renderers.current.environment_texture = undefined) catch()
    )
    true
)

fn oscn_setOutput path =
(
    if (path == "") then
    (
        rendSaveFile = false
        rendOutputFilename = ""
    )
    else
    (
        rendSaveFile = true
        rendOutputFilename = path
        -- render elements of Corona, Redshift and FStorm follow the main file: name_element.ext
        local eng = oscn_engineName()
        -- a .cxr carries every render element (and the LightMix) inside it: no separate file per element,
        -- otherwise 3ds Max writes each element as its own .cxr as well
        local multi = (toLower (getFilenameType path)) == ".cxr"
        if multi then
        (
            local re = maxOps.GetCurRenderElementMgr()
            for i = 0 to (re.NumRenderElements() - 1) do (try (re.SetRenderElementFilename i "") catch())
        )
        else if (eng == "Corona" or eng == "Redshift" or eng == "FStorm") do
        (
            local re = maxOps.GetCurRenderElementMgr()
            for i = 0 to (re.NumRenderElements() - 1) do
            (
                local e = re.GetRenderElement i
                local pieces = filterString (getFilenameFile path) "."
                local frameText = pieces[pieces.count]
                if (pieces.count > 1 and (frameText as integer) != undefined) then
                (
                    local stem = pieces[1]
                    for u = 2 to (pieces.count - 1) do stem += "." + pieces[u]
                    re.SetRenderElementFilename i ((getFilenamePath path) + stem + "_" + e.elementname + "." + frameText + (getFilenameType path))
                )
                else
                (
                    re.SetRenderElementFilename i ((getFilenamePath path) + (getFilenameFile path) + "_" + e.elementname + (getFilenameType path))
                )
            )
        )
    )
    true
)

fn oscn_makeDir path =
(
    local d = getFilenamePath path
    if (d != "" and not (doesDirectoryExist d)) do makeDir d all:true
    true
)

-- kind: 0 single, 1 range, 2 list
fn oscn_setTime kind single start end nth list setType:true =
(
    case kind of
    (
        0:
        (
            local f = single as time
            if (f < animationRange.start) then animationRange = interval f animationRange.end
            else if (f > animationRange.end) then animationRange = interval animationRange.start f
            sliderTime = f
            if setType do rendTimeType = 1
        )
        1:
        (
            local s = start as time
            local e = end as time
            if (e > s) do animationRange = interval s e
            rendStart = s
            rendEnd = e
            sliderTime = s
            rendNThFrame = amax 1 nth
            if setType do rendTimeType = 3
        )
        2:
        (
            rendPickupFrames = list
            if setType do rendTimeType = 4
        )
    )
    true
)

fn oscn_setXref file onOff =
(
    for i = 1 to (xrefs.getXRefFileCount()) do
    (
        local x = xrefs.getXRefFile i
        if ((filenameFromPath x.filename) == file) do
        (
            if (x.disabled == onOff) do x.disabled = (not onOff)
            if (x.hidden == onOff) do x.hidden = (not onOff)
        )
    )
    true
)

-- before a render: the camera goes to the locked view through oscn_setCamera (mode 2), the active view stays
fn oscn_renderView =
(
    try (renderSceneDialog.close()) catch()
    true
)

-- ---------------------------------------------------------------- saved setups

-- Files saved before 2.0.0 keep their setups, their maps and the environment mix maps under one of the old keys below
-- (newest first). They are read like ours, and moved to the keys above the first time the file is saved with this version.
global oscn_oldDat = #("PuzlesSM_Dat", "DrawfieldSM_Dat")
global oscn_oldMaps = #("PuzlesSM_Maps", "DrawfieldSM_Maps")
global oscn_oldMix = #("PZSM_EnvMix", "DFSM_EnvMix")

fn oscn_readKey key =
(
    if (isProperty rootNode key) then ((getProperty rootNode key) as string) else ""
)

-- the setups of such a file, as text ("" when it has none)
fn oscn_readOldSetups =
(
    for k in oscn_oldDat do
    (
        local t = oscn_readKey (k as name)
        if (t != "") do return t
    )
    ""
)

fn oscn_hasLegacy =
(
    local found = false
    for k in (oscn_oldDat + oscn_oldMaps) where (isProperty rootNode (k as name)) do found = true
    found
)

-- the environment mix maps of such a file take the current name, so they are used again instead of made anew
fn oscn_renameOldMixMaps =
(
    local c = undefined
    c = oscn_classNamed "CoronaMix" textureMap
    if (c != undefined) do
        for m in (getClassInstances c) do
            for old in oscn_oldMix where (matchPattern m.name pattern:(old + "*")) do
                m.name = "OSCN_EnvMix" + (substring m.name (old.count + 1) -1)
    true
)

fn oscn_dropLegacy =
(
    for k in oscn_oldMaps where (isProperty rootNode (k as name)) do
    (
        try (for m in (getProperty rootNode (k as name)) where (m != undefined) do oscn_keepMap m) catch()
    )
    for i = (custAttributes.count rootNode) to 1 by -1 do
    (
        local ca = custAttributes.get rootNode i
        local old = false
        if (ca != undefined) do
            for k in (oscn_oldDat + oscn_oldMaps) where (isProperty ca (k as name)) do old = true
        if old do custAttributes.delete rootNode i
    )
    true
)

fn oscn_saveSetups data =
(
    if (not (isProperty rootNode #OpenScene_Dat)) do custAttributes.add rootNode oscn_attrDef
    if (rootNode.OpenScene_Dat != data) do
    (
        rootNode.OpenScene_Dat = data
        setSaveRequired true
    )
    if (oscn_hasLegacy()) do
    (
        oscn_dropLegacy()
        setSaveRequired true
    )
    true
)

-- ---------------------------------------------------------------- cameras

fn oscn_newCamera =
(
    local cam = undefined
    local eng = oscn_engineName()
    try
    (
        if (eng == "Corona") then cam = (oscn_newOf "CoronaCam" camera)
        else if (eng == "V-Ray") then cam = (oscn_newOf "VRayPhysicalCamera" camera)
    )
    catch()
    if (cam == undefined) do cam = Physical()
    try (cam.transform = (inverse (getViewTM()))) catch()
    try (cam.name = uniqueName "OpenScene_Camera") catch()
    viewport.setCamera cam
    cam.inode.handle
)

fn oscn_selectedHandles = (for o in selection collect o.inode.handle)

fn oscn_selectHandles hs =
(
    local ns = for h in hs collect (oscn_node h)
    ns = for n in ns where (isValidNode n) collect n
    if (ns.count > 0) then select ns else clearSelection()
    true
)

-- ---------------------------------------------------------------- render

fn oscn_render =
(
    oscn_cancel = false
    oscn_rendering = true
    local failed = undefined
    try
    (
        try (renderSceneDialog.close()) catch()
        SetQuietMode true
        try (clearFrameBuffer()) catch()
        max quick render
    )
    catch
    (
        failed = getCurrentException()
    )
    SetQuietMode false
    oscn_rendering = false
    if (failed != undefined) then failed else (if oscn_cancel then "canceled" else "done")
)

fn oscn_checkAbort =
(
    try (if ((dotNetClass "Autodesk.Max.GlobalInterface").Instance.COREInterface13.CheckForRenderAbort) do oscn_cancel = true) catch()
)

fn oscn_stop =
(
    oscn_cancel = true
    try ((dotNetClass "Autodesk.Max.GlobalInterface").Instance.COREInterface13.AbortRender()) catch()
    try (CoronaRenderer.CoronaFp.stopRender()) catch()
    try (vrayEndProgressiveRender()) catch()
    true
)

-- ---------------------------------------------------------------- more modules

-- viewport background: 1 gradient, 2 solid, 3 environment, 4 custom file
fn oscn_setBackground kind path =
(
    case kind of
    (
        1: (try (viewport.EnableSolidBackgroundColorMode false) catch(); viewport.DispBkgImage = false)
        2: (try (viewport.EnableSolidBackgroundColorMode true) catch(); viewport.DispBkgImage = false)
        3: (backgroundImageFileName = ""; viewport.DispBkgImage = true)
        4:
        (
            if (path != "" and doesFileExist path) do
            (
                backgroundImageFileName = path
                try (setAsBackground (openBitmap path)) catch()
            )
            viewport.DispBkgImage = true
        )
    )
    true
)

fn oscn_atmospherics =
(
    local items = #()
    for i = 1 to numAtmospherics do
    (
        local a = getAtmospheric i
        append items ("{\"name\":" + (oscn_quote a.name) + ",\"class\":" + (oscn_quote (classof a)) + ",\"active\":" + (oscn_bool (isActive a)) + "}")
    )
    "[" + (oscn_join items) + "]"
)

fn oscn_setAtmos nm onOff =
(
    for i = 1 to numAtmospherics do
    (
        local a = getAtmospheric i
        if (a.name == nm and (isActive a) != onOff) do setActive a onOff
    )
    true
)

fn oscn_elements =
(
    local re = maxOps.GetCurRenderElementMgr()
    local items = #()
    for i = 0 to (re.NumRenderElements() - 1) do
    (
        local e = re.GetRenderElement i
        append items ("{\"name\":" + (oscn_quote e.elementName) + ",\"class\":" + (oscn_quote (classof e)) + ",\"enabled\":" + (oscn_bool e.enabled) + "}")
    )
    "[" + (oscn_join items) + "]"
)

fn oscn_setElement nm onOff =
(
    local re = maxOps.GetCurRenderElementMgr()
    for i = 0 to (re.NumRenderElements() - 1) do
    (
        local e = re.GetRenderElement i
        if (e.elementName == nm and e.enabled != onOff) do e.enabled = onOff
    )
    true
)

-- Render Setup's own scripts (Common > Scripts: a file run before each render, one after it, each with its switch).
-- A render preset keeps them too, so loading one could set a script for the next render: maxlink.load_preset reads
-- them before the load and writes them back after it.
fn oscn_renderSetupScripts = #(usePreRendScript, preRendScript, usePostRendScript, postRendScript)

fn oscn_setRenderSetupScripts v =
(
    if (usePreRendScript != (v[1] == true)) do usePreRendScript = (v[1] == true)
    local pre = if (v[2] == undefined) then "" else (v[2] as string)
    if (preRendScript != pre) do preRendScript = pre
    if (usePostRendScript != (v[3] == true)) do usePostRendScript = (v[3] == true)
    local post = if (v[4] == undefined) then "" else (v[4] as string)
    if (postRendScript != post) do postRendScript = post
    true
)

fn oscn_loadPreset path =
(
    if (path != "" and doesFileExist path) then
    (
        try (renderSceneDialog.close()) catch()
        renderPresets.LoadAll 0 path
    )
    else false
)

fn oscn_savePreset path =
(
    makeDir (getFilenamePath path) all:true
    renderPresets.SaveAll 0 path
)

-- the renderer's plain settings as JSON (for the Render Override card)
fn oscn_rsSnapshot =
(
    local r = renderers.current
    local items = #()
    for n in (getPropNames r) do
    (
        local v = undefined
        try (v = getProperty r n) catch()
        local c = classof v
        local txt = case c of
        (
            BooleanClass: (oscn_bool v)
            Integer: (v as string)
            Float: (if (bit.isNAN v) then undefined else (v as string))
            String: (oscn_quote v)
            default: undefined
        )
        if (txt != undefined) do append items ((oscn_quote n) + ":" + txt)
    )
    "{" + (oscn_join items) + "}"
)

fn oscn_runCode code =
(
    if (code != undefined and code != "") do
    (
        try (execute code) catch (format "OpenScene script: %\n" (getCurrentException()))
    )
    true
)

global oscn_preRenderFile = ""
global oscn_postRenderFile = ""
global oscn_preRenderCode = ""
global oscn_postRenderCode = ""
fn oscn_preRender =
(
    if (oscn_preRenderFile != "" and doesFileExist oscn_preRenderFile) do (try (fileIn oscn_preRenderFile) catch (format "OpenScene pre-render script: %\n" (getCurrentException())))
    oscn_runCode oscn_preRenderCode
)
fn oscn_postRender =
(
    if (oscn_postRenderFile != "" and doesFileExist oscn_postRenderFile) do (try (fileIn oscn_postRenderFile) catch (format "OpenScene post-render script: %\n" (getCurrentException())))
    oscn_runCode oscn_postRenderCode
)
fn oscn_setRenderScripts preFile postFile preCode postCode =
(
    oscn_preRenderFile = preFile
    oscn_postRenderFile = postFile
    oscn_preRenderCode = preCode
    oscn_postRenderCode = postCode
    callbacks.removeScripts id:#oscnRender
    if (preFile != "" or preCode != "") do callbacks.addScript #preRender "oscn_preRender()" id:#oscnRender
    if (postFile != "" or postCode != "") do callbacks.addScript #postRender "oscn_postRender()" id:#oscnRender
    true
)

-- Corona post-production (tone mapping, bloom & glare, sharpening, LUT...) through the VFB's own .conf files
fn oscn_postLoad path = (try (CoronaRenderer.CoronaFp.loadPostSettings path) catch (-1))

fn oscn_snapshotViewport path =
(
    makeDir (getFilenamePath path) all:true
    local b = gw.getViewportDib()
    b.filename = path
    save b
    close b
    true
)

fn oscn_snapshotVfb path =
(
    local b = undefined
    try (b = getLastRenderedImage copy:true) catch()
    if (b == undefined) then false else
    (
        makeDir (getFilenamePath path) all:true
        b.filename = path
        save b
        close b
        true
    )
)

fn oscn_isRendering =
(
    local t = 0
    try (t = CoronaRenderer.CoronaFp.getRenderType()) catch()
    t
)

-- every texture map in the scene, as "class|name" lines (for map settings such as camera overrides)
fn oscn_texmaps =
(
    local ss = stringStream ""
    for m in (oscn_cacheFrom (oscn_allMaps())) do format "%|%\n" ((classof m) as string) m.name to:ss
    ss as string
)

fn oscn_findTexmap cls nm =
(
    local same = oscn_mapsNamed cls nm
    if (same.count == 0) then undefined else same[1]
)

-- Batch Render (3ds Max's own) from setups: a scene state and a view per setup
fn oscn_batchView camHandle viewName stateName presetPath outPath w h =
(
    local cam = oscn_node camHandle
    if (cam == undefined) do return false
    local i = batchRenderMgr.FindView viewName
    if (i != 0) do batchRenderMgr.DeleteView i
    local v = batchRenderMgr.CreateView cam
    v.name = viewName
    if (stateName != "") do (sceneStateMgr.Delete stateName; sceneStateMgr.CaptureAllParts stateName; v.sceneStateName = stateName)
    if (presetPath != "") do v.presetFile = presetPath
    v.overridePreset = true
    v.width = w
    v.height = h
    if (outPath != "") do v.outputFilename = outPath
    true
)

-- ---------------------------------------------------------------- environment / lights helpers

fn oscn_samePath a b = (toLower (substituteString a "/" "\\")) == (toLower (substituteString b "/" "\\"))

-- the bitmap map of this file: one that is already in the scene, or a new one named after the file
fn oscn_hdriBitmap path =
(
    local eng = oscn_engineName()
    local classes = if (eng == "Corona") then #("CoronaBitmap") else if (eng == "V-Ray") then #("VRayBitmap", "VRayHDRI") else #("Bitmaptexture")
    for m in (oscn_allMaps()) where ((findItem classes ((classof m) as string)) > 0 and (oscn_samePath (oscn_mapFile m) path)) do return m
    local m = undefined
    try
    (
        if (eng == "Corona") then (m = oscn_newOf "CoronaBitmap" textureMap; m.filename = path)
        else if (eng == "V-Ray") then (m = oscn_newOf "VRayBitmap" textureMap; m.HDRIMapName = path)
    )
    catch()
    if (m == undefined) do (m = Bitmaptexture(); m.filename = path)
    m.name = getFilenameFile path
    m
)

-- a colour correction (or select) over an HDRI: a copy of it over the new HDRI, so its settings stay and other setups keep theirs
global oscn_wrapHdri
fn oscn_wrapHdri m bmp =
(
    if (oscn_isBitmapClass m) do return bmp
    local n = 0
    try (n = getNumSubTexmaps m) catch()
    for i = 1 to n do
    (
        local sub = undefined
        try (sub = getSubTexmap m i) catch()
        if (sub != undefined and (oscn_hdrLevel sub) > 0) do
        (
            local nm = (filterString m.name "@")[1] + "@" + bmp.name
            local have = oscn_findMap ((classof m) as string) nm
            if (have != undefined) do return have
            local c = copy m
            setSubTexmap c i (oscn_wrapHdri sub bmp)
            c.name = nm
            return c
        )
    )
    bmp
)

-- double click in the HDRI browser: returns the map the environment uses now
fn oscn_useHdri path curCls curName =
(
    local bmp = oscn_hdriBitmap path
    local cur = if (curCls != "" and curCls != undefined) then (oscn_findMap curCls curName) else undefined
    local m = if (cur != undefined and not (oscn_isBitmapClass cur) and (oscn_hdrLevel cur) > 0) then (oscn_wrapHdri cur bmp) else bmp
    oscn_keepMap m
    "{\"class\":" + (oscn_quote (classof m)) + ",\"name\":" + (oscn_quote m.name) + "}"
)

fn oscn_newHdri path =
(
    local m = oscn_hdriBitmap path
    oscn_keepMap m
    environmentMap = m
    useEnvironmentMap = on
    "{\"class\":" + (oscn_quote (classof m)) + ",\"name\":" + (oscn_quote m.name) + "}"
)

fn oscn_newSky =
(
    local eng = oscn_engineName()
    local m = undefined
    try
    (
        if (eng == "Corona") then m = oscn_newOf "CoronaSky" textureMap
        else if (eng == "V-Ray") then m = oscn_newOf "VRaySky" textureMap
    )
    catch()
    if (m == undefined) do m = Physical_Sun___Sky_Environment()
    m.name = uniqueName "OSCN_Sky_"
    oscn_keepMap m
    environmentMap = m
    useEnvironmentMap = on
    "{\"class\":" + (oscn_quote (classof m)) + ",\"name\":" + (oscn_quote m.name) + "}"
)

fn oscn_showInMedit cls nm =
(
    local m = oscn_findMap cls nm
    if (m == undefined) do return false
    try (meditMaterials[activeMeditSlot] = m) catch()
    try (MatEditor.Open()) catch()
    true
)

-- the layers selected in a Layer / Scene Explorer; else the layers of the selected objects; else the active layer
fn oscn_selectedLayers =
(
    local names = #()
    try
    (
        for i = 1 to (SceneExplorerManager.GetExplorerCount()) do
        (
            local nm0 = SceneExplorerManager.GetExplorerName i
            local ex = if (SceneExplorerManager.ExplorerIsOpen nm0) then (SceneExplorerManager.GetExplorer nm0) else undefined
            if (ex != undefined) do
            (
                for it in (ex.SelectedItems()) where (not (isValidNode it)) do
                (
                    local nm = undefined
                    try (nm = it.name) catch()
                    if (nm != undefined and (LayerManager.getLayerFromName nm) != undefined) do appendIfUnique names nm
                )
            )
        )
    )
    catch()
    if (names.count == 0) do (for o in selection do appendIfUnique names o.layer.name)
    if (names.count == 0) do (try (append names LayerManager.current.name) catch())
    names
)

-- ---------------------------------------------------------------- scene events

-- #scene events come in bursts (a merge of 10 000 objects fires #nodeCreated 10 000 times): only the first one of a
-- burst goes to Python, the others wait until Python has read the scene again (it calls oscn_sceneRead)
global oscn_scenePending = false
fn oscn_sceneRead = (oscn_scenePending = false; true)
fn oscn_fire what =
(
    if (oscn_notify != undefined) do
    (
        if (what == #scene) then
        (
            if (not oscn_scenePending) do
            (
                oscn_scenePending = true
                try (oscn_notify what) catch (format "OpenScene: %\n" (getCurrentException()))
            )
        )
        else (try (oscn_notify what) catch (format "OpenScene: %\n" (getCurrentException())))
    )
)

fn oscn_watch onOff =
(
    callbacks.removeScripts id:#oscn
    if onOff do
    (
        callbacks.addScript #filePreOpen "oscn_fire #preopen" id:#oscn
        callbacks.addScript #systemPreReset "oscn_fire #preopen" id:#oscn
        callbacks.addScript #systemPreNew "oscn_fire #preopen" id:#oscn
        callbacks.addScript #filePostOpen "oscn_fire #file" id:#oscn
        callbacks.addScript #systemPostReset "oscn_fire #file" id:#oscn
        callbacks.addScript #systemPostNew "oscn_fire #file" id:#oscn
        callbacks.addScript #filePostMerge "oscn_fire #scene" id:#oscn
        callbacks.addScript #filePreSave "oscn_fire #presave" id:#oscn
        callbacks.addScript #nodeCreated "oscn_fire #scene" id:#oscn
        callbacks.addScript #nodePostDelete "oscn_fire #scene" id:#oscn
        callbacks.addScript #nodeRenamed "oscn_fire #scene" id:#oscn
        callbacks.addScript #layerCreated "oscn_fire #scene" id:#oscn
        callbacks.addScript #layerDeleted "oscn_fire #scene" id:#oscn
        callbacks.addScript #postRendererChange "oscn_fire #scene" id:#oscn
        callbacks.addScript #postRender "oscn_checkAbort()" id:#oscn
        try (callbacks.addScript #viewportChange "oscn_fire #view" id:#oscn) catch()
        callbacks.addScript #preSystemShutdown "oscn_fire #shutdown" id:#oscn
    )
    true
)

ok
