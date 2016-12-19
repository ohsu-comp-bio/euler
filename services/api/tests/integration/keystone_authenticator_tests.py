#!/usr/bin/env python
"""
Test authenticator endpoints, depends on keystone
"""
from keystone_authenticator import BearerAuth
from json import dumps
import os


def test_encode_decode_token():
    profile = {'foo': 'bar'}
    auth = BearerAuth()
    token = auth.make_token(profile)
    parsed = auth.parse_token(token)
    assert parsed == profile


def test_authenticate(client):
    auth = BearerAuth()
    token = auth.authenticate_user(
        username=os.environ.get('OS_USERNAME'),
        user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME'),
        password=os.environ.get('OS_PASSWORD')
    )
    profile = auth.parse_token(token)
    assert profile
    assert profile['name']
    assert profile['domain_name']
    assert profile['mail']
    assert profile['token']
    assert len(profile['roles']) > 0
    for role in profile['roles']:
        assert role['role']
        assert role['scope']
        assert role['scope']['project']
        assert role['scope']['domain']


def test_login(client, app):
    """
    should respond with ok and user
    """
    _development_login(client, app)


def test_logout(client):
    """
    should respond with ok and user
    """
    r = client.post('/v0/logout')
    assert r


def _development_login(client, app):
    return global_id_token


def test_project_lookup(client, app):
    auth = BearerAuth()
    token = {u'mail': u'None', u'token': u'foo', u'domain_name': u'Default',
             u'roles': [
              {u'scope': {u'project': u'admin', u'domain': u'Default'},
                u'role': u'admin'},  # NOQA
              {u'scope': {u'project': u'user', u'domain': u'Default'},
                u'role': u'member'},  # NOQA
              ], u'name': u'admin'}
    assert len(auth._find_projects(token)) == 2


def test_should_retrieve_projects(client, app):
    auth = BearerAuth()
    len(auth.projects(_development_login(client, app))) == 1


def test_check_auth(client, app):
    auth = BearerAuth()
    # for now, only returns true
    assert auth.check_auth(None, None, None, None)


def test_check_default_projects(client, app):
    auth = BearerAuth()
    # for now, no public projects
    assert len(auth.projects(None, None)) == 0


def test_bad_login(client, app):
    """
    should respond with ok and user
    """
    r = client.post('/api/v1/ohsulogin',
                    headers={'content-type': 'application/json'},
                    data=dumps({'user': 'FOO', 'password': 'password'}))
    assert r.status_code == 401


def test_projects_from_token(client, app):
    id_token = _development_login(client, app)
    # save current auth, and ensure test_authenticator used for this test
    old_auth = app.auth
    app.auth = BearerAuth()
    request = {'headers': []}
    request = MockRequest()
    request.headers['authorization'] = 'Bearer {}'.format(id_token)
    projects = app.auth.projects(request=request)
    user = app.auth.get_user(request=request)
    app.auth = old_auth
    assert len(projects) > 0
    assert user


def test_authenticate_with_openstack_header(client, app):
    # save current auth, and ensure test_authenticator used for this test
    old_auth = app.auth
    app.auth = BearerAuth()
    id_token = _development_login(client, app)
    profile = app.auth.parse_token(id_token)
    assert profile['token']
    request = {'headers': []}
    request = MockRequest()
    request.headers['X-Auth-Token'] = profile['token']
    projects = app.auth.projects(request=request)
    user = app.auth.get_user(request=request)
    token = app.auth.token(request=request)
    app.auth = old_auth
    assert len(projects) > 0
    assert user
    assert token


def test_projects_from_unauthorized_token(client, app):
    # save current auth, and ensure test_authenticator used for this test
    old_auth = app.auth
    app.auth = BearerAuth()
    request = {'headers': []}

    class MockRequest:
        headers = {}

    request = MockRequest()
    projects = app.auth.projects(request=request)
    app.auth = old_auth
    assert len(projects) == 0


class MockRequest:
    headers = {}
