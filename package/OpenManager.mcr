-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenManager: Customize User Interface > Group: Main UI > Category: OpenManager > OpenManager
-- oscn_bundleHome is set by the bundle's start-up script (openmanager_bundle.ms): the folder with the openmanager
-- package. oscn_isOpen is set by the package while its window is open.
-- Both are read through globalVars when a handler runs, never by their plain names: a toolbar button asks isChecked
-- while 3ds Max builds its interface, before the start-up script has made them globals, and a name the macro meets
-- before it is a global stays a local of the macro for the whole session, always undefined (the button would say
-- OpenManager is not installed).

macroScript OpenManager
    category:"OpenManager"
    internalCategory:"OpenManager"
    buttonText:"OpenManager"
    toolTip:"OpenManager"
    iconName:"OpenManager"
(
    on isChecked return ((globalVars.isGlobal #oscn_isOpen) and ((globalVars.get #oscn_isOpen) == true))

    on execute do
    (
        local home = if (globalVars.isGlobal #oscn_bundleHome) then (globalVars.get #oscn_bundleHome) else undefined
        if (not (isKindOf home String) or not (doesDirectoryExist home)) then
        (
            messageBox "OpenManager is not installed.\nInstall it from the Open3D launcher, with 3ds Max closed." title:"OpenManager"
        )
        else
        (
            -- the path is the bundle's own folder, never text read from a file; between double quotes, which a
            -- Windows path cannot hold (an apostrophe it can: a user called O'Brien)
            python.Execute ("import sys\nd = r\"" + home + "\"\nif d not in sys.path: sys.path.insert(0, d)\nimport openmanager\nopenmanager.toggle()")
        )
    )
)
