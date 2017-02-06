#!/usr/bin/env python

"""
Formulate manifest for exacloud
"""
from flask import send_file, abort
from json import dumps
import urllib
import requests
import StringIO
from flask import current_app as app


def create(params, PROXY_TARGET, _check_projects):
    """ create an exacloud manifest """
    # if 'filters' not in params:
    #     abort(400, {'message': 'no filters on manifest request'})
    # call the files api to get details
    files_params = {}
    filters = params['filters']
    files_params['filters'] = dumps(filters)
    query = urllib.urlencode(files_params)
    url = "{}{}?{}".format(PROXY_TARGET,
                           '/api/v1/repository/files',
                           query)
    # call the remote
    files_response = requests.get(url)
    files = files_response.json()
    if 'hits' not in files or len(files['hits']) == 0:
        abort(400, {'message': 'no files found on manifest request'})

    # collect info about the file
    project_codes = []
    paths = []
    for hit in files['hits']:
        for donor in hit['donors']:
            project_codes.append(donor['projectCode'])
        for fileCopy in hit['fileCopies']:
            # if fileCopy['repoCode'] == 'exacloud':
            paths.append(fileCopy['fileName'])
    # ensure project authorization
    _check_projects(set(project_codes))

    template = app.jinja_env.get_template('exacloud_manifest.txt')
    strIO = StringIO.StringIO()
    strIO.write(str(template.render(paths=set(paths))))
    strIO.seek(0)
    return send_file(strIO,
                     attachment_filename="exacloud_manifest.sh",
                     as_attachment=True)
