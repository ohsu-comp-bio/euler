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
from flask import redirect, url_for, abort, render_template, flash
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
    app.template_folder = os.path.join(os.path.dirname(
                                       os.path.abspath(__file__)),
                                       'templates')
    app._static_folder = os.path.abspath("static/")
    return app


#  main configuration
app = _configure_app()
#  print useful information at startup
app.logger.debug('Authenticator {}'.format(app.auth))


@app.route('/api/<path:url>', methods=['GET'])
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


# let's find the rule that was just generated
rule = app.url_map._rules[-1]
# we create some comparison keys:
# increase probability that the rule will be near or at the bottom
bottom_compare_key = True, 100, [(2, 0)]
# rig rule.match_compare_key() to return the spoofed compare_key
rule.match_compare_key = lambda: bottom_compare_key


@app.route('/v0/logout', methods=['POST'])
def _development_logout():
    """stub manual logout"""
    return jsonify(
        {'message': 'development user logged out'}
    )


@app.route('/v0/login', methods=['POST'])
def _api_login():
    """login via json"""
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


@app.route('/login', methods=['POST', 'GET'])
def html_login():
    """login via form"""
    if request.method == 'GET':
        redirect_url = request.args.get('redirect')
        app.logger.debug('html_login get redirect_url {}'.format(
            redirect_url))
        redirect_parm = ''
        if redirect_url:
            redirect_parm = '?redirect={}'.format(redirect_url)
        return render_template('login.html',
                               redirect_parm=redirect_parm)
    app.logger.debug('html_login post {} {} {}'.format(
        request.form['domain'],
        request.form['username'],
        request.form['password']))
    id_token = None
    try:
        id_token = app.auth.authenticate_user(
            user_domain_name=request.form['domain'],
            username=request.form['username'],
            password=request.form['password'])
        app.logger.debug('html_login post id_token {}'.format(
            id_token))
    except Exception as e:
        app.logger.exception(e)
    if not id_token:
        return render_template('login.html',
                               domain=request.form['domain'],
                               username=request.form['username'],
                               password=request.form['password'],
                               redirect_parm='',
                               error='Invalid domain/user/password'), 401
    redirect_url = request.args.get('redirect')
    if redirect_url:
        app.logger.debug('html_login post redirect_url {}'.format(
            redirect_url))
        return redirect(redirect_url + '?token={}'.format(id_token))
    return render_template('login.html',
                           domain=request.form['domain'],
                           username=request.form['username'],
                           password=request.form['password'],
                           token=id_token,
                           redirect_parm=''
                           ), 201

# Private util functions


def _remote_url():
    """
    format a url for the configured remote host
    """
    return "{}{}".format(PROXY_TARGET, request.full_path)


app.logger.debug('URL map {}'.format(app.url_map))


# Entry point of app
if __name__ == '__main__':  # pragma: no cover
    # eve doesn't support standard "flask run", so set props here
    debug = 'API_DEBUG' in os.environ  # TODO does eve override?
    api_port = int(os.environ.get('API_PORT', '5000'))
    api_host = os.environ.get('API_TARGET', '0.0.0.0')
    app.run(debug=debug, port=api_port, host=api_host)
    # app.run(debug=debug, port=api_port)
