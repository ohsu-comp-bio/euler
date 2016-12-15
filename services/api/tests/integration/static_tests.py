#!/usr/bin/env python
"""
Test static endpoints
"""


def test_get_login_page_returns_ok(client):
    """
    should respond with ok and files endpoint
    """
    r = client.get('/login')
    assert r.status_code == 200
