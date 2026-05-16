"""Token usage tracking — per-agent and global statistics.

AgentTokenTracker: one per agent, tracks every turn's token usage
plus the input/output content and full graph message snapshots.
GlobalTokenTracker: owned by SelfAgent, aggregates across all agents.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import tiktoken


# ── token counting utility ──────────────────────────────────────

_encoder: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding | None:
    global _encoder
    if _encoder is None:
        try:
            _encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoder = None
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens in a string. Falls back to len/4 if tiktoken fails."""
    enc = _get_encoder()
    if enc is not None:
        return len(enc.encode(text))
    return max(1, len(text) // 4)


def estimate_input_tokens(messages: list) -> int:
    """Estimate token count for a list of LangChain messages."""
    total = 0
    for msg in messages:
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text") or block.get("thinking") or ""
                    total += count_tokens(str(text))
    return total


# ── message serialization ───────────────────────────────────────

def serialize_message(msg) -> dict:
    """Convert a LangChain message to a JSON-safe dict snapshot."""
    d: dict = {"type": getattr(msg, "type", "unknown")}

    content = getattr(msg, "content", "")
    if isinstance(content, str):
        d["content"] = content
    elif isinstance(content, list):
        d["content_blocks"] = []
        for block in content:
            if isinstance(block, dict):
                d["content_blocks"].append(block)
    else:
        d["content"] = str(content)

    # Tool calls (AIMessage)
    tc = getattr(msg, "tool_calls", None)
    if tc:
        d["tool_calls"] = []
        for c in tc:
            if isinstance(c, dict):
                d["tool_calls"].append({
                    "name": c.get("name", ""),
                    "args": c.get("args", {}),
                    "id": c.get("id", ""),
                })

    # Tool message fields
    if hasattr(msg, "name"):
        d["name"] = msg.name
    if hasattr(msg, "tool_call_id"):
        d["tool_call_id"] = msg.tool_call_id

    # Usage metadata (AIMessage)
    um = getattr(msg, "usage_metadata", None)
    if um:
        d["usage_metadata"] = dict(um)

    return d


def serialize_messages(messages: list) -> list[dict]:
    """Convert a list of LangChain messages to JSON-safe dicts."""
    return [serialize_message(m) for m in messages]


# ── data types ──────────────────────────────────────────────────


@dataclass
class TurnUsage:
    """A single conversation turn's token usage with content snapshots."""

    input_estimated: int
    output_actual: int
    input_text: str = ""
    output_text: str = ""
    graph_messages: list[dict] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "input_estimated": self.input_estimated,
            "output_actual": self.output_actual,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "graph_messages": self.graph_messages,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentTokenStats:
    """Snapshot of an agent's token usage (serialisable for API)."""

    agent_name: str
    total_input: int
    total_output: int
    total_tokens: int
    max_input: int
    turn_count: int


# ── per-agent tracker ───────────────────────────────────────────


class AgentTokenTracker:
    """Tracks token usage for a single agent across multiple turns."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self._turns: list[TurnUsage] = []

    # ── public API ───────────────────────────────────────────

    def estimate(self, messages: list) -> int:
        """Estimate input tokens for a list of messages (pre-call)."""
        return estimate_input_tokens(messages)

    def record(
        self,
        input_estimated: int,
        output_actual: int,
        input_text: str = "",
        output_text: str = "",
        graph_messages: list[dict] | None = None,
    ) -> None:
        """Record one conversation turn with content snapshots and graph trace."""
        self._turns.append(TurnUsage(
            input_estimated=input_estimated,
            output_actual=output_actual,
            input_text=input_text,
            output_text=output_text,
            graph_messages=graph_messages or [],
        ))

    @property
    def turns(self) -> list[dict]:
        """Return all recorded turns as dictionaries (for API)."""
        return [t.to_dict() for t in self._turns]

    @property
    def stats(self) -> AgentTokenStats:
        total_in = sum(t.input_estimated for t in self._turns)
        total_out = sum(t.output_actual for t in self._turns)
        max_in = max((t.input_estimated for t in self._turns), default=0)
        return AgentTokenStats(
            agent_name=self.agent_name,
            total_input=total_in,
            total_output=total_out,
            total_tokens=total_in + total_out,
            max_input=max_in,
            turn_count=len(self._turns),
        )

    @property
    def turn_count(self) -> int:
        return len(self._turns)


# ── global tracker ──────────────────────────────────────────────


class GlobalTokenTracker:
    """Aggregates token usage across all agents.  Owned by SelfAgent."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentTokenTracker] = {}

    def agent(self, name: str) -> AgentTokenTracker:
        """Get (or create) the tracker for a named agent."""
        if name not in self._agents:
            self._agents[name] = AgentTokenTracker(name)
        return self._agents[name]

    @property
    def all_stats(self) -> list[AgentTokenStats]:
        """Return stats for every agent that has recorded usage."""
        return [t.stats for t in self._agents.values() if t.turn_count > 0]

    @property
    def total_input(self) -> int:
        return sum(s.total_input for s in self.all_stats)

    @property
    def total_output(self) -> int:
        return sum(s.total_output for s in self.all_stats)

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output

    @property
    def max_input(self) -> int:
        return max((s.max_input for s in self.all_stats), default=0)

    @property
    def agent_count(self) -> int:
        return len(self._agents)
