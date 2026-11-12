-- OpenScene
-- Customize User Interface > Group: Main UI > Category: OpenScene > OpenScene

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
		local dir = (getDir #userScripts) + "\\OpenScene"
		if (not (doesDirectoryExist dir)) then
		(
			messageBox "OpenScene is not installed.\nDrag OpenScene.mzp into 3ds Max again." title:"OpenScene"
		)
		else
		(
			python.Execute ("import sys\nd = r'" + dir + "'\nif d not in sys.path: sys.path.insert(0, d)\nimport openscene\nopenscene.toggle()")
		)
	)
)
