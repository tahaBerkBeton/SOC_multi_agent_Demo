import json, subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class StdioServerParameters:
    """How to launch the server executable."""
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class SimpleClient:
    """Synchronous client for a SimpleServer (spawned as a subprocess)."""

    def __init__(self, params: StdioServerParameters):
        self._params = params
        self._proc: subprocess.Popen | None = None

    # -------- context manager ----------------------------------------------
    def __enter__(self):
        self._proc = subprocess.Popen(
            [self._params.command, *self._params.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=self._params.env,
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._proc:
            self._proc.stdin.close()
            self._proc.terminate()
            self._proc.wait()

    # -------- private helper ------------------------------------------------
    def _roundtrip(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._proc.stdin.write(json.dumps(payload) + "\n")
        self._proc.stdin.flush()
        return json.loads(self._proc.stdout.readline())

    # -------- public API ----------------------------------------------------
    def list_tools(self) -> Dict[str, Any]:
        return self._roundtrip({"type": "list_tools"})

    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        return self._roundtrip({"type": "call_tool", "name": name, "args": args})
