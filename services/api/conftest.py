#!/usr/bin/env python
"""
configure tests - returns a reference to the app
"""

import run
import pytest
import os
from json import dumps


@pytest.fixture
def app(request):
    # get app from main
    app = run.app
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()


GLOBAL_ID_TOKEN = None


# export TEST_OS_PASSWORD="password"
# export TEST_OS_USERNAME="test_user"
# export TEST_OS_USER_DOMAIN_NAME="testing"
@pytest.fixture(autouse=True)
def myglobal(app, request):
    global GLOBAL_ID_TOKEN
    if GLOBAL_ID_TOKEN:
        request.function.func_globals['global_id_token'] = GLOBAL_ID_TOKEN
        return
    # login and return bearer token
    client = app.test_client()
    r = client.post('/api/v1/ohsulogin',
                    data=dumps({"domain":
                                os.environ.get('TEST_OS_USER_DOMAIN_NAME'),
                                "user": os.environ.get('TEST_OS_USERNAME'),
                                "password": os.environ.get('TEST_OS_PASSWORD')
                                }),
                    content_type='application/json')
    assert r.status_code == 200
    assert r.json['id_token']
    request.function.func_globals['global_id_token'] = r.json['id_token']
    GLOBAL_ID_TOKEN = r.json['id_token']

# import run
# import pytest
# import elastic_client
#
# @pytest.fixture
# def app(request, test_users):
#     # get app from main
#     app = run.app
#
#     # Establish an application context before running the tests.
#     ctx = app.app_context()
#     ctx.push()
#
#     # Add setup here if necessary
#     # ...
#
#     # remove that context when done
#     def teardown():
#         # clean up data tests have created
#         db = app.data.driver.db
#         collections = ['file']
#         for collection in collections:
#             db[collection].delete_many({})
#         elastic_client.drop_index('aggregated_resource')
#         ctx.pop()
#
#     request.addfinalizer(teardown)
#     return app


# @pytest.fixture()  # pragma nocoverage
# def db(app, request):
#     return app.data.driver.db


# @pytest.fixture(scope="session")
# def test_users(request):
#     app = run.app
#
#     # Establish an application context before running the tests.
#     ctx = app.app_context()
#     ctx.push()
#
#     db = app.data.driver.db
#     db.auth_roles.insert_one({'mail': 'tesla@ldap.forumsys.com',
#                               'roles': ['admin']})
#
#     # remove that context when done
#     def teardown():
#         # clean up data tests have created
#         # clean up data tests have created
#         db.auth_roles.delete_many({})
#         ctx.pop()
#
#     request.addfinalizer(teardown)
