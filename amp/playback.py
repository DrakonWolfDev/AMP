# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Transport calculations independent of the GUI and decoder."""

from math import isfinite


def seek_target(seconds, mode, position, duration):
    if duration is None or not isfinite(duration) or duration <= 0:
        return None
    if not isfinite(seconds):
        return None
    target = seconds + (position or 0) if mode == "relative" else seconds
    return max(0, min(duration, target))
