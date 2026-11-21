"""Codex statusline provider. Reads only bounded, workspace-local progress."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".local" / "runs"
URI = "ui://clipsignal/status"
TOOL = {
    "name": "statusline",
    "title": "ClipSignal",
    "description": "Show the current ClipSignal workflow stage.",
    "inputSchema": {"type": "object", "properties": {}},
    "_meta": {"openai/ui": {"entrypoints": [{"type": "statusline", "resourceUri": URI}]}},
}
ALLOWED = {
    "module": {"setup", "media", "edit", "leads", "wechat", "publish", "outreach", "repair", "memory"},
    "phase": {"prepare", "run", "verify", "done"},
    "state": {"ready", "working", "passed", "needs-auth", "blocked"},
    "pending": {"setup", "auth", "receipt", "review"},
}


def render(snapshot):
    thread = snapshot.get("thread", {})
    thread_id = thread.get("id")
    files = [STATE / "workspace.json"]
    if isinstance(thread_id, str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", thread_id):
        files.insert(0, STATE / f"{thread_id}.json")
    for file in files:
        try:
            with file.open("rb") as stream:
                data = json.loads(stream.read(4096))
            if not isinstance(data, dict):
                continue
            fields = ("state",) if file.name == "workspace.json" else ALLOWED
            values = [data.get(key) for key in fields]
            labels = [value for key, value in zip(fields, values)
                      if isinstance(value, str) and value in ALLOWED[key]]
            if labels:
                return {"type": "row", "props": {"gap": 1}, "children": ["ClipSignal", *labels]}
        except (OSError, ValueError):
            continue
    return "ClipSignal"


def respond(method, params):
    resource = {"uri": URI, "name": "ClipSignal status", "mimeType": "application/json"}
    if method == "initialize":
        return {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "clipsignal-status", "version": "1.0.0"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call" and params.get("name") == TOOL["name"]:
        return {"content": [{"type": "text", "text": URI}]}
    if method == "resources/list":
        return {"resources": [resource]}
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read" and params.get("uri") == URI:
        snapshot = params.get("_meta", {}).get("com.openai/codex-statusline-state", {})
        return {"contents": [{**resource, "text": json.dumps(render(snapshot))}]}
    raise ValueError("Unknown method or resource")


for line in sys.stdin.buffer:
    request = {}
    try:
        request = json.loads(line)
        if "id" not in request:
            continue
        reply = {"result": respond(request["method"], request.get("params", {}))}
    except (ValueError, KeyError, TypeError, AttributeError):
        reply = {"error": {"code": -32602, "message": "Invalid request"}}
    print(json.dumps({"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                      **reply}), flush=True)
