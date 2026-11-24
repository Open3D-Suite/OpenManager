-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenManager: when a file with setups saved by OpenManager 0.x or by another scene manager is opened and the window
-- is closed, offer to open it to convert them. (Settings > Notification turns this off.) Loaded by
-- openmanager_bundle.ms, which sets oscn_settingsDir.
global oscn_isOpen, oscn_settingsDir
global oscn_startupCheck
fn oscn_startupCheck =
(
    try
    (
        local wanted = true
        if (oscn_settingsDir != undefined and oscn_settingsDir != "") do
        (
            local flag = oscn_settingsDir + "\\notify.txt"
            if (doesFileExist flag) do
            (
                local f = openFile flag
                if (f != undefined) do (wanted = ((readLine f) != "0"); close f)
            )
        )
        -- Once the file has setups of this version (OpenScene_Dat, the name they have had since OpenScene) nothing is
        -- asked: they always win over the other ones, which are never read again. (The other keys hold setups saved
        -- before 2.0.0, converted on the next save.)
        local ours = false
        for k in #(#OpenScene_Dat, #PuzlesSM_Dat, #DrawfieldSM_Dat) where (isProperty rootNode k) do
            if (((getProperty rootNode k) as string).count > 60) do ours = true
        local zero = (isProperty rootNode #OpenManager_Dat) and (((getProperty rootNode #OpenManager_Dat) as string).count > 60)
        local other = (isProperty rootNode #SceneManager_Dat) and (((getProperty rootNode #SceneManager_Dat) as string).count > 25)
        if (wanted and (zero or other) and not ours and oscn_isOpen != true and not (GetQuietMode()) and not (IsNetServer())) do
        (
            local who = if zero then "OpenManager 0.x" else "another scene manager"
            if (queryBox ("This file has setups saved by " + who + ".\nOpen OpenManager to convert them?") title:"OpenManager") do macros.run "OpenManager" "OpenManager"
        )
    )
    catch (format "OpenManager: file-open check failed: %\n" (getCurrentException()))
)
callbacks.removeScripts id:#oscnStartup
callbacks.addScript #filePostOpen "oscn_startupCheck()" id:#oscnStartup
