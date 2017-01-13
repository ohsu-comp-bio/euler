#!/usr/bin/env python

"""
Proxy front end to the dcc server
"""

import os
from eve import Eve
from flask import request, jsonify, Response, abort
from flask_cors import CORS
from flask import redirect, render_template
# our utilities
from keystone_authenticator import BearerAuth
import eve_util
import dcc_proxy


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


@app.route('/api/v1/auth/logout', methods=['POST'])
def _development_logout():
    """stub manual logout"""
    return jsonify(
        {'message': 'user logged out'}
    )


@app.route('/api/v1/ohsulogin', methods=['POST'])
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
        return Response('Invalid domain/user/password',
                        401, {'message':
                              'Invalid domain/user/password {}'.format(e)})


@app.route('/login', methods=['POST', 'GET'])
def html_login():
    """login via form"""
    if request.method == 'GET':
        redirect_url = request.args.get('redirect')
        redirect_parm = ''
        if redirect_url:
            redirect_parm = '?redirect={}'.format(redirect_url)
        return render_template('login.html',
                               redirect_parm=redirect_parm)
    id_token = None
    try:
        id_token = app.auth.authenticate_user(
            user_domain_name=request.form['domain'],
            username=request.form['username'],
            password=request.form['password'])
    except Exception:
        pass  # app.logger.exception(e)
    if not id_token:
        return render_template('login.html',
                               domain=request.form['domain'],
                               username=request.form['username'],
                               password=request.form['password'],
                               redirect_parm='',
                               error='Invalid domain/user/pass'
                               ), 401
    redirect_url = request.args.get('redirect')
    if redirect_url:
        return redirect(redirect_url + '?token={}'.format(id_token))
    return render_template('login.html',
                           domain=request.form['domain'],
                           username=request.form['username'],
                           password=request.form['password'],
                           token=id_token,
                           redirect_parm=''
                           ), 201


@app.route('/api/v1/auth/verify', methods=['GET'])
def verify():
    id_dict = app.auth.token(request)
    if not id_dict:
        abort(401, {'message': 'invalid token'})
    return jsonify({"token": id_dict['token'],
                    "username": '{}@{}'.format(id_dict['name'],
                                               id_dict['domain_name']),
                    "daco": False,
                    "cloudAccess": True}
                   )


@app.route('/api/v1/repository/files', methods=['GET'])
def get_files():
    """
    filter files request
    """
    return dcc_proxy.get_files()


@app.route('/api/v1/repository/files/summary', methods=['GET'])
def get_files_summary():
    """
    filter donor summary request
    """
    return dcc_proxy.get_files_summary()


@app.route('/api/v1/projects/<path:projects>/genes', methods=['GET'])
def get_projects_genes(projects):
    """
    filter projects request
    """
    return dcc_proxy.get_projects_genes('/api/v1/projects/', projects)


@app.route('/api/v1/projects/history', methods=['GET'])
def get_projects_history():
    """
    filter projects request
    """
    return dcc_proxy.get_projects_history('/api/v1/projects/history')


@app.route('/api/v1/projects', methods=['GET'])
def get_projects():
    """
    filter projects request
    """
    return dcc_proxy.get_projects('/api/v1/projects')


@app.route('/api/v1/ui/search/projects/donor-mutation-counts',
           methods=['GET'])
def get_ui_search_projects_donor_mutation_counts():
    """
    filter donor-mutation-counts request
    """
    return dcc_proxy.get_ui_search_projects_donor_mutation_counts(
        '/api/v1/ui/search/projects/donor-mutation-counts')


@app.route('/api/v1/ui/search/gene-project-donor-counts/<path:url>',
           methods=['GET'])
def get_ui_search_gene_project_donor_counts(url):
    """
    filter gene-project-donor-counts request
    """
    return dcc_proxy.get_ui_search_gene_project_donor_counts(
        '/api/v1/ui/search/gene-project-donor-counts/{}'.format(url))


@app.route('/api/v1/donors',
           methods=['GET'])
def get_donors():
    """
    filter donors request
    """
    return dcc_proxy.get_donors('/api/v1/donors')


@app.route('/api/v1/genes',
           methods=['GET'])
def get_genes():
    """
    filter genes request
    """
    return dcc_proxy.get_genes('/api/v1/genes')
 

@app.route('/api/v1/genes/count',
           methods=['GET'])
def genes_count():
    """
    filter genes count request
    """
    return dcc_proxy.get_genes_count('/api/v1/genes/count')


@app.route('/api/v1/genesets/<path:geneSetIds>/genes/counts',
           methods=['GET'])
def get_genesets_genes_counts(geneSetIds):
    """
    filter genesets/{geneSetId}/genes/count request
    """
    return dcc_proxy.get_genesets_genes_counts('/api/v1/genesets', geneSetIds)


@app.route('/api/v1/mutations', 
           methods=['GET'])
def get_mutations():
    """
    filter mutations request
    """
    return dcc_proxy.get_mutations('/api/v1/mutations')

@app.route('/api/v1/download/info/<path:release>/Projects',
           methods=['GET'])
def get_download_info_projects(release):
    """
    redact download info request
    """
    return dcc_proxy.get_download_info_projects(release)


@app.route('/api/<path:url>', methods=['GET'])
def get_any(url):
    """
    Catch-All URL GET: Stream Proxy with Requests
    """
    return dcc_proxy.get_any(url)


@app.route('/api/<path:url>', methods=['POST'])
def post_any(url):  # pragma nocoverage TODO
    """
    Catch-All URL POST: Stream Proxy with Requests
    """
    return dcc_proxy.post_any(url)

# Private util functions


#  print useful information at startup
app.logger.debug('URL map {}'.format(app.url_map))


# Entry point of app
if __name__ == '__main__':  # pragma: no cover
    # eve doesn't support standard "flask run", so set props here
    debug = 'API_DEBUG' in os.environ  # TODO does eve override?
    api_port = int(os.environ.get('API_PORT', '5000'))
    api_host = os.environ.get('API_TARGET', '0.0.0.0')
    app.run(debug=debug, port=api_port, host=api_host)
    # app.run(debug=debug, port=api_port)
