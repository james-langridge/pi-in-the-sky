"""Server log viewing routes."""

import logging
from flask import Blueprint, jsonify, request
from log_handler import get_memory_handler

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/api/logs')
def get_logs():
    """
    Get recent server log entries.

    Query params:
        limit: Maximum entries to return (default 100, max 500)

    Returns:
        JSON array of log entries with timestamp, level, name, message
    """
    handler = get_memory_handler()
    if not handler:
        return jsonify({
            'status': 'error',
            'message': 'Log handler not initialized'
        }), 500

    limit = request.args.get('limit', 100, type=int)
    limit = min(limit, 500)  # Cap at buffer size

    entries = handler.get_entries(limit=limit)

    return jsonify({
        'status': 'ok',
        'count': len(entries),
        'entries': entries
    })
