@echo off
setlocal
cd /d "%~dp0"
call "%~dp0conda-python.cmd" -m pytest -q %*
exit /b %ERRORLEVEL%
