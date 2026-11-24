-- SPDX-License-Identifier: GPL-3.0-or-later
-- OpenScene: Customize User Interface > Group: Main UI > Category: OpenScene > OpenScene
-- oscn_home is set by the bundle's start-up script (openscene_bundle.ms): the folder with the openscene package.
-- 3ds Max loads the macro before that script runs: both names are declared here, so they compile as globals.
global oscn_home, oscn_isOpen

macroScript OpenScene
    category:"OpenScene"
    internalCategory:"OpenScene"
    buttonText:"OpenScene"
    toolTip:"OpenScene"
    iconName:"OpenScene"
(
    on isChecked return (oscn_isOpen == true)

    on execute do
    (
        if (oscn_home == undefined or not (doesDirectoryExist oscn_home)) then
        (
            messageBox "OpenScene is not installed.\nInstall it from the Open3D launcher, with 3ds Max closed." title:"OpenScene"
        )
        else
        (
            -- the path is the bundle's own folder, never text read from a file; between double quotes, which a
            -- Windows path cannot hold (an apostrophe it can: a user called O'Brien)
            python.Execute ("import sys\nd = r\"" + oscn_home + "\"\nif d not in sys.path: sys.path.insert(0, d)\nimport openscene\nopenscene.toggle()")
        )
    )
)
