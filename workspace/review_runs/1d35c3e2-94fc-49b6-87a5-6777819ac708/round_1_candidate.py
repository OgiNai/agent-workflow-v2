import sqlite3
from typing import Optional, Any, Tuple

def find_user(connection: sqlite3.Connection, username: str) -> Optional[Tuple[Any, ...]]:
    """
    Retrieves a user record from the database using a parameterized query to prevent SQL injection.
    """
    query = "SELECT * FROM users WHERE username = ?"
    cursor = connection.execute(query, (username,))
    return cursor.fetchone()