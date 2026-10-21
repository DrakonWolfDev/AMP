# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Resolve explicitly dropped SMB files through the user's KDE session."""

import sys
from pathlib import PurePosixPath

from PySide6.QtCore import QObject, Signal


class NetworkDropResolver(QObject):
    resolved = Signal(str)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending = set()
        self._generation = 0

    def cancel(self):
        # Ignore older replies when the user drops a different file.
        self._generation += 1

    def resolve(self, url):
        self.cancel()
        generation = self._generation
        if not sys.platform.startswith("linux") or url.scheme().lower() != "smb":
            self.failed.emit("This network address is not supported. Open a mounted file instead.")
            return
        try:
            from PySide6.QtDBus import (
                QDBusConnection,
                QDBusMessage,
                QDBusPendingCallWatcher,
            )
        except ImportError:
            self.failed.emit("Network drops need Qt D-Bus support and KDE kio-fuse.")
            return

        message = QDBusMessage.createMethodCall(
            "org.kde.KIOFuse", "/org/kde/KIOFuse", "org.kde.KIOFuse.VFS", "mountUrl"
        )
        # Keep escaping intact; credentials are handled by KDE, never logged by AMP.
        message.setArguments([bytes(url.toEncoded()).decode("ascii")])
        watcher = QDBusPendingCallWatcher(
            QDBusConnection.sessionBus().asyncCall(message, 30000), self
        )
        self._pending.add(watcher)
        watcher.finished.connect(lambda call: self._finished(call, generation))

    def _finished(self, watcher, generation):
        from PySide6.QtDBus import QDBusMessage

        self._pending.discard(watcher)
        reply = watcher.reply()
        watcher.deleteLater()
        if generation != self._generation:
            return
        arguments = reply.arguments()
        if (
            reply.type() == QDBusMessage.MessageType.ReplyMessage
            and len(arguments) == 1
            and isinstance(arguments[0], str)
            and PurePosixPath(arguments[0]).is_absolute()
        ):
            self.resolved.emit(arguments[0])
        else:
            # D-Bus errors may contain credentials or paths; do not display them.
            self.failed.emit(
                "Could not open the network file. Check the share in Dolphin and that "
                "KDE kio-fuse is installed, or open a mounted file instead."
            )
