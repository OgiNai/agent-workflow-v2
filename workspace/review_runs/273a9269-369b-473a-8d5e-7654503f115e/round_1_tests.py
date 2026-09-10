import pytest
from solution import normalize_user_data, process_user, process_admin

def test_normalize_user_data_normal():
    data = {'name': ' Alice ', 'email': 'BOB@Example.com'}
    expected = {'name': 'alice', 'email': 'bob@example.com'}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_missing_keys():
    data = {}
    expected = {'name': '', 'email': ''}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_non_string_types():
    data = {'name': 123, 'email': None}
    expected = {'name': '123', 'email': 'none'}
    assert normalize_user_data(data) == expected

def test_process_user():
    data = {'name': ' CHARLIE ', 'email': 'CHARLIE@TEST.COM'}
    assert process_user(data) == {'name': 'charlie', 'email': 'charlie@test.com'}

def test_process_admin():
    data = {'name': ' ADMIN ', 'email': 'ADMIN@SYSTEM.ORG'}
    assert process_admin(data) == {'name': 'admin', 'email': 'admin@system.org'}

def test_normalize_user_data_extra_keys_ignored():
    data = {'name': 'A', 'email': 'B', 'role': 'superuser'}
    result = normalize_user_data(data)
    assert 'role' not in result
    assert result == {'name': 'a', 'email': 'b'}