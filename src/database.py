import sqlite3
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple
from .logger import get_logger

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "household_tasks.db")


class Database:
    """SQLite database handler for storing task completions."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for task completions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    task_repeat INTEGER NOT NULL,
                    done_by TEXT NOT NULL,
                    done_when TEXT NOT NULL,
                    day_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(room_name, task_name, day_date)
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_day_date 
                ON task_completions(day_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_room_task 
                ON task_completions(room_name, task_name)
            """)
            
            conn.commit()
            get_logger(__name__).info(f"Database initialized at {self.db_path}")
    
    def save_task_completion(
        self, 
        room_name: str, 
        task_name: str, 
        task_repeat: int,
        done_by: str, 
        done_when: datetime, 
        day_date: date
    ) -> bool:
        """
        Save or update a task completion.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO task_completions 
                    (room_name, task_name, task_repeat, done_by, done_when, day_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    room_name,
                    task_name,
                    task_repeat,
                    done_by,
                    done_when.isoformat(),
                    day_date.isoformat()
                ))
                conn.commit()
                get_logger(__name__).debug(
                    f"Saved completion: {room_name}/{task_name} on {day_date} by {done_by}"
                )
                return True
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error saving completion: {e}")
            return False
    
    def delete_task_completion(
        self, 
        room_name: str, 
        task_name: str, 
        day_date: date
    ) -> bool:
        """
        Delete a task completion.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM task_completions 
                    WHERE room_name = ? AND task_name = ? AND day_date = ?
                """, (room_name, task_name, day_date.isoformat()))
                conn.commit()
                get_logger(__name__).debug(
                    f"Deleted completion: {room_name}/{task_name} on {day_date}"
                )
                return True
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error deleting completion: {e}")
            return False
    
    def get_task_completion(
        self, 
        room_name: str, 
        task_name: str, 
        day_date: date
    ) -> Optional[Dict[str, any]]:
        """
        Get a specific task completion.
        
        Returns:
            Dictionary with completion data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT room_name, task_name, task_repeat, done_by, done_when, day_date
                    FROM task_completions 
                    WHERE room_name = ? AND task_name = ? AND day_date = ?
                """, (room_name, task_name, day_date.isoformat()))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'room_name': row['room_name'],
                        'task_name': row['task_name'],
                        'task_repeat': row['task_repeat'],
                        'done_by': row['done_by'],
                        'done_when': datetime.fromisoformat(row['done_when']),
                        'day_date': date.fromisoformat(row['day_date'])
                    }
                return None
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error getting completion: {e}")
            return None
    
    def get_completions_for_date(self, day_date: date) -> List[Dict[str, any]]:
        """
        Get all task completions for a specific date.
        
        Returns:
            List of dictionaries with completion data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT room_name, task_name, task_repeat, done_by, done_when, day_date
                    FROM task_completions 
                    WHERE day_date = ?
                """, (day_date.isoformat(),))
                
                rows = cursor.fetchall()
                return [{
                    'room_name': row['room_name'],
                    'task_name': row['task_name'],
                    'task_repeat': row['task_repeat'],
                    'done_by': row['done_by'],
                    'done_when': datetime.fromisoformat(row['done_when']),
                    'day_date': date.fromisoformat(row['day_date'])
                } for row in rows]
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error getting completions for date: {e}")
            return []
    
    def get_completions_before_date(self, before_date: date, limit: int = 1000) -> List[Dict[str, any]]:
        """
        Get task completions before a specific date.
        
        Args:
            before_date: Get completions before this date
            limit: Maximum number of results
        
        Returns:
            List of dictionaries with completion data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT room_name, task_name, task_repeat, done_by, done_when, day_date
                    FROM task_completions 
                    WHERE day_date < ?
                    ORDER BY day_date DESC
                    LIMIT ?
                """, (before_date.isoformat(), limit))
                
                rows = cursor.fetchall()
                return [{
                    'room_name': row['room_name'],
                    'task_name': row['task_name'],
                    'task_repeat': row['task_repeat'],
                    'done_by': row['done_by'],
                    'done_when': datetime.fromisoformat(row['done_when']),
                    'day_date': date.fromisoformat(row['day_date'])
                } for row in rows]
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error getting completions before date: {e}")
            return []
    
    def get_last_completion(
        self, 
        room_name: str, 
        task_name: str, 
        before_date: Optional[date] = None
    ) -> Optional[Dict[str, any]]:
        """
        Get the most recent completion for a specific room/task combination.
        
        Args:
            room_name: Room name
            task_name: Task name
            before_date: Optional - only search before this date
        
        Returns:
            Dictionary with completion data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if before_date:
                    cursor.execute("""
                        SELECT room_name, task_name, task_repeat, done_by, done_when, day_date
                        FROM task_completions 
                        WHERE room_name = ? AND task_name = ? AND day_date <= ?
                        ORDER BY day_date DESC, done_when DESC
                        LIMIT 1
                    """, (room_name, task_name, before_date.isoformat()))
                else:
                    cursor.execute("""
                        SELECT room_name, task_name, task_repeat, done_by, done_when, day_date
                        FROM task_completions 
                        WHERE room_name = ? AND task_name = ?
                        ORDER BY day_date DESC, done_when DESC
                        LIMIT 1
                    """, (room_name, task_name))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'room_name': row['room_name'],
                        'task_name': row['task_name'],
                        'task_repeat': row['task_repeat'],
                        'done_by': row['done_by'],
                        'done_when': datetime.fromisoformat(row['done_when']),
                        'day_date': date.fromisoformat(row['day_date'])
                    }
                return None
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error getting last completion: {e}")
            return None
    
    def get_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """
        Get the earliest and latest dates in the database.
        
        Returns:
            Tuple of (earliest_date, latest_date) or (None, None) if empty
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MIN(day_date) as min_date, MAX(day_date) as max_date
                    FROM task_completions
                """)
                row = cursor.fetchone()
                if row and row[0]:
                    return (date.fromisoformat(row[0]), date.fromisoformat(row[1]))
                return (None, None)
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error getting date range: {e}")
            return (None, None)
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """
        Delete completions older than the specified number of days.
        
        Args:
            days_to_keep: Keep data from the last N days
        
        Returns:
            Number of rows deleted
        """
        try:
            cutoff_date = date.today()
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM task_completions 
                    WHERE day_date < ?
                """, (cutoff_date.isoformat(),))
                deleted = cursor.rowcount
                conn.commit()
                get_logger(__name__).info(f"Cleaned up {deleted} old completions")
                return deleted
        except sqlite3.Error as e:
            get_logger(__name__).error(f"Database error during cleanup: {e}")
            return 0
