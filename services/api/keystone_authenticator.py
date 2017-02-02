#!/usr/bin/env python

"""
Implements a BearerAuth JWT token using keystone backend
"""

import os
import jwt
import keystone_connector as connector
from eve.auth import TokenAuth
import pydash
from pydash import deep_get
from pydash import deep_pluck
from flask import request

# This should be well-guarded server secret   (in a env, file or database).
assert 'AUTHENTICATOR_SECRET' in os.environ
JWT_SECRET = os.environ.get('AUTHENTICATOR_SECRET',
                            'THIS IS NOT SECURE')


class BearerAuth(TokenAuth):
    """
    Override buildin basic auth
    Create an ID token
    """
    def __init__(self):
        super(BearerAuth, self).__init__()

    def authenticate_user(self, username, user_domain_name, password):
        """ ask the connector to get profile """
        token, role_assignments = connector.get_token_and_roles(
            username=username, user_domain_name=user_domain_name,
            password=password)
        profile = self._map_profile(token, role_assignments)
        return self.make_token(profile)

    def make_token(self, profile):
        return jwt.encode(profile, JWT_SECRET,
                          headers={'exp': 60 * 24 * 30})

    def parse_token(self, token):
        return jwt.decode(token, JWT_SECRET)

    def check_auth(self, token, allowed_roles, resource, method):
        """
        This function replaces the builtin check_auth, and can perform
        arbitrary actions based on the result of the
        Access Control Rules Engine.
        """
        # TODO validate token here
        return True

    def token(self, request):
        """ extract and parse token, can be null """
        # first check if we have a web user
        bearer_prefix = 'Bearer '
        header_token = request.headers.get('authorization')
        if header_token and header_token.startswith(bearer_prefix):
            token = header_token[len(bearer_prefix):]
            id_dict = self.parse_token(token)
            return id_dict
        # see if we have an openstack user
        header_token = request.headers.get('X-Auth-Token')
        if header_token:  # pragma nocoverage
            token = header_token
            token_info, role_assignments = connector.validate_token(
                token,
                fetch_roles=True
            )
            return self._map_profile(token_info, role_assignments)
        # was a cookie set?
        if 'id_token' in request.cookies:
            id_dict = self.parse_token(request.cookies.get('id_token'))
            return id_dict
        return None

    def get_user(self, request):
        """ return a representation of the user org.name """
        id_dict = self.token(request)
        user = 'Anonymous'
        if id_dict:
            user = "{}.{}".format(id_dict['domain_name'],
                                  id_dict['name'])
        return user

    def _map_profile(self, token, role_assignments):
        """ given keystone profile, return ID_TOKEN profile """

        domain_name = deep_get(token, 'user.domain.name')
        roles = []
        for assignment in role_assignments:
            role = assignment.role['name']
            scope = assignment.scope
            simple_scope = {'domain': deep_get(scope, 'project.domain.name'),
                            'project': deep_get(scope, 'project.name')}
            roles.append({'role': role, 'scope': simple_scope})
        id_dict = {
            'domain_name': domain_name,
            'name': pydash.deep_get(token, 'user.name'),
            'mail': pydash.deep_get(token, 'user.email'),
            'roles': roles,
            'token': token['auth_token']
        }
        return id_dict

    def projects(self, token=None, request=None):
        """ given a token, extact the groups and lookup the projects """
        parsed = None
        if token:
            parsed = self.parse_token(token)
        if request:
            parsed = self.token(request)
        if parsed:
            return self._find_projects(parsed)
        else:
            return self._find_projects()

    def _find_projects(self, token=None):
        """ given a token, return project names """
        if not token:
            return []
        return deep_pluck(token['roles'], 'scope.project')

    def authorized(self, allowed_roles, resource, method):
        """ Validates the the current request is allowed to pass through.
        :param allowed_roles: allowed roles for the current request, can be a
                              string or a list of roles.
        :param resource: resource being requested.
        """
        auth = None
        # if hasattr(request.authorization, 'username'):
        #     auth = request.authorization.username

        # Werkzeug parse_authorization does not handle
        # "Authorization: <token>" or
        # "Authorization: Token <token>" or
        # "Authorization: Bearer <token>"
        # headers, therefore they should be explicitly handled
        if not auth and request.headers.get('Authorization'):
            auth = request.headers.get('Authorization').strip()
            if auth.lower().startswith(('token', 'bearer')):
                auth = auth.split(' ')[1]

        # Handle X-Auth-Token
        if not auth and request.headers.get('X-Auth-Token'):
            auth = request.headers.get('X-Auth-Token').strip()

        return auth and self.check_auth(auth, allowed_roles, resource,
                                        method)
