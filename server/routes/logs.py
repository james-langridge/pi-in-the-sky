"""Server log viewing routes."""

import logging
import os
import re
from flask import Blueprint, jsonify, request
from log_handler import get_memory_handler

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'server.log')
LOG_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\S+) - (\w+) - (.*)$')


def parse_log_file(limit: int) -> list[dict]:
    """Read and parse the last N entries from the log file."""
    if not os.path.exists(LOG_FILE):
        return []

    entries = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            match = LOG_PATTERN.match(line.strip())
            if match:
                entries.append({
                    'timestamp': match.group(1),
                    'name': match.group(2),
                    'level': match.group(3),
                    'message': match.group(4)
                })

    return entries[-limit:] if limit else entries


@logs_bp.route('/api/logs')
def get_logs():
    """
    Get recent server log entries.

    Query params:
        source: 'memory' (default) or 'file'
        limit: Maximum entries to return (default 100, max 500)

    Returns:
        JSON array of log entries with timestamp, level, name, message
    """
    source = request.args.get('source', 'memory')
    limit = request.args.get('limit', 100, type=int)
    limit = min(limit, 500)

    if source == 'file':
        entries = parse_log_file(limit)
    else:
        handler = get_memory_handler()
        if not handler:
            return jsonify({
                'status': 'error',
                'message': 'Log handler not initialized'
            }), 500
        entries = handler.get_entries(limit=limit)

    return jsonify({
        'status': 'ok',
        'source': source,
        'count': len(entries),
        'entries': entries
    })
