"""SelfAgent — top-level agent cluster manager.

SelfAgent IS the project itself.  Its lifecycle spans the entire
application.  It owns the message bus, team registry, and all sub-agents.

Startup order:
  1. SelfAgent registers itself in config.json
  2. SelfAgent starts bllose (intent recognition + chat agent)
  3. SelfAgent starts default expert agents (Coding Leader, Paper Leader)
  4. SelfAgent starts its inbox-polling loop to receive requests
  5. SelfAgent syncs all statuses to config.json

Communication uses the inbox pattern (JSONL files):
  - bllose → self_agent inbox: request_expert messages
  - expert → self_agent inbox: status_report / feedback
  - self_agent → bllose inbox: forwarded expert results
"""

import asyncio
import json
import threading
import time
from pathlib import Path

from bllose_agent.agent.base_agent import AgentStatus, BaseAgent
from bllose_agent.services.team_manager import (
    BUS,
    TEAM,
    MessageBus,
    TeammateManager,
)

WORKDIR = Path(__file__).resolve().parent.parent.parent  # backend/
TEAM_DIR = WORKDIR / ".team"
INBOX_DIR = TEAM_DIR / "inbox"
POLL_INTERVAL = 2  # seconds


class SelfAgent:
    """Top-level manager for the entire agent cluster.

    SelfAgent = the project.  It starts first, stops last, and owns
    everything in between (bus, team registry, sub-agents, status sync).
    """

    def __init__(self, team_dir: Path = TEAM_DIR):
        self._team_dir = team_dir
        self.bus: MessageBus = BUS
        self.team: TeammateManager = TEAM
        self._agents: dict[str, BaseAgent] = {}
        self._poll_thread: threading.Thread | None = None
        self._shutdown_flag = threading.Event()

    # ── Lifecycle ───────────────────────────────────────────────

    def start(self) -> str:
        """Start SelfAgent and all default sub-agents.

        Returns a summary of what was started.
        """
        lines: list[str] = []

        # 1. Register self_agent
        self.team.register("self_agent", "self_agent")
        self.team.set_status("self_agent", "starting")
        lines.append("self_agent registered")

        # 2. Start bllose agent (intent recognition + chat)
        from bllose_agent.agent.teammate import BlloseAgent

        bllose = BlloseAgent(self.bus, self.team)
        bllose.start()
        self._agents["bllose"] = bllose
        lines.append("bllose agent started")

        # 3. Start default expert agents
        from bllose_agent.agent.teammate import TeammateAgent

        for name, role in [
            ("Coding Leader", "coding_leader"),
            ("Paper Leader", "paper_leader"),
        ]:
            agent = TeammateAgent(name, role, self.bus, self.team)
            agent.start()
            self._agents[name] = agent
            lines.append(f"{name} ({role}) started")

        # 4. Start inbox-polling thread
        self._poll_thread = threading.Thread(
            target=self._run_poll_loop,
            name="self_agent_poll",
            daemon=True,
        )
        self._poll_thread.start()
        lines.append("self_agent inbox polling started")

        # 5. Final status sync
        self.team.set_status("self_agent", "idle")
        self.sync_status()
        lines.append("status synced to config.json")

        return "\n".join(lines)

    def stop(self) -> str:
        """Stop all sub-agents and self_agent gracefully."""
        lines: list[str] = []
        self._shutdown_flag.set()

        for name, agent in self._agents.items():
            try:
                agent.stop()
                lines.append(f"{name} stopped")
            except Exception as e:
                lines.append(f"{name} stop error: {e}")

        self.team.set_status("self_agent", "shutdown")
        self.sync_status()
        lines.append("self_agent shutdown complete")
        return "\n".join(lines)

    # ── Polling loop (runs in background thread) ────────────────

    def _run_poll_loop(self) -> None:
        """Poll self_agent's inbox for requests from sub-agents."""
        while not self._shutdown_flag.is_set():
            try:
                msgs = self.bus.read_inbox("self_agent")
                for msg in msgs:
                    self._dispatch(msg)
            except Exception:
                pass  # Don't crash the poll loop on transient errors
            time.sleep(POLL_INTERVAL)

    def _dispatch(self, msg: dict) -> None:
        """Route an inbox message to the appropriate handler."""
        msg_type = msg.get("type", "message")
        sender = msg.get("from", "unknown")
        content = msg.get("content", "")

        if msg_type in ("task_assignment", "message"):
            self._handle_sub_agent_request(sender, content)
        elif msg_type == "status_report":
            self.receive_feedback(sender, content)

    # ── Handling sub-agent requests ─────────────────────────────

    def _handle_sub_agent_request(self, sender: str, content: str) -> None:
        """Parse and act on a request from a sub-agent.

        Recognized actions (JSON-encoded in content):
          - {"action": "request_expert", "role": "...", "task": "..."}
        """
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return  # Not JSON — ignore (could be a plain message)

        action = data.get("action", "")
        if action == "request_expert":
            self._handle_expert_request(
                role=data.get("role", ""),
                task=data.get("task", ""),
                requester=sender,
            )

    def _handle_expert_request(
        self, role: str, task: str, requester: str
    ) -> None:
        """Ensure the expert is running, then forward the task."""
        # Map role to agent name
        role_name_map = {
            "coding_leader": "Coding Leader",
            "paper_leader": "Paper Leader",
        }
        expert_name = role_name_map.get(role, role)

        # If expert isn't registered yet, spawn it dynamically
        if expert_name not in self._agents:
            from bllose_agent.agent.teammate import TeammateAgent

            agent = TeammateAgent(expert_name, role, self.bus, self.team)
            agent.start()
            self._agents[expert_name] = agent

        # Forward the task to the expert's inbox
        self.bus.send("self_agent", expert_name, task, "task_assignment")
        self.team.set_status(expert_name, "working")
        self.sync_status()

    # ── Interface: receive feedback from expert agents ──────────

    def receive_feedback(self, from_agent: str, content: str) -> None:
        """Receive feedback/result from an expert and forward to bllose.

        This is the interface SelfAgent exposes to sub-agents for
        reporting results.  Experts send status_report messages to
        self_agent's inbox; this method forwards them to bllose.
        """
        self.bus.send("self_agent", "bllose", content, "status_report")
        self.team.set_status(from_agent, "idle")
        self.sync_status()

    # ── Interface: query sub-agent status ───────────────────────

    def get_agent_status(self, name: str) -> AgentStatus:
        """Query any sub-agent's live status via the unified interface.

        Called by monitoring tools or API handlers that need to know
        which agents are idle / working / shutdown.
        """
        agent = self._agents.get(name)
        if agent:
            return agent.get_status()
        return AgentStatus(name=name, role="unknown", status="unknown")

    def list_agent_statuses(self) -> list[AgentStatus]:
        """Return live status snapshots for all registered sub-agents."""
        return [agent.get_status() for agent in self._agents.values()]

    # ── Status sync ─────────────────────────────────────────────

    def sync_status(self) -> None:
        """Push every sub-agent's current status to config.json.

        Called after any state change so the persisted config always
        reflects the live agent cluster.
        """
        for name, agent in self._agents.items():
            status = agent.get_status()
            self.team.set_status(name, status.status)

    def get_agent(self, name: str) -> BaseAgent | None:
        """Return a sub-agent by name, or None if not found.

        Callers use this to get a direct reference to a sub-agent
        (e.g. to update its status during request processing).
        """
        return self._agents.get(name)

    # ── Accessors ───────────────────────────────────────────────

    @property
    def agent_names(self) -> list[str]:
        return list(self._agents.keys())

    def has_agent(self, name: str) -> bool:
        return name in self._agents
