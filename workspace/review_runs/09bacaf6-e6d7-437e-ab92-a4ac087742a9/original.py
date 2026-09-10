import sqlite3


def find_user(connection, username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return connection.execute(query).fetchone()
