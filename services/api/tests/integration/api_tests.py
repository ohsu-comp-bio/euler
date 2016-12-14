#!/usr/bin/env python
"""
Test schema endpoint
"""


def test_simple_post_file(client):
    """
    should respond with ok
    """
    r = client.post('/v0/files', data=TEST_RESOURCE)
    assert r.status_code == 201


def test_simple_get_file(client):
    """
    should respond with ok
    """
    r = client.get('/v0/files')
    assert r.status_code == 200
    assert len(r.json) > 0

TEST_RESOURCE = {'url': 'foo', 'bob': 'your uncle'}
