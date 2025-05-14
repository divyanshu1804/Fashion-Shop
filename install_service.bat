@echo off
echo Installing Fashion Store E-commerce as a Windows Service...

REM Check if NSSM is installed
where nssm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo NSSM (Non-Sucking Service Manager) is not installed.
    echo Please download it from https://nssm.cc/download and add it to your PATH.
    echo Or run: winget install nssm
    exit /b 1
)

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SERVICE_NAME=FashionStore"

REM Install the service
echo Installing %SERVICE_NAME% service...
nssm install %SERVICE_NAME% "%PYTHON_PATH%" "%CURRENT_DIR%production_server.py"
nssm set %SERVICE_NAME% DisplayName "Fashion Store E-commerce"
nssm set %SERVICE_NAME% Description "Fashion Store E-commerce web application"
nssm set %SERVICE_NAME% AppDirectory "%CURRENT_DIR%"
nssm set %SERVICE_NAME% AppStdout "%CURRENT_DIR%service_stdout.log"
nssm set %SERVICE_NAME% AppStderr "%CURRENT_DIR%service_stderr.log"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

echo Service installed successfully!
echo To start the service, run: nssm start %SERVICE_NAME%
echo To stop the service, run: nssm stop %SERVICE_NAME%
echo To remove the service, run: nssm remove %SERVICE_NAME%

pause 