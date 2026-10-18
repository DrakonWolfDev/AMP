# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""One bounded folder traversal, retained while a decoder opens candidates."""

from dataclasses import dataclass, field

from .folder_navigator import NavigationStep


@dataclass
class NavigationAttempt:
    steps: list[NavigationStep]
    direction: int
    index: int = 0
    skipped: int = 0
    wrapped: bool = False
    attempted: set = field(default_factory=set)

    def next(self):
        while self.index < len(self.steps):
            step = self.steps[self.index]
            self.index += 1
            self.wrapped = self.wrapped or step.wrapped
            if step.path not in self.attempted:
                self.attempted.add(step.path)
                return step.path
        return None

    def message(self):
        parts = []
        if self.wrapped:
            boundary = "beginning" if self.direction > 0 else "end"
            parts.append(f"↻ Folder looped — back to the {boundary}")
        if self.skipped:
            parts.append(f"Skipped {self.skipped} unreadable file(s).")
        return " · ".join(parts)
