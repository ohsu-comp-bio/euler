#!/usr/bin/env python
"""
Test schema endpoint
"""
from keystone_authenticator import BearerAuth
import keystone_connector as connector

from json import dumps
import os


def _development_login(client):
    return global_id_token


def test_simple_post_file(client):
    """
    should respond with ok
    """
    # # You must initialize logging, otherwise you'll not see debug output.
    # http_client.HTTPConnection.debuglevel = 1
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("requests.packages.urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True

    id_token = _development_login(client)
    headers = {'Authorization': 'Bearer {}'.format(id_token)}
    r = client.post('/v0/files', data=TEST_RESOURCE, headers=headers)
    assert r.status_code == 201


def test_simple_get_file(client):
    """
    should respond with ok
    """
    id_token = _development_login(client)
    headers = {'Authorization': 'Bearer {}'.format(id_token)}
    r = client.get('/v0/files', headers=headers)
    assert r.status_code == 200
    assert len(r.json) > 0


def test_simple_get_file_x_auth(client, app):
    """
    should respond with ok
    """
    # http_client.HTTPConnection.debuglevel = 1
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("requests.packages.urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True

    id_token = _development_login(client)
    auth = app.auth
    profile = auth.parse_token(id_token)

    headers = {'X-Auth-Token': profile['token']}
    r = client.get('/v0/files', headers=headers)
    assert r.status_code == 200
    assert len(r.json) > 0
    connector.validate_token(profile['token'], fetch_roles=True)


TEST_RESOURCE = {'url': 'foo', 'bob': 'your uncle'}
