-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenManager: Customize User Interface > Group: Main UI > Category: OpenManager > OpenManager
-- oscn_bundleHome is set by the bundle's start-up script (openmanager_bundle.ms): the folder with the openmanager
-- package.
-- 3ds Max loads the macro before that script runs: both names are declared here, so they compile as globals.
global oscn_bundleHome, oscn_isOpen

macroScript OpenManager
    category:"OpenManager"
    internalCategory:"OpenManager"
    buttonText:"OpenManager"
    toolTip:"OpenManager"
    iconName:"OpenManager"
(
    on isChecked return (oscn_isOpen == true)

    on execute do
    (
        if (oscn_bundleHome == undefined or not (doesDirectoryExist oscn_bundleHome)) then
        (
            messageBox "OpenManager is not installed.\nInstall it from the Open3D launcher, with 3ds Max closed." title:"OpenManager"
        )
        else
        (
            -- the path is the bundle's own folder, never text read from a file; between double quotes, which a
            -- Windows path cannot hold (an apostrophe it can: a user called O'Brien)
            python.Execute ("import sys\nd = r\"" + oscn_bundleHome + "\"\nif d not in sys.path: sys.path.insert(0, d)\nimport openmanager\nopenmanager.toggle()")
        )
    )
)
