#!/usr/bin/env python
"""
Test keystone endpoints
"""
import keystone_connector as connector
import os
import pytest


def test_should_have_env_defined():
    """for auth user (the system account assigned to authenticate)"""
    assert 'OS_USERNAME' in os.environ
    assert 'OS_USER_DOMAIN_NAME' in os.environ
    assert 'OS_PASSWORD' in os.environ
    assert 'OS_AUTH_URL' in os.environ
    assert 'OS_PROJECT_NAME' in os.environ
    assert 'OS_USER_DOMAIN_ID' in os.environ
    assert 'OS_PROJECT_DOMAIN_ID' in os.environ


def test_should_list_roles_for_auth_user():
    token, role_assignments = connector.get_token_and_roles(
                        username=os.environ.get('OS_USERNAME'),
                        user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME'),
                        password=os.environ.get('OS_PASSWORD'),
                      )
    assert token['user']['id']
    assert role_assignments


def test_should_validate_token_for_auth_user():
    token, role_assignments = connector.get_token_and_roles(
                        username=os.environ.get('OS_USERNAME'),
                        user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME'),
                        password=os.environ.get('OS_PASSWORD'),
                      )
    assert connector.validate_token(token)
    assert connector.validate_token(token['auth_token'])
    try:
        connector.validate_token('foo')
    except Exception:
        pass


@pytest.mark.skipif('TEST_OS_USERNAME' not in os.environ,
                    reason="""
Please configure [TEST_OS_USERNAME,TEST_OS_USER_DOMAIN_NAME,TEST_OS_PASSWORD]
if you would like to test end user authentication.
            """)
def test_should_list_roles_for_any_user():  # pragma nocoverage
    token, role_assignments = connector.get_token_and_roles(
                        username=os.environ.get('TEST_OS_USERNAME'),
                        user_domain_name=os.environ.get(
                                'TEST_OS_USER_DOMAIN_NAME'),
                        password=os.environ.get('TEST_OS_PASSWORD'),
                     )
    assert token['user']['id']
    assert role_assignments
