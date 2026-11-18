-- OpenScene: removes everything the .mzp installed (run it from Scripting > Run Script).
-- The setups stored inside .max files are left as they are.
(
	try (python.Execute "import sys\nm = sys.modules.get('openscene')\nif m:\n    m.close()") catch()
	callbacks.removeScripts id:#oscn
	callbacks.removeScripts id:#oscnRender
	callbacks.removeScripts id:#oscnStartup

	local osUnDelDir
	fn osUnDelDir d = (if (doesDirectoryExist d) do try ((dotNetClass "System.IO.Directory").Delete (trimRight d "\\/") true) catch())

	-- the "OpenScene" toolbar the installer made (a button the user put on a toolbar of their own is left alone)
	local osUnToolbar
	fn osUnToolbar =
	(
		try
		(
			cui.saveConfig()
			local f = cui.getConfigFile()
			if (f != undefined and (doesFileExist f)) do
			(
				local io = dotNetClass "System.IO.File"
				local txt = io.ReadAllText f
				local s = findString txt "<Window objectName=\"OpenScene\""
				if (s != undefined) do
				(
					local rest = substring txt s -1
					local e = findString rest "</Window>"
					if (e != undefined) do
					(
						local stop = s + e - 1 + "</Window>".count
						while (s > 1 and txt[s - 1] == " ") do s -= 1
						while (stop <= txt.count and (txt[stop] == "\r" or txt[stop] == "\n")) do stop += 1
						txt = (substring txt 1 (s - 1)) + (substring txt stop -1)
						io.WriteAllText f txt (dotNetObject "System.Text.UTF8Encoding" true)
						cui.loadConfig f
					)
				)
			)
		)
		catch (format "OpenScene uninstaller: toolbar not removed: %\n" (getCurrentException()))
	)
	osUnToolbar()

	local cfg = (getDir #plugcfg) + "\\"
	local gone = #(
		(getDir #userMacros) + "\\OpenScene.mcr",
		(getDir #userStartupScripts) + "\\OpenScene_startup.ms",
		cfg + "OpenScene.json",
		cfg + "OpenScene_default.json",
		cfg + "OpenScene_notify.txt"
	)
	for theme in #("Dark", "Light") do
		for f in (getFiles ((getDir #userIcons) + "\\" + theme + "\\OpenScene_*.png")) do append gone f
	for f in gone where (doesFileExist f) do deleteFile f
	osUnDelDir (cfg + "OpenScene_hdri")
	osUnDelDir ((getDir #userScripts) + "\\OpenScene")
	messageBox "OpenScene was removed.\nRestart 3ds Max to drop it from the menus and toolbars." title:"OpenScene"
)
