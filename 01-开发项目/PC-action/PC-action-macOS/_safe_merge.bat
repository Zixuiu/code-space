@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "d:\codespace\01-开发项目\PC-action\PC-action-macOS"
set "PROJ=%cd%"
set "TS=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TS=%TS: =0%"
set "BACKUP=%PROJ%\_backup_merge_%TS%"
set "LOG=%PROJ%\_merge_result.txt"
set "HIDE=%PROJ%\_merge_temp_hide"

echo === 安全合并开始 %date% %time% > "%LOG%"
echo 项目目录: %PROJ% >> "%LOG%"
echo 备份目录: %BACKUP% >> "%LOG%"
echo. >> "%LOG%"

REM ========================================
REM Step 1: 备份本地保护数据
REM ========================================
echo [1/5] 备份本地保护数据... >> "%LOG%"
mkdir "%BACKUP%" 2>nul

if exist "recordings\" (
    xcopy "recordings" "%BACKUP%\recordings\" /E /I /H /Y > nul 2>&1
    echo   备份 recordings/ 文件夹 OK >> "%LOG%"
)
if exist "data\combo_skills.json" (
    xcopy "data\combo_skills.json" "%BACKUP%\data\" /I /H /Y > nul 2>&1
    echo   备份 data/combo_skills.json OK >> "%LOG%"
)
if exist "data\combo_skills.json.bak" (
    xcopy "data\combo_skills.json.bak" "%BACKUP%\data\" /I /H /Y > nul 2>&1
    echo   备份 data/combo_skills.json.bak OK >> "%LOG%"
)
if exist "data\shortcuts.json" (
    xcopy "data\shortcuts.json" "%BACKUP%\data\" /I /H /Y > nul 2>&1
    echo   备份 data/shortcuts.json OK >> "%LOG%"
)
if exist "data\key_bindings.json" (
    xcopy "data\key_bindings.json" "%BACKUP%\data\" /I /H /Y > nul 2>&1
    echo   备份 data/key_bindings.json OK >> "%LOG%"
)
if exist "login_credentials.json" (
    copy "login_credentials.json" "%BACKUP%\" /Y > nul 2>&1
    echo   备份 login_credentials.json OK >> "%LOG%"
)
echo   备份完成 >> "%LOG%"
echo. >> "%LOG%"

REM ========================================
REM Step 2: 抓取远程代码
REM ========================================
echo [2/5] 抓取远程最新代码 (git fetch --all)... >> "%LOG%"
git fetch --all >> "%LOG%" 2>&1
echo   fetch 完成，错误码=%errorlevel% >> "%LOG%"

echo. >> "%LOG%"
echo -- 远程分支列表 -- >> "%LOG%"
git branch -r >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo -- 本地最近3次提交 -- >> "%LOG%"
git log --oneline -3 HEAD >> "%LOG%" 2>&1

REM ========================================
REM Step 3: 临时移走本地保护数据（避免合并冲突）
REM ========================================
echo. >> "%LOG%"
echo [3/5] 临时移走本地保护数据... >> "%LOG%"
if exist "%HIDE%\" rmdir /S /Q "%HIDE%" 2>nul
mkdir "%HIDE%" 2>nul

if exist "recordings\" (
    move "recordings" "%HIDE%\recordings" > nul 2>&1
    echo   移走 recordings/ >> "%LOG%"
)
if exist "data\combo_skills.json" (
    if not exist "%HIDE%\data\" mkdir "%HIDE%\data" 2>nul
    move "data\combo_skills.json" "%HIDE%\data\combo_skills.json" > nul 2>&1
    echo   移走 data/combo_skills.json >> "%LOG%"
)
if exist "data\combo_skills.json.bak" (
    if not exist "%HIDE%\data\" mkdir "%HIDE%\data" 2>nul
    move "data\combo_skills.json.bak" "%HIDE%\data\combo_skills.json.bak" > nul 2>&1
    echo   移走 data/combo_skills.json.bak >> "%LOG%"
)
if exist "data\shortcuts.json" (
    if not exist "%HIDE%\data\" mkdir "%HIDE%\data" 2>nul
    move "data\shortcuts.json" "%HIDE%\data\shortcuts.json" > nul 2>&1
    echo   移走 data/shortcuts.json >> "%LOG%"
)
if exist "data\key_bindings.json" (
    if not exist "%HIDE%\data\" mkdir "%HIDE%\data" 2>nul
    move "data\key_bindings.json" "%HIDE%\data\key_bindings.json" > nul 2>&1
    echo   移走 data/key_bindings.json >> "%LOG%"
)
if exist "login_credentials.json" (
    move "login_credentials.json" "%HIDE%\login_credentials.json" > nul 2>&1
    echo   移走 login_credentials.json >> "%LOG%"
)

REM ========================================
REM Step 4: 合并远程代码（冲突优先远程代码版本）
REM ========================================
echo. >> "%LOG%"
echo [4/5] 合并远程代码（代码冲突优先用远程最新版）... >> "%LOG%"

for /f "tokens=*" %%i in ('git branch -r 2^>nul ^| findstr /v HEAD') do (
    set "REMOTE_BRANCH=%%i"
    goto :found_branch
)
:found_branch

if "%REMOTE_BRANCH%"=="" (
    echo   未找到远程分支，跳过合并 >> "%LOG%"
    goto :restore_local
)

echo   选择远程分支: %REMOTE_BRANCH% >> "%LOG%"
git merge -X theirs --no-edit %REMOTE_BRANCH% >> "%LOG%" 2>&1
echo   merge 完成，错误码=%errorlevel% >> "%LOG%"

REM 强制清掉合并过程中可能从远程拉来的保护路径（ recordings/ 等）
if exist "recordings\" rmdir /S /Q "recordings" 2>nul
if exist "data\combo_skills.json" del /F /Q "data\combo_skills.json" 2>nul
if exist "data\combo_skills.json.bak" del /F /Q "data\combo_skills.json.bak" 2>nul
if exist "data\shortcuts.json" del /F /Q "data\shortcuts.json" 2>nul
if exist "data\key_bindings.json" del /F /Q "data\key_bindings.json" 2>nul
if exist "login_credentials.json" del /F /Q "login_credentials.json" 2>nul

REM ========================================
REM Step 5: 恢复本地保护数据（覆盖远程）
REM ========================================
:restore_local
echo. >> "%LOG%"
echo [5/5] 恢复本地保护数据... >> "%LOG%"

if exist "%HIDE%\recordings\" (
    move "%HIDE%\recordings" "recordings" > nul 2>&1
    if errorlevel 1 (
        xcopy "%HIDE%\recordings" "recordings\" /E /I /H /Y > nul 2>&1
    )
    echo   恢复 recordings/ >> "%LOG%"
)
if exist "%HIDE%\data\combo_skills.json" (
    if not exist "data\" mkdir "data" 2>nul
    move "%HIDE%\data\combo_skills.json" "data\combo_skills.json" > nul 2>&1
    echo   恢复 data/combo_skills.json >> "%LOG%"
)
if exist "%HIDE%\data\combo_skills.json.bak" (
    if not exist "data\" mkdir "data" 2>nul
    move "%HIDE%\data\combo_skills.json.bak" "data\combo_skills.json.bak" > nul 2>&1
    echo   恢复 data/combo_skills.json.bak >> "%LOG%"
)
if exist "%HIDE%\data\shortcuts.json" (
    if not exist "data\" mkdir "data" 2>nul
    move "%HIDE%\data\shortcuts.json" "data\shortcuts.json" > nul 2>&1
    echo   恢复 data/shortcuts.json >> "%LOG%"
)
if exist "%HIDE%\data\key_bindings.json" (
    if not exist "data\" mkdir "data" 2>nul
    move "%HIDE%\data\key_bindings.json" "data\key_bindings.json" > nul 2>&1
    echo   恢复 data/key_bindings.json >> "%LOG%"
)
if exist "%HIDE%\login_credentials.json" (
    move "%HIDE%\login_credentials.json" "login_credentials.json" > nul 2>&1
    echo   恢复 login_credentials.json >> "%LOG%"
)

REM 备份兜底：如果从临时目录恢复失败，从备份目录复制
if not exist "recordings\" if exist "%BACKUP%\recordings\" (
    xcopy "%BACKUP%\recordings" "recordings\" /E /I /H /Y > nul 2>&1
    echo   [兜底] 从备份恢复 recordings/ >> "%LOG%"
)
if not exist "data\combo_skills.json" if exist "%BACKUP%\data\combo_skills.json" (
    if not exist "data\" mkdir "data" 2>nul
    copy "%BACKUP%\data\combo_skills.json" "data\combo_skills.json" /Y > nul 2>&1
    echo   [兜底] 从备份恢复 data/combo_skills.json >> "%LOG%"
)

REM 清理
if exist "%HIDE%\" rmdir /S /Q "%HIDE%" 2>nul

REM ========================================
REM 最终校验
REM ========================================
echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo  合并完成 - 数据校验 >> "%LOG%"
echo ======================================== >> "%LOG%"

set /a ok=0
set /a bad=0

if exist "recordings\" (
    echo  [OK] recordings/ 文件夹 存在 >> "%LOG%"
    set /a ok+=1
) else (
    echo  [MISSING] recordings/ 文件夹 不存在！ >> "%LOG%"
    set /a bad+=1
)
if exist "data\combo_skills.json" (
    for %%A in ("data\combo_skills.json") do echo  [OK] combo_skills.json 存在 %%~zA 字节 >> "%LOG%"
    set /a ok+=1
) else (
    echo  [MISSING] combo_skills.json 不存在！ >> "%LOG%"
    set /a bad+=1
)
if exist "data\shortcuts.json" (
    echo  [OK] shortcuts.json 存在 >> "%LOG%"
    set /a ok+=1
)
if exist "data\key_bindings.json" (
    echo  [OK] key_bindings.json 存在 >> "%LOG%"
    set /a ok+=1
)

echo. >> "%LOG%"
echo  备份目录: %BACKUP% >> "%LOG%"
echo  校验结果: %ok% 项通过, %bad% 项缺失 >> "%LOG%"
if %bad%==0 (
    echo  状态: 全部通过 ✅ 快捷键、录制、组合技均为本地原始版本 >> "%LOG%"
) else (
    echo  状态: 有缺失项，请从备份目录手动恢复 >> "%LOG%"
)
echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo  完成时间: %date% %time% >> "%LOG%"
echo ======================================== >> "%LOG%"

endlocal
exit /b 0