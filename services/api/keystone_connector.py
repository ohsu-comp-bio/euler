#!/usr/bin/env python
"""
Connect to keystone for authentication and authorization.
Uses a system account, assumed to exist, defined by env variables:

['OS_USERNAME','OS_USER_DOMAIN_NAME','OS_PASSWORD','OS_AUTH_URL',
'OS_PROJECT_NAME','OS_USER_DOMAIN_ID','OS_PROJECT_DOMAIN_ID']

"""
import os

from keystoneclient import client
from keystoneauth1.identity import v3
from keystoneauth1 import session


def get_token_and_roles(username, user_domain_name, password):
    """ returns a tuple (token,role_assignments) """
    token, client = _get_token(
        username=username,
        user_domain_name=user_domain_name,
        password=password,
    )
    assert token['user']['id']
    user_id = token['user']['id']
    role_assignments = get_role_assignments(client, user_id)
    # place email into token
    user = client.users.get(user_id)
    if hasattr(user, 'email'):   # pragma: no cover
        token['user']['email'] = user.email
    else:
        token['user']['email'] = 'None'
    return token, role_assignments


def get_role_assignments(client, user_id):
    role_mgr = client.role_assignments
    role_assignments = role_mgr.list(user=user_id, include_names=True)
    return role_assignments


def validate_token(token, fetch_roles=False):
    """ returns access information. throws exception if invalid token """
    client = _authenticated_session()
    if not isinstance(token, basestring):
        token = token['auth_token']
    token_info = client.tokens.validate(token)
    if not fetch_roles:
        return token_info
    user_id = token_info['user']['id']
    role_assignments = get_role_assignments(client, user_id)
    return token_info, role_assignments


def _get_token(username, user_domain_name, password):
    client = _authenticated_session()
    token = client.get_raw_token_from_identity_service(
        username=username,
        user_domain_name=user_domain_name,
        auth_url=os.environ.get('OS_AUTH_URL'),
        password=password
    )
    return token, client


def _authenticated_session():
    return _authenticated_session_password()


def _authenticated_session_password():
    """ login """
    auth = v3.Password(username=os.environ.get('OS_USERNAME'),
                       user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME'),
                       auth_url=os.environ.get('OS_AUTH_URL'),
                       password=os.environ.get('OS_PASSWORD'),
                       project_name=os.environ.get('OS_PROJECT_NAME'),
                       project_domain_id=os.environ.get('OS_PROJECT_DOMAIN_ID')
                       )
    sess = session.Session(auth=auth)
    return client.Client(session=sess)


def _authenticated_session_token():  # pragma nocoverage
    """ login """
    auth = v3.Token(token=os.environ.get('ADMIN_TOKEN'),
                    project_name='admin',
                    project_domain_id='default',
                    auth_url=os.environ.get('OS_AUTH_URL'),
                    )
    sess = session.Session(auth=auth)
    return client.Client(session=sess)
