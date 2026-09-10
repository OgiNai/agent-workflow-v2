import pytest
from solution import normalize_user_data, process_user, process_admin

def test_normalize_user_data_standard():
    data = {'name': ' Alice ', 'email': 'ALICE@Example.com'}
    expected = {'name': 'alice', 'email': 'alice@example.com'}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_missing_keys():
    data = {}
    expected = {'name': '', 'email': ''}
    assert normalize_user_data(data) == expected

def test_normalize_user_data_non_string_types():
    data = {'name': 123, 'email': None}
    expected = {'name': '123', 'email': 'none'}
    assert normalize_user_data(data) == expected

def test_process_user_behavior():
    user = {'name': ' BOB ', 'email': 'BOB@Test.com'}
    assert process_user(user) == {'name': 'bob', 'email': 'bob@test.com'}

def test_process_admin_behavior():
    admin = {'name': ' ADMIN ', 'email': 'ADMIN@System.org'}
    assert process_admin(admin) == {'name': 'admin', 'email': 'admin@system.org'}

def test_normalize_user_data_whitespace_only():
    data = {'name': '   ', 'email': '\t\n'}
    expected = {'name': '', 'email': ''}
    assert normalize_user_data(data) == expected