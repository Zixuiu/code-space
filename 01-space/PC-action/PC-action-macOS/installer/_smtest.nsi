Unicode true
!include "LogicLib.nsh"
!include "FileFunc.nsh"
OutFile "output\_test\smtest.exe"
RequestExecutionLevel user
Section
  SetShellVarContext current
  FileOpen $0 "$EXEDIR\smpath.txt" w
  FileWrite $0 "current SMPROGRAMS = $SMPROGRAMS$\r$\n"
  FileWrite $0 "exists(created) = "
  CreateDirectory "$SMPROGRAMS\ZZTest"
  ${If} ${FileExists} "$SMPROGRAMS\ZZTest"
    FileWrite $0 "yes$\r$\n"
  ${Else}
    FileWrite $0 "no$\r$\n"
  ${EndIf}
  SetShellVarContext all
  FileWrite $0 "all SMPROGRAMS = $SMPROGRAMS$\r$\n"
  FileClose $0
SectionEnd
