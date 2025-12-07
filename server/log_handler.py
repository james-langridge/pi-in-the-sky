"""In-memory log handler for serving logs via API."""

import logging
from collections import deque
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LogEntry:
    """Immutable log entry."""
    timestamp: str
    level: str
    name: str
    message: str


class MemoryLogHandler(logging.Handler):
    """
    Log handler that stores entries in a ring buffer.

    Uses collections.deque for O(1) append and automatic size limiting.
    """

    def __init__(self, max_entries: int = 500):
        super().__init__()
        self._buffer: deque = deque(maxlen=max_entries)

    def emit(self, record: logging.LogRecord) -> None:
        """Store formatted log record in buffer."""
        entry = LogEntry(
            timestamp=self.formatter.formatTime(record) if self.formatter else record.asctime,
            level=record.levelname,
            name=record.name,
            message=record.getMessage()
        )
        self._buffer.append(entry)

    def get_entries(self, limit: int = 100) -> List[dict]:
        """
        Get recent log entries as dicts.

        Args:
            limit: Maximum number of entries to return (most recent)

        Returns:
            List of log entry dicts, newest last
        """
        entries = list(self._buffer)
        if limit and len(entries) > limit:
            entries = entries[-limit:]
        return [
            {
                'timestamp': e.timestamp,
                'level': e.level,
                'name': e.name,
                'message': e.message
            }
            for e in entries
        ]

    def clear(self) -> None:
        """Clear all stored log entries."""
        self._buffer.clear()


# Global handler instance for access from routes
_memory_handler: MemoryLogHandler | None = None


def setup_memory_handler(max_entries: int = 500) -> MemoryLogHandler:
    """
    Set up and return the global memory log handler.

    Should be called once during application startup.
    """
    global _memory_handler
    _memory_handler = MemoryLogHandler(max_entries=max_entries)
    _memory_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Add to root logger to capture all logs
    root_logger = logging.getLogger()
    root_logger.addHandler(_memory_handler)

    return _memory_handler


def get_memory_handler() -> MemoryLogHandler | None:
    """Get the global memory handler instance."""
    return _memory_handler
