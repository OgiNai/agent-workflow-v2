import pytest
from solution import normalize_user_data, process_user, process_admin

def test_normalize_user_data_basic():
    data = {'name': ' John Doe ', 'email': 'JOHN@EXAMPLE.COM'}
    expected = {'name': 'john doe', 'email': 'john@example.com'}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_missing_keys():
    data = {}
    expected = {'name': '', 'email': ''}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_non_string_values():
    data = {'name': 123, 'email': None}
    expected = {'name': '123', 'email': 'none'}
    assert normalize_user_data(data) == expected

def test_process_user_integration():
    user = {'name': ' Alice ', 'email': 'ALICE@TEST.ORG'}
    assert process_user(user) == {'name': 'alice', 'email': 'alice@test.org'}

def test_process_admin_integration():
    admin = {'name': ' BOB ', 'email': 'BOB@ADMIN.COM'}
    assert process_admin(admin) == {'name': 'bob', 'email': 'bob@admin.com'}

def test_normalize_user_data_whitespace_only():
    data = {'name': '   ', 'email': '\t\n'}
    expected = {'name': '', 'email': ''}
    assert normalize_user_data(data) == expected