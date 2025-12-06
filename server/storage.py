"""Storage layer for push subscriptions using SQLite."""

import sqlite3
import json
import logging
import uuid
from typing import List, Optional, Dict
from contextlib import contextmanager
from datetime import datetime, timedelta

from models import PushSubscription

logger = logging.getLogger(__name__)


class SubscriptionStorage:
    """Manages push subscription persistence in SQLite."""
    
    def __init__(self, db_path: str = "subscriptions.db"):
        """
        Initialize storage with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id TEXT PRIMARY KEY,
                    endpoint TEXT NOT NULL UNIQUE,
                    p256dh TEXT NOT NULL,
                    auth TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    user_agent TEXT
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def add_subscription(self, endpoint: str, p256dh: str, auth: str, 
                        user_agent: Optional[str] = None) -> PushSubscription:
        """
        Add or update a push subscription.
        
        Args:
            endpoint: Push service endpoint URL
            p256dh: Public key for payload encryption
            auth: Authentication secret
            user_agent: Browser user agent string
            
        Returns:
            Created or updated PushSubscription
        """
        subscription_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if endpoint already exists
            cursor.execute(
                "SELECT id FROM push_subscriptions WHERE endpoint = ?",
                (endpoint,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing subscription
                subscription_id = existing[0]
                cursor.execute("""
                    UPDATE push_subscriptions 
                    SET p256dh = ?, auth = ?, user_agent = ?
                    WHERE id = ?
                """, (p256dh, auth, user_agent, subscription_id))
                logger.info(f"Updated subscription {subscription_id}")
            else:
                # Insert new subscription
                cursor.execute("""
                    INSERT INTO push_subscriptions 
                    (id, endpoint, p256dh, auth, created_at, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (subscription_id, endpoint, p256dh, auth, created_at, user_agent))
                logger.info(f"Added new subscription {subscription_id}")
            
            conn.commit()
        
        return PushSubscription(
            id=subscription_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            created_at=created_at,
            user_agent=user_agent
        )
    
    def remove_subscription(self, endpoint: str) -> bool:
        """
        Remove a push subscription by endpoint.
        
        Args:
            endpoint: Push service endpoint URL
            
        Returns:
            True if subscription was removed, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM push_subscriptions WHERE endpoint = ?",
                (endpoint,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Removed subscription with endpoint: {endpoint}")
                return True
            else:
                logger.warning(f"No subscription found with endpoint: {endpoint}")
                return False
    
    def get_all_subscriptions(self) -> List[PushSubscription]:
        """
        Retrieve all active push subscriptions.
        
        Returns:
            List of PushSubscription objects
        """
        subscriptions = []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, endpoint, p256dh, auth, created_at, user_agent
                FROM push_subscriptions
                ORDER BY created_at DESC
            """)
            
            for row in cursor.fetchall():
                subscription = PushSubscription(
                    id=row[0],
                    endpoint=row[1],
                    p256dh=row[2],
                    auth=row[3],
                    created_at=row[4],
                    user_agent=row[5]
                )
                subscriptions.append(subscription)
        
        logger.info(f"Retrieved {len(subscriptions)} subscriptions")
        return subscriptions
    
    def get_subscription_by_endpoint(self, endpoint: str) -> Optional[PushSubscription]:
        """
        Get a specific subscription by endpoint.
        
        Args:
            endpoint: Push service endpoint URL
            
        Returns:
            PushSubscription if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, endpoint, p256dh, auth, created_at, user_agent
                FROM push_subscriptions
                WHERE endpoint = ?
            """, (endpoint,))
            
            row = cursor.fetchone()
            if row:
                return PushSubscription(
                    id=row[0],
                    endpoint=row[1],
                    p256dh=row[2],
                    auth=row[3],
                    created_at=row[4],
                    user_agent=row[5]
                )
        
        return None
    
    def cleanup_old_subscriptions(self, days: int = 90) -> int:
        """
        Remove subscriptions older than specified days.
        
        Args:
            days: Number of days to keep subscriptions
            
        Returns:
            Number of subscriptions removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM push_subscriptions WHERE created_at < ?",
                (cutoff_str,)
            )
            conn.commit()
            
            removed_count = cursor.rowcount
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old subscriptions")
            
            return removed_count