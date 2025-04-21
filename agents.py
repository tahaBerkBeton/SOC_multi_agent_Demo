# agents.py

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from openai import OpenAI
from my_mcp.client import SimpleClient, StdioServerParameters


@dataclass
class Tool:
    """
    Holds metadata for a tool exposed by an MCP server.
    """
    name: str
    description: str
    inputSchema: Dict[str, Any]


class Workspace:
    """
    Simple file‑based workspace for an agent.
    Always overwrites its contents on initialization.
    """

    def __init__(self, agent_name: str, initial_data: Optional[str] = None):
        self.workspace_dir = "workspaces"
        self.workspace_path = os.path.join(
            self.workspace_dir, f"{agent_name}_workspace.txt"
        )
        self._ensure_workspace(initial_data)

    def _ensure_workspace(self, initial_data: Optional[str]):
        # Create directory if needed
        os.makedirs(self.workspace_dir, exist_ok=True)
        # Always overwrite existing file with the default structure
        content = f"""<workspace>
  <data>
{initial_data or ''}
  </data>
  <logs>
    {{
      "entries": []
    }}
  </logs>
</workspace>"""
        with open(self.workspace_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_content(self) -> str:
        """
        Return the raw contents of the workspace file.
        """
        if os.path.exists(self.workspace_path):
            with open(self.workspace_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""


class Agent:
    """
    LLM‑powered agent that communicates with a dedicated MCP server
    for its tool implementations.
    """

    def __init__(
        self,
        *,
        name: str,
        instructions: str,
        model: str,
        mcp_server: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace: bool = False,
        workdata: Optional[str] = None,
        handoffs: Optional[List["Agent"]] = None,
    ):
        # Basic agent properties
        self.name = name
        self.instructions = instructions
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.handoffs = handoffs or []

        # Start the MCP subprocess and fetch tool metadata
        params = StdioServerParameters(command="python", args=[mcp_server])
        self._mcp_client_ctx = SimpleClient(params)
        self._mcp_client = self._mcp_client_ctx.__enter__()
        tools_meta = self._mcp_client.list_tools()["tools"]
        self.tools: List[Tool] = [
            Tool(name=t["name"], description=t.get("description", ""), inputSchema=t["inputSchema"])
            for t in tools_meta
        ]

        # Optionally initialize a fresh workspace
        self.workspace_enabled = workspace
        self.workspace = Workspace(name, workdata) if workspace else None

    def RunTool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Invoke a tool on the MCP server and return its result.
        Raises RuntimeError on tool errors.
        """
        resp = self._mcp_client.call_tool(tool_name, arguments)
        if resp.get("isError"):
            raise RuntimeError(f"Tool '{tool_name}' failed: {resp.get('error')}")
        return resp.get("content")

    def handoff(self, target_agent_name: str):
        """
        Switch to another agent in the allowed handoff list.
        Raises ValueError if the target is not permitted.
        """
        if target_agent_name == self.name:
            raise ValueError(f"Cannot hand off to self ({self.name})")
        for agent in self.handoffs:
            if agent.name == target_agent_name:
                return agent
        allowed = ", ".join(a.name for a in self.handoffs)
        raise ValueError(f"Handoff to '{target_agent_name}' not allowed. Allowed: {allowed}")

    def _create_client(self) -> OpenAI:
        """
        Construct an OpenAI API client using the configured base_url and api_key.
        """
        kwargs: Dict[str, Any] = {}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.api_key:
            kwargs["api_key"] = self.api_key
        return OpenAI(**kwargs)

    def _build_system_prompt(self) -> str:
        """
        Generate the system prompt including tool descriptions and workspace.
        """
        tools_block = ""
        for t in self.tools:
            tools_block += (
                f"Tool: {t.name}\n"
                f"Description: {t.description}\n"
                f"Parameters: {json.dumps(t.inputSchema, indent=2)}\n\n"
            )
        prompt = (
            f"You are {self.name} agent.\n\n"
            f"{self.instructions}\n\n"
            f"Available tools:\n{tools_block}"
            "To call a tool, reply with exactly:\n"
            "<tool_call>{\"name\":\"tool_name\",\"arguments\":{...}}</tool_call>\n"
        )
        if self.handoffs:
            names = ", ".join(a.name for a in self.handoffs)
            prompt += (
                f"\nYou may hand off to: {names}. "
                "Include <handoff>AgentName</handoff> to do so.\n"
            )
        if self.workspace_enabled and self.workspace:
            prompt += f"\n\nWorkspace snapshot:\n{self.workspace.get_content()}\n"
        return prompt

    def __del__(self):
        """
        Cleanup MCP subprocess and remove workspace file if it was used.
        """
        try:
            self._mcp_client_ctx.__exit__(None, None, None)
        except Exception:
            pass
        if self.workspace_enabled and self.workspace:
            try:
                os.remove(self.workspace.workspace_path)
            except Exception:
                pass


class Runner:
    """
    Static helper methods to drive synchronous or streamed LLM calls.
    """

    @staticmethod
    def run(agent: "Agent", convo: List[Dict[str, str]]):
        client = agent._create_client()
        msgs = [{"role": "system", "content": agent._build_system_prompt()}] + convo
        resp = client.chat.completions.create(model=agent.model, messages=msgs)
        return resp.choices[0].message

    @staticmethod
    def run_streamed(agent: "Agent", convo: List[Dict[str, str]]):
        client = agent._create_client()
        msgs = [{"role": "system", "content": agent._build_system_prompt()}] + convo
        return client.chat.completions.create(model=agent.model, messages=msgs, stream=True)
