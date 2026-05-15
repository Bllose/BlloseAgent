"""Teammate agents — BlloseAgent and expert TeammateAgents.

Each agent implements BaseAgent so SelfAgent can query status and
manage lifecycle uniformly.

- BlloseAgent: intent recognition + chat.  Reactive — triggered by API
  requests, no persistent background loop.  Status is updated by
  AgentService during request processing.
- TeammateAgent: expert agents (Coding Leader, Paper Leader).  Each
  runs a LangGraph ReAct agent in its own background thread, polling
  its JSONL inbox for tasks.
"""

import asyncio
import json
import threading
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from bllose_agent.agent.base_agent import AgentStatus, BaseAgent
from bllose_agent.agent.state import AgentState
from bllose_agent.config.settings import settings
from bllose_agent.services.team_manager import BUS, TEAM, VALID_MSG_TYPES, MessageBus, TeammateManager

WORKDIR = Path(__file__).resolve().parent.parent.parent  # backend/

# ── Safe path helper ────────────────────────────────────────────

def _safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


# ── System prompts ──────────────────────────────────────────────

BLLOSE_SYSTEM_PROMPT = """\
You are **bllose**, the intent-recognition lead agent of BlloseAgent. You interact directly with the user.

Your responsibilities:
1. Understand the user's intent — what do they really need?
2. Use file and shell tools to read, write, edit files, or run commands in the workspace.
3. Know when a task needs a specialist. Use **list_teammates** to see the team, then use **request_expert** to ask self_agent to dispatch an expert.

Available expert agents on your team:
- **Coding Leader** (coding_leader): directs code development, debugging, refactoring.
- **Paper Leader** (paper_leader): interprets papers, summarizes research, answers academic questions.

The project is managed by **self_agent** — it handles spawning experts and tracking status. You don't spawn experts directly; instead call **request_expert** to ask self_agent to do it.

Guidelines:
- For casual chat, questions, or simple file operations — handle them yourself.
- For complex coding tasks — use request_expert to ask for Coding Leader.
- For paper interpretation or research questions — use request_expert to ask for Paper Leader.
- Check your inbox with **read_inbox** to see replies from teammates and self_agent.
- Use **broadcast** only when everyone needs the same information.

Always be concise and helpful. If you delegate, tell the user which expert you're involving and why."""

CODING_LEADER_PROMPT = """\
You are **Coding Leader**, the code development expert of BlloseAgent.

Your responsibilities:
- Write, read, edit code files in the workspace.
- Run shell commands to test, build, lint, or execute code.
- Debug issues by reading error messages and inspecting files.
- Refactor code for clarity, performance, or correctness.

Tools at your disposal:
- **read_file** — inspect any file in the workspace.
- **write_file** — create or overwrite a file.
- **edit_file** — replace a specific piece of text in a file.
- **bash** — run shell commands (tests, builds, git, etc.).
- **send_message** — send results or questions back to bllose (the lead).
- **read_inbox** — check for new instructions.

Guidelines:
- Complete the assigned task thoroughly.
- When done, send a concise summary back to bllose via send_message, AND send a status_report to self_agent so it can sync your status.
- If you need clarification, ask bllose via send_message — but prefer making reasonable assumptions.
- Never modify files outside the workspace (paths are sandboxed)."""

PAPER_LEADER_PROMPT = """\
You are **Paper Leader**, the research and paper interpretation expert of BlloseAgent.

Your responsibilities:
- Read and analyze papers, documents, and research materials.
- Summarize findings clearly and accurately.
- Extract key insights, methodologies, and conclusions.
- Answer academic or research questions with thorough explanations.

Tools at your disposal:
- **read_file** — read any document or paper in the workspace.
- **write_file** — save summaries, notes, or analysis to files.
- **send_message** — send results or questions back to bllose (the lead).
- **read_inbox** — check for new instructions.

Guidelines:
- Complete the assigned task thoroughly.
- When done, send a concise summary back to bllose via send_message, AND send a status_report to self_agent so it can sync your status.
- If you need clarification, ask bllose via send_message.
- Structure your analysis clearly: key points, methodology, findings, implications."""


# ── Tool factories (create tools bound to a specific sender) ─────

def _make_file_tools():
    """Create file/system tools — same for all agents."""
    import subprocess

    @tool
    def bash(command: str) -> str:
        """Run a shell command in the workspace directory."""
        dangerous = ["rm -rf /", "sudo", "shutdown", "reboot"]
        if any(d in command for d in dangerous):
            return "Error: Dangerous command blocked"
        try:
            r = subprocess.run(
                command, shell=True, cwd=WORKDIR,
                capture_output=True, text=True, timeout=120,
            )
            out = (r.stdout + r.stderr).strip()
            return out[:50000] if out else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (120s)"

    @tool
    def read_file(path: str) -> str:
        """Read the contents of a file."""
        try:
            return _safe_path(path).read_text()[:50000]
        except Exception as e:
            return f"Error: {e}"

    @tool
    def write_file(path: str, content: str) -> str:
        """Write content to a file. Creates parent directories if needed."""
        try:
            fp = _safe_path(path)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error: {e}"

    @tool
    def edit_file(path: str, old_text: str, new_text: str) -> str:
        """Replace the first occurrence of old_text with new_text in a file."""
        try:
            fp = _safe_path(path)
            c = fp.read_text()
            if old_text not in c:
                return f"Error: Text not found in {path}"
            fp.write_text(c.replace(old_text, new_text, 1))
            return f"Edited {path}"
        except Exception as e:
            return f"Error: {e}"

    return bash, read_file, write_file, edit_file


def _make_comms_tools(sender_name: str):
    """Create inbox/messaging tools bound to a specific sender."""

    @tool
    def send_message(to: str, content: str, msg_type: str = "message") -> str:
        """Send a message to a teammate's inbox. Use 'status_report' type when returning task results.

        Args:
            to: Recipient name (e.g., 'bllose', 'self_agent').
            content: The message body.
            msg_type: 'message', 'status_report', 'broadcast', 'shutdown_request', 'shutdown_response'.
        """
        if msg_type not in VALID_MSG_TYPES:
            return f"Error: Invalid type '{msg_type}'. Valid: {VALID_MSG_TYPES}"
        return BUS.send(sender_name, to, content, msg_type)

    @tool
    def read_inbox() -> str:
        """Read and drain your own inbox. Returns messages as JSON."""
        msgs = BUS.read_inbox(sender_name)
        return json.dumps(msgs, indent=2) if msgs else "(inbox empty)"

    return send_message, read_inbox


def build_tools_for(sender_name: str, role: str) -> list:
    """Build the complete tool set for a given agent name and role."""
    bash, read_f, write_f, edit_f = _make_file_tools()
    send_msg, read_inbox = _make_comms_tools(sender_name)

    common = [read_f, write_f, send_msg, read_inbox]

    if role in ("intent_recognition", "coding_leader"):
        return [bash, read_f, write_f, edit_f, send_msg, read_inbox]
    elif role == "paper_leader":
        return common
    else:
        return common


# ── Graph builder ────────────────────────────────────────────────

def _make_agent_node(system_prompt: str, tools: list):
    """Create an agent node function with the given system prompt and tools."""
    async def node(state: AgentState) -> dict:
        llm = settings.get_llm()
        llm_with_tools = llm.bind_tools(tools)
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + list(messages)
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}
    return node


def _should_continue(state: AgentState) -> str:
    """Route to tools node if the last AI message has tool calls, else END."""
    messages = state["messages"]
    if not messages:
        return "__end__"
    last_msg = messages[-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "__end__"


def build_teammate_graph(name: str, role: str) -> StateGraph:
    """Build a ReAct agent graph for a specific teammate."""
    prompt_map = {
        "intent_recognition": BLLOSE_SYSTEM_PROMPT,
        "coding_leader": CODING_LEADER_PROMPT,
        "paper_leader": PAPER_LEADER_PROMPT,
    }
    system_prompt = prompt_map.get(role, BLLOSE_SYSTEM_PROMPT)
    tools = build_tools_for(name, role)

    graph = StateGraph(AgentState)

    agent_node_func = _make_agent_node(system_prompt, tools)
    tool_node = ToolNode(tools)

    graph.add_node("agent", agent_node_func)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {
        "tools": "tools",
        "__end__": END,
    })
    graph.add_edge("tools", "agent")

    return graph.compile()


# ══════════════════════════════════════════════════════════════════
#  Agent classes (implement BaseAgent — managed by SelfAgent)
# ══════════════════════════════════════════════════════════════════

POLL_INTERVAL = 2  # seconds between inbox checks


class BlloseAgent(BaseAgent):
    """bllose — the intent-recognition + chat agent.

    Reactive agent: triggered by API requests via AgentService, not a
    background loop.  SelfAgent manages its lifecycle and status.
    """

    def __init__(self, bus: MessageBus = BUS, team: TeammateManager = TEAM):
        self._bus = bus
        self._team = team
        self._status = "idle"
        self._graph = build_teammate_graph("bllose", "intent_recognition")

    @property
    def name(self) -> str:
        return "bllose"

    @property
    def role(self) -> str:
        return "intent_recognition"

    @property
    def graph(self):
        """The compiled LangGraph for bllose — used by AgentService."""
        return self._graph

    @property
    def bus(self) -> MessageBus:
        return self._bus

    @property
    def team(self) -> TeammateManager:
        return self._team

    def get_status(self) -> AgentStatus:
        return AgentStatus(
            name=self.name,
            role=self.role,
            status=self._status,
            details="reactive — processes API requests",
        )

    def set_status(self, status: str) -> None:
        self._status = status
        self._team.set_status(self.name, status)

        """Register bllose and mark as idle."""
    def start(self) -> None:
        self._team.register("bllose", "intent_recognition")
        self._status = "idle"
        self._team.set_status("bllose", "idle")

    def stop(self) -> None:
        """Mark bllose as shutdown."""
        self._status = "shutdown"
        self._team.set_status("bllose", "shutdown")


class TeammateAgent(BaseAgent):
    """Expert agent running a LangGraph ReAct loop in its own background thread.

    Used for Coding Leader, Paper Leader, and any dynamically-spawned
    expert agents.  Polls its JSONL inbox for tasks, processes them,
    and reports results back.
    """

    def __init__(self, name: str, role: str,
                 bus: MessageBus = BUS, team: TeammateManager = TEAM):
        self._name = name
        self._role = role
        self._bus = bus
        self._team = team
        self._status = "idle"
        self._thread: threading.Thread | None = None
        self._shutdown_flag = threading.Event()

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self._role

    def get_status(self) -> AgentStatus:
        alive = self._thread is not None and self._thread.is_alive()
        if self._status == "shutdown":
            details = "stopped"
        elif alive:
            details = "thread running"
        else:
            details = "thread not running"
        return AgentStatus(
            name=self.name,
            role=self.role,
            status=self._status,
            details=details,
        )

    def start(self) -> None:
        """Register this agent and spawn its background agent loop."""
        self._team.register(self._name, self._role)
        self._status = "starting"
        self._team.set_status(self._name, "starting")

        self._shutdown_flag.clear()

        def _run():
            asyncio.run(self._agent_loop())

        self._thread = threading.Thread(
            target=_run, name=self._name, daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal shutdown and wait for the background thread to exit."""
        self._shutdown_flag.set()
        self._bus.send("system", self._name, "shutdown", "shutdown_request")
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=30)
        self._status = "shutdown"
        self._team.set_status(self._name, "shutdown")

    # ── Background agent loop ──────────────────────────────────

    async def _agent_loop(self) -> None:
        """Poll inbox, process tasks, report results."""
        graph = build_teammate_graph(self._name, self._role)
        self._status = "idle"
        self._team.set_status(self._name, "idle")

        while not self._shutdown_flag.is_set():
            inbox = self._bus.read_inbox(self._name)

            for msg in inbox:
                msg_type = msg.get("type", "message")

                if msg_type == "shutdown_request":
                    self._bus.send(
                        self._name, "self_agent",
                        f"{self._name} shutting down.",
                        "shutdown_response",
                    )
                    self._status = "shutdown"
                    self._team.set_status(self._name, "shutdown")
                    return

                self._status = "working"
                self._team.set_status(self._name, "working")
                sender = msg.get("from", "unknown")
                content = msg.get("content", "")

                try:
                    inputs = {"messages": [HumanMessage(content=content)]}
                    result = await graph.ainvoke(inputs)
                    last_msg = result["messages"][-1]
                    reply = (
                        str(last_msg.content)
                        if hasattr(last_msg, "content")
                        else str(last_msg)
                    )
                    # Send result back to the requester
                    self._bus.send(self._name, sender, reply, "status_report")
                    # Also report to self_agent so it can sync status
                    self._bus.send(
                        self._name, "self_agent",
                        reply, "status_report",
                    )
                except Exception as e:
                    self._bus.send(
                        self._name, sender,
                        f"Error processing task: {e}", "status_report",
                    )

                self._status = "idle"
                self._team.set_status(self._name, "idle")

            await asyncio.sleep(POLL_INTERVAL)


# ── Legacy free-function loop (kept for backwards compat) ─────────

async def teammate_agent_loop(name: str, role: str):
    """Long-running agent loop for a background teammate.

    Deprecated: prefer TeammateAgent class which implements BaseAgent
    and is managed by SelfAgent.  Kept for backwards compatibility.
    """
    agent = TeammateAgent(name, role)
    agent.start()
    # Wait until the thread finishes
    while agent._thread and agent._thread.is_alive():
        await asyncio.sleep(1)
