import pytest
from solution import normalize_user_data, process_user, process_admin

def test_normalize_user_data_basic():
    data = {'name': ' Alice ', 'email': 'BOB@Example.com'}
    expected = {'name': 'alice', 'email': 'bob@example.com'}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_missing_keys():
    data = {}
    expected = {'name': '', 'email': ''}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_non_string_values():
    data = {'name': 123, 'email': None}
    expected = {'name': '123', 'email': 'none'}
    assert normalize_user_data(data) == expected

def test_process_user():
    user = {'name': '  John  ', 'email': 'JOHN@DOE.COM'}
    assert process_user(user) == {'name': 'john', 'email': 'john@doe.com'}

def test_process_admin():
    admin = {'name': ' ADMIN ', 'email': 'ADMIN@SYSTEM.ORG'}
    assert process_admin(admin) == {'name': 'admin', 'email': 'admin@system.org'}

def test_normalize_user_data_extra_keys():
    data = {'name': 'A', 'email': 'B', 'role': 'admin'}
    result = normalize_user_data(data)
    assert 'role' not in result
    assert result == {'name': 'a', 'email': 'b'}