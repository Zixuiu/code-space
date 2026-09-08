; ============================================================
;  PC-Action 安装脚本 (NSIS 3 / Unicode / 简体中文)
;
;  向导流程：
;    欢迎 → 许可协议 → 选择安装位置（C/D/E 任意盘）→ 附加选项 → 安装 → 完成
;
;  编译命令（installer 目录下执行）：
;    tools\nsis\nsis-3.10\makensis.exe /V2 setup.nsi
;  可选参数：
;    /DAPP_VERSION=1.0.1       指定版本号
;    /DREQUIRED_MB=900         指定安装所需磁盘空间(MB)
;
;  前置：已用 PyInstaller 生成 ..\dist\PC-Action\PC-Action.exe
; ============================================================

Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; ---------- 可由命令行覆盖的参数 ----------
!ifndef APP_VERSION
  !define APP_VERSION "1.0.0"
!endif
!ifndef REQUIRED_MB
  !define REQUIRED_MB "900"
!endif

; ---------- 基本信息 ----------
!define APP_NAME      "Action"
!define APP_EXE       "Action.exe"
!define APP_PUBLISHER "Action"
!define APP_URL       "https://477b6492.r8.cpolar.top"
!define UNINST_KEY    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Action"
!define DIST_DIR      "..\dist\Action"

Name "${APP_NAME} ${APP_VERSION}"
!ifdef PER_USER_INSTALL
  OutFile "output\_test\Action-Setup-test.exe"
!else
  OutFile "output\Action-${APP_VERSION}-Setup.exe"
!endif
InstallDir "$PROGRAMFILES64\${APP_NAME}"
; InstallDirRegKey 只认固定根键（不支持 SHCTX），按安装范围二选一
!ifdef PER_USER_INSTALL
  InstallDirRegKey HKCU "${UNINST_KEY}" "InstallLocation"
!else
  InstallDirRegKey HKLM "${UNINST_KEY}" "InstallLocation"
!endif
; 默认请求管理员权限（装到 Program Files / 写 HKLM 需要）；
; 编译测试版时可加 /DPER_USER_INSTALL 降级为普通权限（用于无人值守冒烟测试）
!ifdef PER_USER_INSTALL
  RequestExecutionLevel user
!else
  RequestExecutionLevel admin
!endif
SetCompressor /SOLID lzma
SetCompressorDictSize 64
ShowInstDetails show
ShowUninstDetails show
BrandingText "${APP_NAME} ${APP_VERSION}"

Icon "app.ico"
UninstallIcon "app.ico"

VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_NAME} Setup"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 ${APP_PUBLISHER}"

; ---------- 界面 ----------
!define MUI_ICON "app.ico"
!define MUI_UNICON "app.ico"
!define MUI_ABORTWARNING
!define MUI_UNABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "欢迎安装 ${APP_NAME} ${APP_VERSION}"
!define MUI_WELCOMEPAGE_TEXT "Action 是一款 Windows 桌面自动化工具：录下你的操作流程，之后一键自动重复执行。$\r$\n$\r$\n本向导会把它安装到你自己指定的位置（可以选 C 盘、D 盘或任意文件夹），并在开始菜单创建快捷方式。$\r$\n$\r$\n安装前请关闭正在运行的 Action。"
!define MUI_DIRECTORYPAGE_TEXT_TOP "请选择 ${APP_NAME} 的安装位置。$\r$\n默认优先放在 D:\${APP_NAME}；点“浏览(B)...”可改到 C 盘、D 盘或任意文件夹。$\r$\n$\r$\n所需空间约 ${REQUIRED_MB} MB，安装前会校验目标磁盘剩余空间。"
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "安装位置："
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "立即运行 ${APP_NAME}"
!define MUI_FINISHPAGE_LINK "访问 ${APP_NAME} 官网"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_URL}"

; ---------- 页面 ----------
!insertmacro MUI_PAGE_WELCOME
; NSIS 自带简体中文语言文件的底部提示写的是“[我同意(I)]”，与按钮文字“我接受”不一致，这里覆盖为一致文案
!define MUI_INNERTEXT_LICENSE_BOTTOM "如果你接受许可证的条款，请点击 [我接受(I)] 继续安装。你必须在同意后才能安装 ${APP_NAME} ${APP_VERSION}。"
!insertmacro MUI_PAGE_LICENSE "license.txt"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirPageLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

; ---------- 安装前初始化 ----------
Function .onInit
!ifdef PER_USER_INSTALL
  SetShellVarContext current
!else
  SetShellVarContext all
!endif

  ; 只允许一个安装实例
  System::Call 'kernel32::CreateMutex(i 0, i 0, t "PCActionSetupMutex") ?e'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION|MB_OK "安装程序已经在运行中。"
    Abort
  ${EndIf}

  ; 关闭正在运行的 PC-Action，避免文件被占用导致安装失败
  nsExec::Exec /TIMEOUT=3000 '"$SYSDIR\taskkill.exe" /F /IM "${APP_EXE}"'

  ; 命令行用 /D=xxx 显式指定了目录时，一切以它为准：
  ; 否则下面覆盖 $INSTDIR 会让静默安装（Setup.exe /S /D=路径）把文件装到别处。
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/D=" $R1
  ${If} ${Errors}
    ClearErrors

    ; 已装过则沿用上次的目录（覆盖/升级安装）
    ReadRegStr $1 SHCTX "${UNINST_KEY}" "InstallLocation"
    ${If} $1 == ""
      ReadRegStr $1 HKCU "${UNINST_KEY}" "InstallLocation"
    ${EndIf}
    ${If} $1 != ""
      StrCpy $INSTDIR $1
    ${Else}
      ; 没装过：默认放 D 盘（没有 D 盘则保持 Program Files）
      ; 注意：IfFileExists "D:\" 对驱动器根目录判定不可靠，改用 GetDriveType：
      ; 返回值 >1 表示该盘存在（2 可移动 / 3 本地磁盘 / 4 网络驱动器 / 5 光驱 / 6 RAM 盘）
      System::Call 'kernel32::GetDriveType(t "D:\\") i .r2'
      ${If} $2 > 1
        StrCpy $INSTDIR "D:\${APP_NAME}"
      ${EndIf}
    ${EndIf}
  ${EndIf}
FunctionEnd

; ---------- 安装目录校验 ----------
Function DirPageLeave
  ${GetRoot} "$INSTDIR" $0
  ${If} $0 == ""
    Return
  ${EndIf}
  ${DriveSpace} "$0" "/D=F /S=M" $1
  ${If} $1 == ""
    Return              ; 读不到就不阻断安装
  ${EndIf}
  ${If} $1 < ${REQUIRED_MB}
    MessageBox MB_ICONEXCLAMATION|MB_OK "目标磁盘剩余空间不足：$1 MB（建议 ${REQUIRED_MB} MB 以上）。$\r$\n请更换安装位置或清理磁盘后重试。"
    Abort
  ${EndIf}
FunctionEnd

; ---------- 主程序 ----------
Section "!${APP_NAME} 主程序（必选）" SEC_MAIN
  SectionIn RO
!ifdef PER_USER_INSTALL
  SetShellVarContext current
!else
  SetShellVarContext all
!endif
  SetOutPath "$INSTDIR"
  SetOverwrite on
  File /r "${DIST_DIR}\*.*"

  ; 用户数据目录（录制流程 / 登录信息 / 设置都放在这里）
  CreateDirectory "$INSTDIR\user_data"
  CreateDirectory "$INSTDIR\recordings"

  ; 卸载程序 + 添加/删除程序信息
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr   SHCTX "${UNINST_KEY}" "DisplayName"     "${APP_NAME} ${APP_VERSION}"
  WriteRegStr   SHCTX "${UNINST_KEY}" "DisplayVersion"  "${APP_VERSION}"
  WriteRegStr   SHCTX "${UNINST_KEY}" "Publisher"       "${APP_PUBLISHER}"
  WriteRegStr   SHCTX "${UNINST_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr   SHCTX "${UNINST_KEY}" "QuietUninstallString" '"$INSTDIR\uninstall.exe" /S'
  WriteRegStr   SHCTX "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   SHCTX "${UNINST_KEY}" "DisplayIcon"     "$INSTDIR\${APP_EXE},0"
  WriteRegStr   SHCTX "${UNINST_KEY}" "URLInfoAbout"    "${APP_URL}"
  WriteRegDWORD SHCTX "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD SHCTX "${UNINST_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD SHCTX "${UNINST_KEY}" "EstimatedSize" "$0"

  ; 开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

; ---------- 附加选项 ----------
Section "创建桌面快捷方式" SEC_DESKTOP
!ifdef PER_USER_INSTALL
  SetShellVarContext current
!else
  SetShellVarContext all
!endif
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
SectionEnd

Section "开机自动启动" SEC_AUTORUN
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}" '"$INSTDIR\${APP_EXE}"'
SectionEnd

; ---------- 组件说明 ----------
LangString DESC_SEC_MAIN    ${LANG_SIMPCHINESE} "Action 主程序及运行库（必选）"
LangString DESC_SEC_DESKTOP ${LANG_SIMPCHINESE} "在桌面上创建 Action 快捷方式"
LangString DESC_SEC_AUTORUN ${LANG_SIMPCHINESE} "开机登录后自动启动 Action（可随时在设置里关闭）"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN}    $(DESC_SEC_MAIN)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} $(DESC_SEC_DESKTOP)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_AUTORUN} $(DESC_SEC_AUTORUN)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ---------- 卸载前确认 ----------
Function un.onInit
!ifdef PER_USER_INSTALL
  SetShellVarContext current
!else
  SetShellVarContext all
!endif
  System::Call 'kernel32::CreateMutex(i 0, i 0, t "PCActionUninstMutex") ?e'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION|MB_OK "卸载程序已经在运行中。"
    Abort
  ${EndIf}
  MessageBox MB_ICONQUESTION|MB_YESNO "确定要卸载 ${APP_NAME} 吗？" /SD IDYES IDYES +2
  Abort
  nsExec::Exec /TIMEOUT=3000 '"$SYSDIR\taskkill.exe" /F /IM "${APP_EXE}"'
FunctionEnd

; ---------- 卸载 ----------
Section "Uninstall"
  ; 是否保留用户数据
  MessageBox MB_ICONQUESTION|MB_YESNO "是否保留用户数据（录制的流程、登录信息、个人设置）？$\r$\n$\r$\n选“是”保留，选“否”将一并删除。" /SD IDYES IDYES keep_data
  RMDir /r "$INSTDIR\user_data"
  RMDir /r "$INSTDIR\recordings"
  keep_data:

  Delete "$INSTDIR\${APP_EXE}"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\icons"
  RMDir /r "$INSTDIR\data"
  Delete "$INSTDIR\*.*"
  RMDir "$INSTDIR"

  ; 快捷方式
!ifdef PER_USER_INSTALL
  SetShellVarContext current
!else
  SetShellVarContext all
!endif
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"

  ; 注册表
  DeleteRegKey SHCTX "${UNINST_KEY}"
  DeleteRegValue SHCTX "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
SectionEnd
