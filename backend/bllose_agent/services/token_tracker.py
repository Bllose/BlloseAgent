"""Token usage tracking — per-agent and global statistics.

AgentTokenTracker: one per agent, tracks every turn's token usage.
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
            _encoder = None  # stays None — fall back to char heuristic
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


# ── data types ──────────────────────────────────────────────────


@dataclass
class TurnUsage:
    """A single conversation turn's token usage."""

    input_estimated: int
    output_actual: int
    timestamp: float = field(default_factory=time.time)


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

    def record(self, input_estimated: int, output_actual: int) -> None:
        """Record one conversation turn."""
        self._turns.append(TurnUsage(
            input_estimated=input_estimated,
            output_actual=output_actual,
        ))

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
