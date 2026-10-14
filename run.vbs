' 点小点开发启动脚本
' 一键启动 Flask 后端 + Vite 前端开发服务器，并打开浏览器

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' 项目根目录（脚本所在目录）
ProjectRoot = FSO.GetParentFolderName(WScript.ScriptFullName)

' Python 优先使用项目 .venv，否则使用 PATH 中的解释器；可在此填写自己的完整路径。
PythonExe = "python"
LocalPython = FSO.BuildPath(ProjectRoot, ".venv\Scripts\python.exe")
If FSO.FileExists(LocalPython) Then PythonExe = LocalPython

' 后端启动命令，路径加引号以支持文件夹名称中的空格。
BackendCmd = "cmd /k cd /d """ & ProjectRoot & "\backend"" && """ & PythonExe & """ app.py"

' 前端启动命令
FrontendCmd = "cmd /k cd /d """ & ProjectRoot & "\frontend"" && npm run dev"

' 以新窗口启动后端
WshShell.Run BackendCmd, 1, False

' 等待 2 秒让后端先启动
WScript.Sleep 2000

' 以新窗口启动前端
WshShell.Run FrontendCmd, 1, False

' 等待 3 秒让 Vite 启动
WScript.Sleep 3000

' 打开浏览器（Vite dev server，含 HMR，API 代理到 Flask:5000）
WshShell.Run "http://localhost:5173"
