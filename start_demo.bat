@echo off
cd /d "%~dp0"
echo.
echo =============================================
echo   MeetOps AI  -  start_demo
echo =============================================
echo.

:: 0. Docker Desktop must be running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running.
    echo         Start it, wait for the whale icon, then run this again.
    pause & exit /b 1
)

:: 1. Kill any non-Docker process on port 8000
echo [1/4] Checking port 8000...
powershell -NoProfile -Command "$procs=(netstat -ano|Select-String ':8000.*LISTENING'|ForEach-Object{($_ -split '\s+')[-1]}|Sort-Object -Unique);foreach($p in $procs){$proc=Get-Process -Id $p -EA SilentlyContinue;if($proc){if($proc.ProcessName -notmatch 'docker|wsl'){Write-Host('        Killing stray '+$proc.ProcessName+' (PID '+$p+') on port 8000');Stop-Process -Id $p -Force}else{Write-Host('        Port held by '+$proc.ProcessName+' (PID '+$p+') - OK')}}}"
echo.

:: 2. Start Docker stack
echo [2/4] Starting Docker stack (db + backend)...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] docker compose up failed. Is Docker Desktop healthy?
    pause & exit /b 1
)
echo.

:: 3. Poll /health every 2 s, up to 30 tries (60 s max)
echo [3/4] Waiting for backend to be healthy...
set TRIES=0
:POLL
timeout /t 2 /nobreak < nul >nul 2>&1
powershell -NoProfile -Command "try{(New-Object Net.WebClient).DownloadString('http://127.0.0.1:8000/health')|Out-Null;exit 0}catch{exit 1}" < nul >nul 2>&1
if %errorlevel% equ 0 goto HEALTHY
set /a TRIES=%TRIES%+1
if %TRIES% geq 30 (
    echo [ERROR] Backend not healthy after 60 s.
    echo         Diagnose with: docker compose logs backend
    pause & exit /b 1
)
echo         Attempt %TRIES%/30...
goto POLL
:HEALTHY
echo         Backend is healthy!
echo.

:: 4. Launch Streamlit (skip if already running on 8501)
echo [4/4] Starting Streamlit frontend...
powershell -NoProfile -Command "try{(New-Object Net.WebClient).DownloadString('http://127.0.0.1:8501')|Out-Null;exit 0}catch{exit 1}" < nul >nul 2>&1
if %errorlevel% equ 0 (
    echo         Already running at http://localhost:8501
) else (
    pushd "%~dp0frontend"
    start "MeetOps Streamlit" cmd /k "call venv\Scripts\activate.bat && streamlit run streamlit_app.py"
    popd
    echo         Launched in a new window.
)
echo.
echo =============================================
echo   MeetOps AI is running
echo.
echo   App  : http://localhost:8501
echo   Docs : http://localhost:8000/docs
echo.
echo   Stop : stop_demo.bat
echo =============================================
echo.
