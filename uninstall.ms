-- OpenScene: removes everything the .mzp installed (run it from Scripting > Run Script).
-- The setups stored inside .max files are left as they are.
(
	try (python.Execute "import sys\nm = sys.modules.get('openscene')\nif m:\n    m.close()") catch()
	callbacks.removeScripts id:#oscn
	callbacks.removeScripts id:#oscnRender
	callbacks.removeScripts id:#oscnStartup

	local osUnDelDir
	fn osUnDelDir d = (if (doesDirectoryExist d) do try ((dotNetClass "System.IO.Directory").Delete (trimRight d "\\/") true) catch())

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
