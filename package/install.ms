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

	-- Puts an "OpenScene" toolbar with the button in the user's interface, once: only when no toolbar has the button yet
	-- (the user may have placed it already). MAXScript has no call to add a button to a toolbar, so the current
	-- interface is saved, the toolbar is added to its .cuix file (XML) and the file is loaded again. The file is backed
	-- up first and put back if anything fails. Returns #added, #already or #failed.
	local osInstToolbar
	fn osInstToolbar =
	(
		local f = undefined
		local backup = undefined
		local result = #failed
		try
		(
			cui.saveConfig()
			f = cui.getConfigFile()
			if (f != undefined and (doesFileExist f)) do
			(
				local io = dotNetClass "System.IO.File"
				local txt = io.ReadAllText f
				if ((findString txt "actionID=\"OpenScene`OpenScene\"") != undefined) then result = #already
				else
				(
					local at = findString txt "</CUIWindows>"
					if (at != undefined) do
					(
						local nl = if ((findString txt "\r\n") != undefined) then "\r\n" else "\n"
						local win = "    <Window objectName=\"OpenScene\" name=\"OpenScene\" type=\"T\" cType=\"1\" toolbarRows=\"1\">" + nl
						win += "            <Items>" + nl
						win += "                <Item typeID=\"2\" type=\"CTB_MACROBUTTON\" width=\"0\" height=\"0\" controlID=\"0\" macroTypeID=\"3\" macroType=\"MB_TYPE_ACTION\" actionTableID=\"647394\" imageID=\"-1\" imageName=\"\" actionID=\"OpenScene`OpenScene\" tip=\"OpenScene\" label=\"OpenScene\" />" + nl
						win += "            </Items>" + nl
						win += "        </Window>" + nl + "    "
						backup = f + ".before-openscene"
						if (doesFileExist backup) do deleteFile backup
						copyFile f backup
						-- the block goes in front of the line that closes the list of windows
						local lineStart = at
						while (lineStart > 1 and txt[lineStart - 1] == " ") do lineStart -= 1
						txt = (substring txt 1 (lineStart - 1)) + "    " + win + (substring txt at -1)
						io.WriteAllText f txt (dotNetObject "System.Text.UTF8Encoding" true)
						cui.loadConfig f
						cui.showToolbar "OpenScene"
						result = #added
					)
				)
			)
		)
		catch
		(
			format "OpenScene installer: toolbar not added: %\n" (getCurrentException())
			if (backup != undefined and (doesFileExist backup)) do
			(
				try (deleteFile f; copyFile backup f; cui.loadConfig f) catch()
			)
			result = #failed
		)
		result
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

		-- the button on a toolbar of its own (skipped when a toolbar already has it)
		local bar = osInstToolbar()

		local msg = "OpenScene is installed.\n\n"
		if (bar == #added) then msg += "Its button is on the new \"OpenScene\" toolbar: drag the toolbar where you want it.\n\n"
		else if (bar == #already) then msg += "Its button is already on one of your toolbars.\n\n"
		else
		(
			msg += "To place its button: Customize > Customize User Interface\n"
			msg += "Group: Main UI   Category: OpenScene   Action: OpenScene\n\n"
		)
		msg += "Open it now?"
		if (queryBox msg title:title) do macros.run "OpenScene" "OpenScene"
	)
)
