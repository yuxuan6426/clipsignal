import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class StatusProtocol(unittest.TestCase):
    def test_thread_isolation_and_bounded_public_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "tools" / "status.py"
            script.parent.mkdir()
            shutil.copyfile(Path(__file__).parents[1] / "tools" / "status.py", script)
            states = root / ".local" / "runs"
            states.mkdir(parents=True)
            (states / "workspace.json").write_text('{"state":"ready","module":"edit"}')
            (states / "a.json").write_text('{"module":"leads","phase":"verify","state":"passed","note":"private"}')
            listed = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            requests = [listed]
            for number, thread in enumerate(["a", "b", "../a"], 2):
                requests.append({"jsonrpc": "2.0", "id": number, "method": "resources/read",
                                 "params": {"uri": "ui://clipsignal/status", "_meta": {
                                     "com.openai/codex-statusline-state": {"thread": {"id": thread}}
                                 }}})
            process = subprocess.run([sys.executable, str(script)], input="\n".join(map(json.dumps, requests)),
                                     text=True, capture_output=True, check=True, timeout=4)
            result = [json.loads(line)["result"] for line in process.stdout.splitlines()]
            entrypoints = result[0]["tools"][0]["_meta"]["openai/ui"]["entrypoints"]
            self.assertEqual(entrypoints, [{"type": "statusline", "resourceUri": "ui://clipsignal/status"}])
            values = [json.loads(value["contents"][0]["text"])["children"] for value in result[1:]]
            self.assertEqual(values[0], ["ClipSignal", "leads", "verify", "passed"])
            self.assertEqual(values[1], ["ClipSignal", "ready"])
            self.assertEqual(values[2], values[1])
