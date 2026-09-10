; Action 安装包脚本（Inno Setup 6）
; 用法：装好 Inno Setup 后，右键本文件 → Compile，或命令行 iscc Action.iss
; 前置：dist\Action.exe 已存在（PyInstaller onefile 产物，自包含）

[Setup]
AppName=Action
AppVersion=1.0.0
AppPublisher=Action
DefaultDirName={autopf}\Action
DefaultGroupName=Action
OutputDir=..\dist_installer
OutputBaseFilename=Action-Setup-1.0.0
SetupIconFile=
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\Action.exe
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinese"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\Action.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Action"; Filename: "{app}\Action.exe"
Name: "{autodesktop}\Action"; Filename: "{app}\Action.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务"; Flags: unchecked

[Run]
Filename: "{app}\Action.exe"; Description: "启动 Action"; Flags: nowait postinstall skipifsilent
