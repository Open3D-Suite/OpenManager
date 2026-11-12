-- OpenScene installer (runs when the .mzp is dropped on 3ds Max)
(
	local title = "OpenScene"
	local src = getFilenamePath (getSourceFileName())

	local osInstCopyTree
	fn osInstCopyTree fromDir toDir =
	(
		makeDir toDir all:true
		for f in (getFiles (fromDir + "*")) do
		(
			local target = toDir + (filenameFromPath f)
			if (doesFileExist target) do deleteFile target
			copyFile f target
		)
		for d in (getDirectories (fromDir + "*")) do
		(
			local leaf = pathConfig.stripPathToLeaf (trimRight d "\\/")
			if (leaf != "__pycache__") do osInstCopyTree d (toDir + leaf + "\\")
		)
	)

	if ((maxVersion())[1] < 27000) then
	(
		messageBox "OpenScene needs 3ds Max 2025 or newer (Python 3 + PySide6)." title:title
	)
	else
	(
		-- an open window is closed first so its files can be replaced
		try (python.Execute "import sys\nm = sys.modules.get('openscene')\nif m:\n    m.close()\n    for k in [k for k in list(sys.modules) if k == 'openscene' or k.startswith('openscene.')]:\n        del sys.modules[k]") catch()

		local dst = (getDir #userScripts) + "\\OpenScene\\"
		osInstCopyTree (src + "OpenScene\\") dst

		-- small startup script: offers to open the window when a file with setups to convert is opened
		local su = (getDir #userStartupScripts) + "\\OpenScene_startup.ms"
		if (doesFileExist su) do deleteFile su
		copyFile (dst + "OpenScene_startup.ms") su
		try (fileIn su) catch()

		-- icons for the light and the dark theme
		for theme in #("Dark", "Light") do
		(
			local idir = (getDir #userIcons) + "\\" + theme + "\\"
			makeDir idir all:true
			for f in (getFiles (src + "icons\\" + theme + "\\*.png")) do
			(
				local target = idir + (filenameFromPath f)
				if (doesFileExist target) do deleteFile target
				copyFile f target
			)
		)

		-- the macro: copied so 3ds Max loads it on every start, and run now so it is there straight away
		local mcr = (getDir #userMacros) + "\\OpenScene.mcr"
		if (doesFileExist mcr) do deleteFile mcr
		copyFile (src + "OpenScene.mcr") mcr
		fileIn mcr
		try (colorMan.reInitIcons()) catch()

		local msg = "OpenScene is installed.\n\n"
		msg += "Customize > Customize User Interface\n"
		msg += "Group: Main UI   Category: OpenScene\n"
		msg += "Action: OpenScene\n\n"
		msg += "Drag it to a toolbar or a menu. Open it now?"
		if (queryBox msg title:title) do macros.run "OpenScene" "OpenScene"
	)
)
