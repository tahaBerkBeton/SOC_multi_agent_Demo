import inspect, json, sys
from typing import Any, Callable, Dict

# Very small mapping from Python → JSON‑Schema scalar types
_PY_TO_JSON = {int: "number", float: "number", str: "string", bool: "boolean"}


class _Tool:
    """Internal helper that stores metadata and executes the function."""
    def __init__(self, fn: Callable[..., Any]):
        self.fn = fn
        self.name = fn.__name__
        self.description = (fn.__doc__ or "").strip()

        sig = inspect.signature(fn)
        props, required = {}, []
        for p in sig.parameters.values():
            if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
                props[p.name] = {
                    "title": p.name.capitalize(),
                    "type": _PY_TO_JSON.get(p.annotation, "string"),
                }
                required.append(p.name)

        self.input_schema = {
            "title": f"{self.name}Arguments",
            "type": "object",
            "properties": props,
            "required": required,
        }

    def call(self, args: Dict[str, Any]):
        return self.fn(**args)


class SimpleServer:
    """Drop‑in‑simple MCP‑style server (blocking, STDIO JSON protocol)."""

    def __init__(self, name: str = "SimpleServer"):
        self.name = name
        self._tools: Dict[str, _Tool] = {}

    # Decorator factory ------------------------------------------------------
    def tool(self):
        def _register(fn):
            self._tools[fn.__name__] = _Tool(fn)
            return fn
        return _register

    # ------------------------------------------------------------------------
    def _handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if request.get("type") == "list_tools":
            return {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.input_schema,
                    }
                    for t in self._tools.values()
                ]
            }

        if request.get("type") == "call_tool":
            name, args = request["name"], request.get("args", {})
            tool = self._tools.get(name)
            if not tool:
                return {"error": f"Tool '{name}' not found", "isError": True}
            try:
                return {"content": tool.call(args), "isError": False}
            except Exception as exc:
                return {"error": str(exc), "isError": True}

        return {"error": "Unknown request", "isError": True}

    # ------------------------------------------------------------------------
    def run(self):
        """Blocks on STDIN, writes one JSON line per response."""
        for line in sys.stdin:
            if not line.strip():
                continue
            response = self._handle(json.loads(line))
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
