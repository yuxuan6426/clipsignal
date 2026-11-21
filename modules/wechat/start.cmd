@echo off
setlocal
cd /d "%~dp0"
call "%~dp0conda-python.cmd" -m channels.server %*
exit /b %ERRORLEVEL%
