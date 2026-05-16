"""Base agent interface — all sub-agents expose this unified interface to SelfAgent.

SelfAgent calls these methods to query status, manage lifecycle, and
coordinate the agent cluster.  Every sub-agent (bllose, coding_leader,
paper_leader, and any future expert) must implement this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentStatus:
    """Live status snapshot for a sub-agent."""

    name: str
    role: str
    status: str  # "starting" | "idle" | "working" | "shutdown" | "error"
    details: str = ""


class BaseAgent(ABC):
    """Unified interface that every sub-agent exposes to SelfAgent.

    SelfAgent uses this interface to:
    - Query each sub-agent's running status at any time
    - Start / stop sub-agents
    - Manage the full agent lifecycle
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent name (e.g. 'bllose', 'coding_leader')."""
        ...

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role key (e.g. 'intent_recognition', 'coding_leader')."""
        ...

    @abstractmethod
    def get_status(self) -> AgentStatus:
        """Return a live snapshot of this agent's current state.

        SelfAgent calls this whenever it needs to sync status to config.json
        or display the team dashboard.
        """
        ...

    @abstractmethod
    def start(self) -> None:
        """Start this agent (register, spawn threads if needed, set idle)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop this agent gracefully (signal threads, set shutdown)."""
        ...
