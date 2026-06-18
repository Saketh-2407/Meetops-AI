@echo off
cd /d "%~dp0"
echo.
echo =============================================
echo   MeetOps AI  -  stop_demo
echo =============================================
echo.

:: 1. Stop Streamlit
echo [1/2] Stopping Streamlit...

:: Kill the cmd window launched by start_demo (and its child Python process)
taskkill /fi "WindowTitle eq MeetOps Streamlit" /t /f >nul 2>&1

:: Belt-and-suspenders: kill whatever Python process owns port 8501
powershell -NoProfile -Command "$p=(netstat -ano|Select-String ':8501.*LISTENING'|ForEach-Object{($_ -split '\s+')[-1]}|Select-Object -First 1);if($p){$proc=Get-Process -Id $p -EA SilentlyContinue;if($proc -and $proc.ProcessName -match 'python'){Write-Host('        Killed '+$proc.ProcessName+' PID '+$p);Stop-Process -Id $p -Force}else{Write-Host('        Port 8501: nothing to kill')}}"

echo         Done.
echo.

:: 2. Stop Docker stack
echo [2/2] Stopping Docker stack...
docker info >nul 2>&1
if %errorlevel% equ 0 (
    docker compose down
) else (
    echo         Docker Desktop not running - nothing to stop.
)
echo.
echo =============================================
echo   MeetOps AI stopped.
echo =============================================
echo.
