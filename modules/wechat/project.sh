#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "$0")"
action=${1:-}
if [[ $# -gt 0 ]]; then
    shift
fi

case "$action" in
    setup|start|test|import|mcp-config|doctor) ;;
    *)
        printf '%s\n' 'Usage: bash project.sh {setup [--test]|start [options]|test [options]|import <file>|mcp-config|doctor}'
        exit 2
        ;;
esac

environment=${CHANNELS_CONDA_ENV:-}
active_environment=${CONDA_DEFAULT_ENV:-}
if [[ -n "$environment" && "${environment,,}" != base ]]; then
    conda_target=(-n "$environment")
elif [[ -z "$environment" && -n "$active_environment" && "${active_environment,,}" != base && -n "${CONDA_PREFIX:-}" ]]; then
    conda_target=(-p "$CONDA_PREFIX")
else
    printf '%s\n' 'Activate your project Conda environment or set CHANNELS_CONDA_ENV to its name.' >&2
    exit 2
fi

conda_path=${CHANNELS_CONDA_EXE:-${CONDA_EXE:-}}
if [[ -n "$conda_path" ]]; then
    conda_path="$(cygpath -u "$conda_path")"
elif command -v conda >/dev/null 2>&1; then
    conda_path=conda
else
    printf '%s\n' 'Conda was not found. Initialize Conda for Git Bash or set CHANNELS_CONDA_EXE.' >&2
    exit 1
fi

run_python() {
    "$conda_path" run --no-capture-output "${conda_target[@]}" python "$@"
}

case "$action" in
    setup)
        if [[ $# -eq 0 ]]; then
            run_python -m pip install -r requirements.txt
        elif [[ $# -eq 1 && $1 == --test ]]; then
            run_python -m pip install -r requirements.txt -r tests/requirements.txt
        else
            printf '%s\n' 'Usage: bash project.sh setup [--test]' >&2
            exit 2
        fi
        ;;
    start) run_python -m channels.server "$@" ;;
    test) run_python -m pytest -q "$@" ;;
    import) run_python -m channels.import_data "$@" ;;
    mcp-config) run_python -m channels.mcp_server --codex-config ;;
    doctor)
        run_python -c 'import importlib.util, sys; packages = ("fastapi", "uvicorn", "mcp", "httpx", "pydantic", "win32gui", "comtypes", "psutil"); missing = [name for name in packages if importlib.util.find_spec(name) is None]; print(sys.executable); print(sys.version.split()[0]); print("Missing: " + ", ".join(missing) if missing else "Runtime dependencies found"); sys.exit(bool(missing))'
        ;;
esac
