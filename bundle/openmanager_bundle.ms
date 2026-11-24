-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenManager.bundle start: the bundle's post-start-up script (3ds Max 2025 and later). Says where OpenManager is
-- (oscn_bundleHome, read by the OpenManager macro), runs openmanager.startup (the settings of the versions before,
-- what older installs left, the toolbar the first time) and adds the file-open check of OpenManager_startup.ms.
-- Not oscn_home: an OpenScene.bundle still installed sets that one too, in the session in which this one removes it.
-- Declared before the block: inside ( ) an unknown name would compile as a local.
global oscn_bundleHome, oscn_settingsDir
(
    oscn_bundleHome = pathConfig.normalizePath ((getFilenamePath (getThisScriptFilename())) + "..\\OpenManager")
    -- the path is the bundle's own folder, never text read from a file; between double quotes, which a Windows path
    -- cannot hold (an apostrophe it can: a user called O'Brien)
    local py = "import sys\nd = r\"" + oscn_bundleHome + "\"\nif d not in sys.path: sys.path.insert(0, d)\n"
    try (python.Execute (py + "import openmanager.startup\nopenmanager.startup.run()"))
    catch (format "OpenManager: start-up failed: %\n" (getCurrentException()))
    -- the file-open check that a start-up script of OpenManager 0.x, left by its .mzp, added in this session
    callbacks.removeScripts id:#omgrStartup
    fileIn (oscn_bundleHome + "\\OpenManager_startup.ms")
)
