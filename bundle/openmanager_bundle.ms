-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenManager.bundle start: the bundle's post-start-up script (3ds Max 2025 and later). Says where OpenManager is
-- (oscn_home, read by the OpenManager macro), runs openmanager.startup (settings of the 2.x versions, the old .mzp copy,
-- the toolbar the first time) and adds the file-open check of OpenManager_startup.ms.
-- Declared before the block: inside ( ) an unknown name would compile as a local.
global oscn_home, oscn_settingsDir
(
    oscn_home = pathConfig.normalizePath ((getFilenamePath (getThisScriptFilename())) + "..\\OpenManager")
    -- the path is the bundle's own folder, never text read from a file; between double quotes, which a Windows path
    -- cannot hold (an apostrophe it can: a user called O'Brien)
    local py = "import sys\nd = r\"" + oscn_home + "\"\nif d not in sys.path: sys.path.insert(0, d)\n"
    try (python.Execute (py + "import openmanager.startup\nopenmanager.startup.run()"))
    catch (format "OpenManager: start-up failed: %\n" (getCurrentException()))
    fileIn (oscn_home + "\\OpenManager_startup.ms")
)
