#!/usr/bin/env python

"""
Proxy front end to the dcc server
"""

import os
from eve import Eve
from flask import request, jsonify, Response
from flask_cors import CORS
from flask import stream_with_context
import requests

# our utilities
from keystone_authenticator import BearerAuth
import eve_util

assert 'PROXY_TARGET' in os.environ
PROXY_TARGET = os.environ['PROXY_TARGET']


def _configure_app():
    """ set app wide config """
    # start the app
    app = Eve(auth=BearerAuth)
    # allow cross site access
    CORS(app)
    # after commit, publish
    app.on_inserted += eve_util.on_inserted
    return app


#  main configuration
app = _configure_app()
#  print useful information at startup
app.logger.debug('Authenticator {}'.format(app.auth))
app.logger.debug('URL map {}'.format(app.url_map))


@app.route('/<path:url>', methods=['GET'])
def get_root(url):
    """
    Catch-All URL GET: Stream Proxy with Requests
    """
    app.logger.info('get_root')
    req = requests.get(_remote_url(), stream=True)
    # interesting example here ...
    # see http://www.programcreek.com/python/example/58918
    #        /flask.stream_with_context exec_query
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


@app.route('/v0/logout', methods=['POST'])
def _development_logout():
    """stub manual logout"""
    return jsonify(
        {'message': 'development user logged out'}
    )


@app.route('/v0/login', methods=['POST'])
def _development_login():
    """stub manual login"""
    credentials = request.get_json(silent=True)
    try:
        id_token = app.auth.authenticate_user(
                    user_domain_name=credentials['domain'],
                    username=credentials['user'],
                    password=credentials['password'])
        return jsonify({'id_token': id_token})
    except Exception as e:
        app.logger.debug(e)
        return Response('Invalid domain/user/password',
                        401, {'message': 'Invalid domain/user/password'})


# Private util functions

def _remote_url():
    """
    format a url for the configured remote host
    """
    return "{}{}".format(PROXY_TARGET, request.full_path)


# Entry point of app
if __name__ == '__main__':  # pragma: no cover
    # eve doesn't support standard "flask run", so set props here
    debug = 'PROXY_DEBUG' in os.environ  # TODO does eve override?
    api_port = int(os.environ.get('API_PORT', '5000'))
    api_host = os.environ.get('API_TARGET', '0.0.0.0')
    app.run(debug=debug, port=api_port, host=api_host)
    # app.run(debug=debug, port=api_port)
