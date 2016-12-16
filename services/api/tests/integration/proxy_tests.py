#!/usr/bin/env python
"""
Test proxy
"""


def test_status_returns_ok(client):
    """
    should respond with ok and response from dcc
    """
    r = client.get('/api/version')
    assert r.status_code == 200
    assert r.json.keys() == ['indexCommit', 'indexName', 'api',
                             'portal', 'portalCommit']
