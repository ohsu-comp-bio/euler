#!/usr/bin/env python

"""
Proxy front end to the dcc server
"""
import os
from flask import request, Response, abort, make_response
from flask import current_app as app
from flask import stream_with_context
import requests
import urllib
from pydash import deep_set, deep_get, filter_, reduce_, pluck
from json import loads, dumps

assert 'PROXY_TARGET' in os.environ
PROXY_TARGET = os.environ['PROXY_TARGET']


def get_any(url):
    """
    Catch-All URL GET: Stream Proxy with Requests
    """
    remote_url = _remote_url()
    app.logger.debug(remote_url)
    # Note: /api/browser/gene and /api/browser/mutation take differnet paths
    # through the client (h2 add Authentication header)
    # see dcc-portal-ui/app/vendor/scripts/genome-viewer/icgc-gene-adapter.js
    whitelist_paths = ['/api/version', '/api/v1/releases/current',
                       '/api/browser/gene', '/api/browser/mutation']
    auth_required = request.path not in whitelist_paths
    # if no whitelist_projects, abort
    _whitelist_projects(auth_required)
    req = requests.get(remote_url, stream=True)
    # interesting example here ...
    # see http://www.programcreek.com/python/example/58918
    #        /flask.stream_with_context exec_query
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


def post_any(url):  # pragma nocoverage  TODO
    """
    Catch-All URL POST: Stream Proxy with Requests
    """
    req = requests.post(_remote_url(), stream=True)
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


def get_projects(url):
    """ apply project filter to files request /api/v1/projects"""
    # if no whitelist_projects, don't abort
    whitelist_projects = _whitelist_projects(False)
    if len(whitelist_projects) == 0:
        whitelist_projects = ['UNAUTHENTICATED_USER']  # has no projects
    # create mutable dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_project_codes(params, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)


def get_projects_genes(url, projects):
    """ apply project filter to files request /api/v1/projects/.../genes"""
    # if no whitelist_projects, don't abort
    whitelist_projects = _whitelist_projects(True)
    # contrain list of projects
    project_codes = projects.split(',')
    if not set(project_codes) <= set(whitelist_projects):
        abort(401, {'message': 'you do not have access to projects:{}'
              .format(set(project_codes) - set(whitelist_projects))})
    # call PROXY_TARGET
    return _call_proxy_target()


def get_projects_history(url):
    """
    if we look at the implementation of this endpoint, there are no filters
    http://bit.ly/2hJggE4 So, redact the response strip off all projects
    not in white list
    """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # call the remote
    remote_response = requests.get(_remote_url())
    groups = remote_response.json()
    # redact
    groups = filter_(groups, lambda group:
                     group['group'] in whitelist_projects)
    # formulate response with redacted groups and original content type
    response = make_response(dumps(groups))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    return response


def get_files():
    """ apply project filter to files request /api/v1/repository/files"""
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutable dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_file_project_codes(params,
                                                       whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)

def get_files_summary():
    """ apply project filter to files request /api/v1/repository/files/summary """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutable dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_file_project_codes(params, 
                                                       whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)

def get_ui_search_projects_donor_mutation_counts(url):
    """
    if we look at the implementation of this endpoint, there are no filters
    http://bit.ly/2hICXZ9 So, redact the response strip off all projects
    not in white list
    """
    # {
    #   "BRCA-UK": {
    #     "DO1007": 97,
    #     "DO1128": 47,
    #     "DO1006": 317,
    #     "DO1127": 74, ...}, ... }
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # call the remote
    remote_response = requests.get(_remote_url())
    # redact the response
    counts = remote_response.json()
    omit_these = set(counts.keys()) - set(whitelist_projects)
    for key in omit_these:
        if key in counts:
            del counts[key]
    # formulate response with redacted counts and original content type
    response = make_response(dumps(counts))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    return response


def get_ui_search_gene_project_donor_counts(url):
    """
    if we look at the implementation of this endpoint, there are no filters
    http://bit.ly/2hfku5a So, redact the response strip off all projects
    not in white list
    """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # call the remote
    remote_response = requests.get(_remote_url())
    counts = remote_response.json()
    # redact
    for gene_name in counts:
        gene = counts[gene_name]
        gene['terms'] = filter_(gene['terms'],
                                lambda term:
                                term['term'] in whitelist_projects)
    # re-aggregate after redaction
    for gene_name in counts:
        gene = counts[gene_name]
        gene['total'] = reduce_(pluck(gene['terms'], 'count'),
                                lambda total, count: total + count)

    # formulate response with redacted counts and original content type
    response = make_response(dumps(counts))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    return response


def get_donors(url):
    """ apply project filter to files request /api/v1/donors"""
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutable dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call the remote
    remote_response = requests.get(_remote_url(params))
    # redact
    d = remote_response.json()
    if 'projectId' in d['facets']:
        # redact project list
        projects = d['facets']['projectId']
        projects['terms'] = filter_(projects['terms'],
                                    lambda term: term['term']
                                    in whitelist_projects)
        # re-aggregate after redaction
        if 'terms' in projects and len(projects['terms']) > 0:
            projects['total'] = reduce_(pluck(projects['terms'], 'count'),
                                        lambda total, count: total + count)
    # formulate response with redacted projects and original content type
    response = make_response(dumps(d))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    return response


def get_download_info_projects(release):
    """
    if we look at the implementation of this endpoint, there are no filters
    http://bit.ly/2iCeW8C So, redact the response strip off all projects
    not in white list
    """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutable dict, this request has no parameters
    params = request.args.copy()
    # call the remote
    remote_response = requests.get(_remote_url(params))
    # redact

    def dir_ok(name):
        return 'README' in name or name in whitelist_projects

    d = remote_response.json()
    d = filter_(d,
                lambda dir: dir_ok(dir['name'].split('/')[-1]))
    # formulate response with redacted projects and original content type
    response = make_response(dumps(d))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    return response


# Private util functions ########################################

def _ensure_project_codes(params, whitelist_projects):
    """ set project code filter, returns project codes and updated params """
    project_codes = deep_get(params, 'filters.project.id.is')
    if project_codes:
        intersection = list(set(params).intersection(whitelist_projects))
        if len(intersection) == 0:
            intersection = whitelist_projects
        params = deep_set(params, 'filters.project.id.is', intersection)
        return params, project_codes

    project_codes = deep_get(params, 'filters.project.id.not')
    if project_codes or project_codes == []:
        # remove the 'not'
        params = deep_set(params, 'filters.project.id', {})
        # set to 'is intersection'
        difference = list(set(whitelist_projects) - set(project_codes))
        params = deep_set(params, 'filters.project.id.is', difference)
        return params, project_codes

    params = deep_set(params,
                      'filters.project.id.is', whitelist_projects)
    project_codes = deep_get(params, 'filters.project.id.is')
    return params, project_codes


def _call_proxy_target(params=None):
    """ call PROXY_TARGET """
    req = requests.get(_remote_url(params), stream=True)
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


def _abort_if_unauthorized(project_codes, whitelist_projects):
    """ unauthorized if not project_codes subset of whitelist """
    if not set(project_codes) <= set(whitelist_projects):
        abort(401, {'message': 'you do not have access to projects:{}'
              .format(set(project_codes) - set(whitelist_projects))})


def _whitelist_projects(mandatory=False):
    """ return project list, abort if missing  """
    whitelist_projects = app.auth.projects(request=request)
    if mandatory and not whitelist_projects:
        abort(401, {'message': 'authorization required, no project access'})
    return whitelist_projects


def _ensure_filters():
    """ return mutable dict, ensure filters params """
    # create mutable dict
    params = request.args.copy()
    # ensure 'filters' param exists
    if 'filters' not in params:
        params['filters'] = {}
    # ensure 'filters' parameter string is decoded
    if isinstance(params['filters'], basestring):
        params['filters'] = loads(urllib.unquote_plus(params['filters']))
    return params


def _ensure_file_project_codes(params, whitelist_projects):
    """ set project code filter, returns project codes and updated params """
    project_codes = deep_get(params, 'filters.file.projectCode.is')
    if not project_codes:
        params = deep_set(params,
                          'filters.file.projectCode.is', whitelist_projects)
        project_codes = deep_get(params, 'filters.file.projectCode.is')
    return params, project_codes


def _ensure_donor_project_ids(params, whitelist_projects):
    """ set project code filter, returns project codes and updated params
        {"donor":{"projectId":{"is":["ALL-US"]}}
    """
    project_codes = deep_get(params, 'filters.donor.projectId.is')
    if not project_codes:
        params = deep_set(params,
                          'filters.donor.projectId.is', whitelist_projects)
        project_codes = deep_get(params, 'filters.donor.projectId.is')
    return params, project_codes


def _remote_url(params=None, url=None):
    """
    format a url for the configured remote host. if params, a new query_string
    is created.  if url, that url is used instead of original
    """
    if params:
        return _remote_url_params(params)
    if url:  # pragma nocoverage
        return "{}{}".format(PROXY_TARGET, url)
    return "{}{}".format(PROXY_TARGET, request.full_path)


def _remote_url_params(params):
    """
    format a url for the configured remote host, using passed param dict
    """
    filters = params['filters']
    params['filters'] = dumps(filters)
    query = urllib.urlencode(params)
    url = "{}{}?{}".format(PROXY_TARGET, request.path, query)
    app.logger.debug('url {}'.format(url))
    return url
