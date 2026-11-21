@echo off
setlocal
cd /d "%~dp0"
call "%~dp0conda-python.cmd" -m pip install -r requirements.txt %*
exit /b %ERRORLEVEL%
