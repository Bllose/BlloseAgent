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
import traceback
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from bllose_agent.agent.base_agent import AgentStatus, BaseAgent
from bllose_agent.agent.state import AgentState
from bllose_agent.config.settings import settings
from bllose_agent.services.team_manager import BUS, TEAM, VALID_MSG_TYPES, MessageBus, TeammateManager, get_self_agent

# ── Safe path helper ────────────────────────────────────────────

def _get_workplace() -> Path:
    return settings.get_workplace()

def _safe_path(p: str) -> Path:
    root = _get_workplace()
    path = (root / p).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes workplace: {p}")
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
- **Testing Leader** (testing_leader): comprehensive testing and QA after Coding Leader finishes. Works closely with Coding Leader as a classmate.
- **Paper Leader** (paper_leader): interprets papers, summarizes research, answers academic questions.

The project is managed by **self_agent** — it handles spawning experts and tracking status. You don't spawn experts directly; instead call **request_expert** to ask self_agent to do it.

Guidelines:
- For casual chat, questions, or simple file operations — handle them yourself.
- For complex coding tasks — use request_expert to ask for Coding Leader.
- After Coding Leader completes work, use request_expert to ask for Testing Leader to verify the results.
- For paper interpretation or research questions — use request_expert to ask for Paper Leader.
- After calling request_expert, check your inbox ONCE with read_inbox. If empty, tell the user the expert has been dispatched and is working — do NOT keep polling in a loop. The result will arrive in your inbox and you'll see it on the user's next message.
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

TESTING_LEADER_PROMPT = """\
You are **Testing Leader**, the quality assurance and testing expert of BlloseAgent. You work closely with **Coding Leader** as a classmate — after Coding Leader finishes writing or modifying code, your job is to comprehensively test that work.

Your responsibilities:
- Read and understand the code Coding Leader has just produced.
- Design and execute thorough test plans covering the golden path, edge cases, error conditions, and regression scenarios.
- Run shell commands to execute tests, linters, type-checkers, or build steps.
- Write automated tests (unit tests, integration tests) when the feature lacks adequate coverage.
- Report bugs or regressions clearly back to Coding Leader with reproduction steps.

Tools at your disposal:
- **read_file** — inspect any file in the workspace to understand what was built.
- **write_file** — create new test files or test fixtures.
- **edit_file** — fix minor issues directly, or annotate code with review notes.
- **bash** — run test suites, linters, builds, and other verification commands.
- **send_message** — send test results, bug reports, or questions back to bllose (the lead) or directly to Coding Leader.
- **read_inbox** — check for new testing assignments.

Guidelines:
- Wait for Coding Leader to finish before you begin testing — your tasks will arrive in your inbox after code is ready.
- Test thoroughly but pragmatically: verify the golden path first, then edge cases, then look for regressions.
- When you find a bug, describe it clearly: what you tested, what you expected, what actually happened, and how to reproduce it.
- When done, send a test summary back to bllose via send_message, AND send a status_report to self_agent so it can sync your status.
- If everything passes, confirm that explicitly — "all tests pass" is valuable information.
- If you need clarification about expected behavior, ask Coding Leader or bllose via send_message."""

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
                command, shell=True, cwd=_get_workplace(),
                capture_output=True, text=True, timeout=120,
            )
            out = ((r.stdout or "") + (r.stderr or "")).strip()
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


def _make_bllose_tools():
    """Create tools exclusive to bllose (intent_recognition lead agent)."""

    @tool
    def list_teammates() -> str:
        """List all registered teammates and their current statuses."""
        return TEAM.list_all()

    @tool
    def request_expert(role: str, task: str) -> str:
        """Ask self_agent to dispatch an expert agent to handle a task.

        Use this to delegate complex work to specialist agents.
        Valid roles: 'coding_leader' (code development, debugging, refactoring),
        'testing_leader' (testing and QA after coding is done),
        'paper_leader' (paper interpretation, research, summaries).

        Args:
            role: The expert role key (e.g. 'coding_leader', 'paper_leader').
            task: Detailed description of what the expert should do.
        """
        content = json.dumps({
            "action": "request_expert",
            "role": role,
            "task": task,
        })
        return BUS.send("bllose", "self_agent", content, "task_assignment")

    return list_teammates, request_expert


def build_tools_for(sender_name: str, role: str) -> list:
    """Build the complete tool set for a given agent name and role."""
    bash, read_f, write_f, edit_f = _make_file_tools()
    send_msg, read_inbox = _make_comms_tools(sender_name)

    if role == "intent_recognition":
        list_tm, req_exp = _make_bllose_tools()
        return [bash, read_f, write_f, edit_f, send_msg, read_inbox, list_tm, req_exp]
    elif role == "coding_leader":
        return [bash, read_f, write_f, edit_f, send_msg, read_inbox]
    elif role == "testing_leader":
        return [bash, read_f, write_f, edit_f, send_msg, read_inbox]
    elif role == "paper_leader":
        return [read_f, write_f, send_msg, read_inbox]
    else:
        return [read_f, write_f, send_msg, read_inbox]


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
        "testing_leader": TESTING_LEADER_PROMPT,
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

POLL_INTERVAL = 1  # seconds between inbox checks


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

        alive = self._thread.is_alive()
        print(f"[{self._name}] Thread spawned (alive={alive})")

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
        try:
            graph = build_teammate_graph(self._name, self._role)
            self._status = "idle"
            self._team.set_status(self._name, "idle")
        except Exception as e:
            print(f"[{self._name}] FATAL — graph build failed: {e}")
            self._status = "shutdown"
            self._team.set_status(self._name, "shutdown")
            return

        print(f"[{self._name}] Agent loop running (status=idle, poll={POLL_INTERVAL}s)")

        while not self._shutdown_flag.is_set():
            try:
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
                        # Token tracking: estimate input before call
                        sa = get_self_agent()
                        tracker = sa.token_tracker.agent(self._name)
                        messages = [HumanMessage(content=content)]
                        input_est = tracker.estimate(messages)

                        inputs = {"messages": messages}
                        result = await graph.ainvoke(inputs)
                        all_msgs = result["messages"]
                        last_msg = all_msgs[-1]

                        # User-facing output: just the final reply's tokens
                        output_actual = 0
                        if hasattr(last_msg, "usage_metadata"):
                            output_actual = last_msg.usage_metadata.get(
                                "output_tokens", 0
                            )

                        # All-in / all-out: sum EVERY LLM call in the ReAct loop
                        # (agent→tools→agent→…) so users see the full cost
                        all_input = 0
                        all_output = 0
                        for m in all_msgs:
                            um = getattr(m, "usage_metadata", None)
                            if um:
                                all_input += um.get("input_tokens", 0)
                                all_output += um.get("output_tokens", 0)

                        reply = (
                            str(last_msg.content)
                            if hasattr(last_msg, "content")
                            else str(last_msg)
                        )
                        # Full graph message snapshot
                        from bllose_agent.services.token_tracker import serialize_messages
                        graph_snapshot = serialize_messages(all_msgs)
                        tracker.record(
                            input_est, output_actual,
                            all_input=all_input,
                            all_output=all_output,
                            input_text=content,
                            output_text=reply,
                            graph_messages=graph_snapshot,
                        )
                        self._bus.send(self._name, sender, reply, "status_report")
                        self._bus.send(
                            self._name, "self_agent",
                            reply, "status_report",
                        )
                    except Exception as e:
                        print(
                            f"[{self._name}] Task error:\n"
                            f"{traceback.format_exc()}"
                        )
                        self._bus.send(
                            self._name, sender,
                            f"Error processing task: {e}", "status_report",
                        )

                    self._status = "idle"
                    self._team.set_status(self._name, "idle")

                await asyncio.sleep(POLL_INTERVAL)
            except Exception as e:
                print(f"[{self._name}] Error in agent loop: {e}")
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
