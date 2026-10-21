@echo off
setlocal
pushd "%~dp0"
if not exist ".venv-windows\Scripts\python.exe" (
  echo Windows setup is needed. Run:
  echo powershell -ExecutionPolicy Bypass -File tools\setup_windows.ps1
  popd
  exit /b 1
)
".venv-windows\Scripts\python.exe" -c "import sys; assert sys.platform == 'win32'; from amp.app import main" >nul 2>&1
if errorlevel 1 (
  echo The Windows environment is incomplete or unusable. Run:
  echo powershell -ExecutionPolicy Bypass -File tools\setup_windows.ps1
  popd
  exit /b 1
)
".venv-windows\Scripts\python.exe" -m amp %*
set "AMP_EXIT=%ERRORLEVEL%"
popd
exit /b %AMP_EXIT%
