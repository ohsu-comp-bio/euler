"""
Test admin setup.
"""

from keystoneclient import client
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

import os


def test_should_have_env_defined():
    assert 'OS_USERNAME' in os.environ
    assert 'OS_AUTH_URL' in os.environ
    assert 'OS_PASSWORD' in os.environ
    assert 'OS_PROJECT_NAME' in os.environ
    assert 'OS_USER_DOMAIN_ID' in os.environ
    assert 'OS_PROJECT_DOMAIN_ID' in os.environ


def test_should_access_keystone():
    keystone = _authenticated_session()
    assert keystone


def test_keystone_should_be_v3():
    keystone = _authenticated_session()
    assert 'v3' in str(type(keystone))


def test_should_list_projects():
    projects = _authenticated_session().projects.list()
    assert len(projects) > 0


def test_should_have_admin_project():
    projects = _authenticated_session().projects.list()
    for project in projects:
        if project.name == 'admin':
            break
    assert project.name == 'admin'


def _authenticated_session():
    return _authenticated_session_password()


def _authenticated_session_password():
    """ login """
    auth = v3.Password(username=os.environ.get('OS_USERNAME'),
                       project_name=os.environ.get('OS_PROJECT_NAME'),
                       user_domain_id=os.environ.get('OS_USER_DOMAIN_ID'),
                       auth_url=os.environ.get('OS_AUTH_URL'),
                       password=os.environ.get('OS_PASSWORD'),
                       project_domain_id=os.environ.get('OS_PROJECT_DOMAIN_ID')
                       )
    sess = session.Session(auth=auth)
    return client.Client(session=sess)


def _authenticated_session_token():
    """ login """
    auth = v3.Token(token=os.environ.get('ADMIN_TOKEN'),
                    project_name='admin',
                    project_domain_id='default',
                    auth_url=os.environ.get('OS_AUTH_URL'),
                    )
    sess = session.Session(auth=auth)
    return client.Client(session=sess)
