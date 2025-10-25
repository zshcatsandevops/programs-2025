@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ===== Admin check =====
net session >nul 2>&1
if not "%errorlevel%"=="0" (
  echo Requesting Administrator privileges...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -Verb RunAs -FilePath '%~f0'"
  exit /b
)

rem ===== Timestamped log =====
for /f %%a in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"') do set "STAMP=%%a"
set "LOG=%TEMP%\win11_tuneup_%STAMP%.log"
call :log "Win11 Tune-up starting (log: %LOG%)"

rem ===== OS info (best-effort) =====
for /f "tokens=2,*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName ^| find "ProductName"') do set "PRODUCT=%%b"
call :log "Detected OS: %PRODUCT%"

rem ===== Feature toggles (1=on, 0=off) =====
set "CREATE_RESTORE_POINT=1"
set "DO_HEALTH_REPAIR=1"
set "CLEAN_TEMP=1"
set "CLEAN_COMPONENT_STORE=0"   rem Safe cleanup; skip by default
set "UPGRADE_APPS=1"
set "STORE_RESET=1"
set "SET_HIGH_PERFORMANCE=1"
set "TRY_ULTIMATE=1"
set "DISABLE_TRANSPARENCY=1"
set "DISABLE_ANIMATIONS=1"
set "RESET_NETWORK=0"           rem Off by default (requires reboot)

rem ===== Restore point =====
if "%CREATE_RESTORE_POINT%"=="1" (
  call :log "Creating system restore point (if System Protection is enabled)..."
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Checkpoint-Computer -Description 'win11_tuneup_%STAMP%' -RestorePointType 'MODIFY_SETTINGS' ^| Out-Null } catch { }"
)

rem ===== Health repair =====
if "%DO_HEALTH_REPAIR%"=="1" (
  call :log "Running DISM health checks..."
  DISM /Online /Cleanup-Image /CheckHealth >>"%LOG%" 2>&1
  DISM /Online /Cleanup-Image /ScanHealth >>"%LOG%" 2>&1

  call :log "Restoring component store health (DISM /RestoreHealth)..."
  DISM /Online /Cleanup-Image /RestoreHealth >>"%LOG%" 2>&1

  call :log "Running System File Checker (sfc /scannow)..."
  sfc /scannow >>"%LOG%" 2>&1

  call :log "Checking disk (chkdsk /scan)..."
  chkdsk /scan >>"%LOG%" 2>&1
)

rem ===== Temp cleanup =====
if "%CLEAN_TEMP%"=="1" (
  call :log "Cleaning TEMP folders..."
  for %%D in ("%TEMP%" "%SystemRoot%\Temp") do (
    if exist "%%~D\" (
      pushd "%%~D"
      del /f /s /q *.* >nul 2>&1
      popd
    )
  )
)

rem ===== Optional component store cleanup =====
if "%CLEAN_COMPONENT_STORE%"=="1" (
  call :log "Cleaning superseded components (no ResetBase)..."
  DISM /Online /Cleanup-Image /StartComponentCleanup >>"%LOG%" 2>&1
)

rem ===== App upgrades via winget (if available) =====
if "%UPGRADE_APPS%"=="1" (
  winget -v >nul 2>&1
  if "%errorlevel%"=="0" (
    call :log "Upgrading apps with winget (silent where possible)..."
    winget upgrade --all --include-unknown --silent --accept-source-agreements --accept-package-agreements >>"%LOG%" 2>&1
  ) else (
    call :log "winget not found; skipping app upgrades."
  )
)

rem ===== Reset Microsoft Store cache =====
if "%STORE_RESET%"=="1" (
  call :log "Resetting Microsoft Store cache (wsreset)..."
  start "" /wait wsreset.exe -i >>"%LOG%" 2>&1
)

rem ===== Power plan: High performance, then try Ultimate =====
if "%SET_HIGH_PERFORMANCE%"=="1" (
  call :log "Setting power plan to High performance..."
  powercfg -setactive scheme_max >>"%LOG%" 2>&1
)

if "%TRY_ULTIMATE%"=="1" (
  call :log "Trying to activate Ultimate Performance plan..."
  set "ULT_GUID="
  for /f "tokens=4" %%G in ('powercfg /list ^| findstr /I "Ultimate"') do set "ULT_GUID=%%G"
  if defined ULT_GUID (
    powercfg -setactive %ULT_GUID% >>"%LOG%" 2>&1
    call :log "Activated existing Ultimate Performance plan: %ULT_GUID%"
  ) else (
    for /f "tokens=4" %%G in ('powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 ^| findstr /I "GUID"') do set "ULT_GUID=%%G"
    if defined ULT_GUID (
      powercfg -setactive %ULT_GUID% >>"%LOG%" 2>&1
      call :log "Created & activated Ultimate Performance plan: %ULT_GUID%"
    ) else (
      call :log "Could not create Ultimate Performance plan; keeping High performance."
    )
  )
)

rem ===== Lightweight UI tweaks =====
if "%DISABLE_TRANSPARENCY%"=="1" (
  call :log "Disabling transparency effects..."
  reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f >nul 2>&1
)

if "%DISABLE_ANIMATIONS%"=="1" (
  call :log "Disabling taskbar and window animations (per-user)..."
  reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f >nul 2>&1
  reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarAnimations /t REG_DWORD /d 0 /f >nul 2>&1
  reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >nul 2>&1
)

rem ===== Optional network reset =====
if "%RESET_NETWORK%"=="1" (
  call :log "Resetting network stack (a reboot will be required)..."
  ipconfig /flushdns >>"%LOG%" 2>&1
  netsh winsock reset >>"%LOG%" 2>&1
  netsh int ip reset >>"%LOG%" 2>&1
)

call :log "Operation complete. Some changes require sign-out or restart."
echo.
echo Done. Log saved to: %LOG%
echo Consider restarting Windows to apply all changes.
goto :eof

:log
echo [%date% %time%] %~1
>>"%LOG%" echo [%date% %time%] %~1
goto :eof
