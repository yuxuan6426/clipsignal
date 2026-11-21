@echo off
setlocal
cd /d "%~dp0"
set "CHANNELS_CONDA_SELECTOR=-n"
set "CHANNELS_CONDA_TARGET=%CHANNELS_CONDA_ENV%"
if not defined CHANNELS_CONDA_TARGET (
    if not defined CONDA_DEFAULT_ENV goto environment_required
    if /i "%CONDA_DEFAULT_ENV%"=="base" goto environment_required
    if not defined CONDA_PREFIX goto environment_required
    set "CHANNELS_CONDA_SELECTOR=-p"
    set "CHANNELS_CONDA_TARGET=%CONDA_PREFIX%"
)
if /i "%CHANNELS_CONDA_TARGET%"=="base" goto environment_required
if defined CHANNELS_CONDA_EXE (
    set "CHANNELS_CONDA_COMMAND=%CHANNELS_CONDA_EXE%"
) else if defined CONDA_EXE (
    set "CHANNELS_CONDA_COMMAND=%CONDA_EXE%"
) else (
    set "CHANNELS_CONDA_COMMAND=conda"
)
call "%CHANNELS_CONDA_COMMAND%" run --no-capture-output %CHANNELS_CONDA_SELECTOR% "%CHANNELS_CONDA_TARGET%" python %*
exit /b %ERRORLEVEL%

:environment_required
echo Activate your project Conda environment or set CHANNELS_CONDA_ENV to its name. 1>&2
exit /b 2
