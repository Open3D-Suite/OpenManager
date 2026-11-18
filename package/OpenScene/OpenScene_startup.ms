-- OpenScene: when a file with setups saved by another scene manager is opened and the window is closed, offer to
-- open it to convert them. (Settings > Notification turns this off.)
global oscn_isOpen
global oscn_startupCheck
fn oscn_startupCheck =
(
	try
	(
		local flag = (getDir #plugcfg) + "\\OpenScene_notify.txt"
		local wanted = true
		if (doesFileExist flag) do
		(
			local f = openFile flag
			if (f != undefined) do (wanted = ((readLine f) != "0"); close f)
		)
		-- Once the file has setups of OpenScene nothing is asked: they always win over the other ones, which are never
		-- read again. (The other keys hold setups saved before 2.0.0, converted on the next save.)
		local ours = false
		for k in #(#OpenScene_Dat, #PuzlesSM_Dat, #DrawfieldSM_Dat) where (isProperty rootNode k) do
			if (((getProperty rootNode k) as string).count > 60) do ours = true
		local other = (isProperty rootNode #SceneManager_Dat) and (((getProperty rootNode #SceneManager_Dat) as string).count > 25)
		if (wanted and other and not ours and oscn_isOpen != true and not (GetQuietMode()) and not (IsNetServer())) do
		(
			if (queryBox "This file has setups saved by another scene manager.\nOpen OpenScene to convert them?" title:"OpenScene") do macros.run "OpenScene" "OpenScene"
		)
	)
	catch()
)
callbacks.removeScripts id:#oscnStartup
callbacks.addScript #filePostOpen "oscn_startupCheck()" id:#oscnStartup
