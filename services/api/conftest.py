#!/usr/bin/env python
"""
configure tests - returns a reference to the app
"""

import run
import pytest


@pytest.fixture
def app(request):
    # get app from main
    app = run.app
    return app


@pytest.fixture
def client(app):
    return app.test_client()

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
