import sqlite3
from typing import Optional, Any

def find_user(connection: sqlite3.Connection, username: str) -> Optional[Any]:
    """Retrieves a user record from the database safely using parameterized queries."""
    query = "SELECT * FROM users WHERE username = ?"
    cursor = connection.execute(query, (username,))
    return cursor.fetchone()