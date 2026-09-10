import sqlite3
from typing import Optional, Any, Tuple

def find_user(connection: sqlite3.Connection, username: str) -> Optional[Tuple[Any, ...]]:
    """Finds a user by username using a parameterized query to prevent SQL injection."""
    query = "SELECT * FROM users WHERE username = ?"
    cursor = connection.execute(query, (username,))
    return cursor.fetchone()