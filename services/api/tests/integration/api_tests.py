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

TEST_RESOURCE = {'url': 'foo'}
