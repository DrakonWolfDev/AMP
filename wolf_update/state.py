"""Minimal state contract for update checks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateState:
    last_successful_check: str | None = None
    dismissed_version: str | None = None


class MemoryStateStore:
    def __init__(self, state: UpdateState | None = None) -> None:
        self.state = state or UpdateState()

    def load(self) -> UpdateState:
        return self.state

    def save(self, state: UpdateState) -> None:
        self.state = state
