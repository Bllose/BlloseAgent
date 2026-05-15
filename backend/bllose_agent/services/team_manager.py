import json
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

WORKDIR = Path(__file__).resolve().parent.parent.parent  # backend/
TEAM_DIR = WORKDIR / ".team"
INBOX_DIR = TEAM_DIR / "inbox"

VALID_MSG_TYPES = {
    "message",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "task_assignment",
    "status_report",
}

if TYPE_CHECKING:
    from bllose_agent.agent.self_agent import SelfAgent


# ── SelfAgent registry ──────────────────────────────────────────

_self_agent: "SelfAgent | None" = None


def get_self_agent() -> "SelfAgent":
    """Return the running SelfAgent singleton.

    Raises AssertionError if SelfAgent hasn't been started yet.
    """
    assert _self_agent is not None, "SelfAgent has not been started"
    return _self_agent


def set_self_agent(sa: "SelfAgent") -> None:
    """Set the global SelfAgent singleton (called once at startup)."""
    global _self_agent
    _self_agent = sa


# ── Message bus (JSONL inboxes) ─────────────────────────────────

class MessageBus:
    """JSONL inbox per teammate — append-only send, drain-on-read."""

    def __init__(self, inbox_dir: Path):
        self.dir = inbox_dir
        self.dir.mkdir(parents=True, exist_ok=True)

    def send(self, sender: str, to: str, content: str,
             msg_type: str = "message", extra: dict | None = None) -> str:
        if msg_type not in VALID_MSG_TYPES:
            return f"Error: Invalid type '{msg_type}'. Valid: {VALID_MSG_TYPES}"
        msg = {
            "type": msg_type,
            "from": sender,
            "content": content,
            "timestamp": time.time(),
        }
        if extra:
            msg.update(extra)
        inbox_path = self.dir / f"{to}.jsonl"
        with open(inbox_path, "a") as f:
            f.write(json.dumps(msg) + "\n")
        return f"Sent {msg_type} to {to}"

    def read_inbox(self, name: str) -> list[dict]:
        inbox_path = self.dir / f"{name}.jsonl"
        if not inbox_path.exists():
            return []
        messages = []
        for line in inbox_path.read_text().strip().splitlines():
            if line:
                messages.append(json.loads(line))
        inbox_path.write_text("")
        return messages

    def broadcast(self, sender: str, content: str, teammates: list[str]) -> str:
        count = 0
        for name in teammates:
            if name != sender:
                self.send(sender, name, content, "broadcast")
                count += 1
        return f"Broadcast to {count} teammates"


BUS = MessageBus(INBOX_DIR)


# ── Teammate registry (persisted to config.json) ────────────────

class TeammateManager:
    """Persistent teammate registry backed by .team/config.json.

    Each teammate can be spawned as a background thread running its own
    LangGraph agent loop.  The config.json status is kept in sync with
    the real agent state (idle / working / shutdown).
    """

    def __init__(self, team_dir: Path):
        self.dir = team_dir
        self.dir.mkdir(exist_ok=True)
        self.config_path = self.dir / "config.json"
        self.config = self._load_config()
        self.threads: dict[str, threading.Thread] = {}
        self._shutdown_flags: dict[str, threading.Event] = {}

    def _load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {"team_name": "default", "members": []}

    def _save_config(self):
        self.config_path.write_text(json.dumps(self.config, indent=2))

    def _find_member(self, name: str) -> dict | None:
        for m in self.config["members"]:
            if m["name"] == name:
                return m
        return None

    def register(self, name: str, role: str) -> str:
        """Register a new teammate (idle) if not already present."""
        member = self._find_member(name)
        if member:
            return f"'{name}' already registered (status: {member['status']})"
        self.config["members"].append({
            "name": name,
            "role": role,
            "status": "idle",
            "status_updated_at": time.time(),
        })
        self._save_config()
        return f"Registered '{name}' (role: {role})"

    def set_status(self, name: str, status: str) -> str:
        member = self._find_member(name)
        if not member:
            return f"Error: '{name}' not found"
        member["status"] = status
        member["status_updated_at"] = time.time()
        self._save_config()
        return f"'{name}' status → {status}"

    def list_all(self) -> str:
        if not self.config["members"]:
            return "No teammates."
        lines = [f"Team: {self.config['team_name']}"]
        for m in self.config["members"]:
            lines.append(f"  {m['name']} ({m['role']}): {m['status']}")
        return "\n".join(lines)

    def member_names(self) -> list[str]:
        return [m["name"] for m in self.config["members"]]

    def get_status(self, name: str) -> str:
        member = self._find_member(name)
        return member["status"] if member else "unknown"

    # ── Thread-backed spawn / shutdown ───────────────────────────

    def spawn(self, name: str, role: str) -> str:
        """Launch a teammate as a background thread running its own agent loop.

        The teammate polls its inbox in a loop.  Status updates to config.json
        happen inside the agent loop so they reflect real state.
        """
        from bllose_agent.agent.teammate import teammate_agent_loop

        member = self._find_member(name)
        if not member:
            self.register(name, role)

        if name in self.threads and self.threads[name].is_alive():
            return f"'{name}' is already running (status: {member['status']})"

        def _run_in_thread():
            import asyncio
            asyncio.run(teammate_agent_loop(name, role))

        thread = threading.Thread(target=_run_in_thread, name=name, daemon=True)
        self.threads[name] = thread
        thread.start()
        return f"Spawned '{name}' (role: {role}) — agent thread running"

    def shutdown(self, name: str) -> str:
        """Send shutdown_request to a teammate and wait for its thread to exit."""
        if name not in self.threads or not self.threads[name].is_alive():
            return f"'{name}' is not running"
        BUS.send("system", name, "shutdown", "shutdown_request")
        self.threads[name].join(timeout=30)
        if self.threads[name].is_alive():
            return f"'{name}' did not shut down within 30s"
        return f"'{name}' shut down"

    def shutdown_all(self) -> str:
        results = []
        for name in list(self.threads.keys()):
            results.append(self.shutdown(name))
        return "\n".join(results)


TEAM = TeammateManager(TEAM_DIR)
