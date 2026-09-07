; ============================================================
; PC-Action 安装包构建脚本 (Inno Setup)
; 作用：生成标准安装包，安装时让用户选择安装到 C 盘或 D 盘，
;       并自动创建开始菜单/桌面快捷方式、支持卸载。
;
; 使用方法：
;   1) 先安装 Inno Setup 6 (https://jrsoftware.org/isinfo.php)
;   2) 把打包好的 PC-Action.exe 放到本脚本同级的 dist\ 目录
;   3) 用 Inno Setup 打开本文件，点 Build，或命令行：
;      "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
; ============================================================

#define MyAppName "PC-Action"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PC-Action"
#define MyAppExeName "PC-Action.exe"

[Setup]
; 卸载信息注册到"添加/删除程序"
AppId={{4B7E2CE7-ABCD-4C1E-9B21-AC7239E20A5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
; 默认安装位置建议设为 D 盘（用户仍可在向导页改成 C 盘或其他盘）
; 若想默认 C 盘，把下一行改为：近默认目录 {autopf}
;DefaultDirName=D:\{#MyAppName}
; 允许用户改到任意盘/目录（这正是"选 C 盘或 D 盘"的关键）
DisableDirPage=no
DefaultGroupName={#MyAppName}
; 打包后放置的 exe（相对本脚本文件）
SourceDir=..\dist
OutputDir=..\installer\output
OutputBaseFilename=PC-Action-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 生成 64 位安装，解包到 Program Files 时不重定向到 x86
ArchitecturesInstallIn64BitMode=x64compatible
; ---------- 可选：安装包图标（需要 app.ico） ----------
; SetupIconFile=app.ico
; 卸载图标
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
; 简体中文（Optional 环境变量控制；缺少 .islu 文件时可去掉这行用英文默认）
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: unchecked
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
; 单文件版：只安装这一个 exe（内部已包含 icons/定价配置）
Source: "{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; 若改用"目录版"（onedir），把上面那行注释掉，改用下面几行整个目录拷入：
; Source: ".\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后勾选运行
Filename: "{app}\{#MyAppExeName}"; Description: "立即运行 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; 开机自启（配合上面的 autostart 任务）
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart