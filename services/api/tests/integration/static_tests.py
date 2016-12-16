#!/usr/bin/env python
"""
Test static endpoints
"""
import os


def test_get_login_page_returns_ok(client):
    """
    should respond with ok and redirect
    """
    r = client.get('/login')
    assert r.status_code == 200
    r = client.get('/login?redirect=foo')
    assert r.status_code == 200
    assert 'action="/login?redirect=foo"' in r.data


def test_post_login_page_returns_ok_and_token(client):
    """
    should respond with ok and token
    """
    r = client.post('/login', data=dict(
        domain=os.environ.get('OS_USER_DOMAIN_NAME'),
        username=os.environ.get('OS_USERNAME'),
        password=os.environ.get('OS_PASSWORD')
    ), follow_redirects=False)
    assert r.status_code == 201
    assert '<h3>JWT</h3>' in r.data


def test_post_login_page_returns_redirect(client):
    """
    should respond with redirect and token
    """
    r = client.post('/login?redirect=foo', data=dict(
        domain=os.environ.get('OS_USER_DOMAIN_NAME'),
        username=os.environ.get('OS_USERNAME'),
        password=os.environ.get('OS_PASSWORD')
    ), follow_redirects=False)
    assert r.status_code == 302
    assert 'foo?token=' in r.data


def test_post_bad_login_page_returns_invalid(client):
    """
    should respond with redirect and token
    """
    r = client.post('/login?redirect=foo', data=dict(
        domain='foo',
        username=os.environ.get('OS_USERNAME'),
        password=os.environ.get('OS_PASSWORD')
    ), follow_redirects=False)
    assert r.status_code == 401
    assert '<strong>Error:</strong>' in r.data
