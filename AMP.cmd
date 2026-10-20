@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run the setup steps in README.md first.
  popd
  exit /b 1
)
".venv\Scripts\python.exe" -m amp %*
set "AMP_EXIT=%ERRORLEVEL%"
popd
exit /b %AMP_EXIT%
