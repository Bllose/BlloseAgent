import json
import subprocess
from pathlib import Path

from langchain_core.tools import tool

from bllose_agent.services.team_manager import BUS, TEAM, VALID_MSG_TYPES

WORKDIR = Path(__file__).resolve().parent.parent.parent  # backend/


def _safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


# ── File / System tools ──────────────────────────────────────────


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
    """Read the contents of a file. Returns file text or error."""
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


# ── Team management tools ────────────────────────────────────────


@tool
def list_teammates() -> str:
    """List all teammates with their name, role, and current (live) status.

    Use this to see who is idle (ready for work) vs working (busy).
    """
    return TEAM.list_all()


@tool
def send_message(to: str, content: str, msg_type: str = "task_assignment") -> str:
    """Send a message or task to a teammate's inbox.

    Use msg_type='task_assignment' to give work to a teammate.
    Use msg_type='message' for casual / follow-up communication.
    The teammate will pick it up from their inbox and process it.

    Args:
        to: The teammate's name (e.g. 'coding_leader', 'paper_leader').
        content: The task description or message body.
        msg_type: 'task_assignment' (default), 'message', 'broadcast',
            'shutdown_request', 'shutdown_response', 'status_report'.
    """
    return BUS.send("bllose", to, content, msg_type)


@tool
def read_inbox() -> str:
    """Read and drain bllose's own inbox. Returns messages as JSON.

    Check this to see replies and status reports from teammates
    and from self_agent.
    """
    msgs = BUS.read_inbox("bllose")
    return json.dumps(msgs, indent=2) if msgs else "(inbox empty)"


@tool
def broadcast(content: str) -> str:
    """Send a broadcast message to all teammates at once."""
    return BUS.broadcast("bllose", content, TEAM.member_names())


@tool
def request_expert(role: str, task: str) -> str:
    """Request an expert agent from self_agent.

    self_agent will ensure the expert is running and assign the task.
    Use this instead of spawning experts directly — self_agent manages
    the full agent lifecycle and keeps config.json in sync.

    Args:
        role: Expert role — 'coding_leader' or 'paper_leader'.
        task: The task description — what you need the expert to do.
    """
    payload = json.dumps({
        "action": "request_expert",
        "role": role,
        "task": task,
    })
    return BUS.send("bllose", "self_agent", payload, "task_assignment")


# ── Tool collection ──────────────────────────────────────────────

TOOLS = [
    bash,
    read_file,
    write_file,
    edit_file,
    list_teammates,
    send_message,
    read_inbox,
    broadcast,
    request_expert,
]
