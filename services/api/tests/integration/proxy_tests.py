#!/usr/bin/env python
"""
Test proxy
"""
import urllib
import json

# assumes OS_USERNAME has access to only one project
MY_PROJECT = 'BRCA-UK'


def test_should_create_external_entityset_ok(client, app):
    """
    should respond with ok /api/v1/entityset/external
    """
    headers = {'Authorization': _login_bearer_token(client, app),
               'Content-Type': 'application/json'}
    data = {"filters": {}, "size": 173535, "type": "DONOR",
            "name": "Input donor set", "description": "", "isTransient": True,
            "sortBy": "fileName", "sortOrder": "DESCENDING"}
    r = client.post('/api/v1/entityset/external', headers=headers,
                    data=json.dumps(data))
    assert r.status_code == 201
    assert r.json['id']


def test_should_validate_token_ok(client, app):
    """
    should respond with ok and response for token
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/auth/verify', headers=headers)
    assert r.status_code == 200


def test_should_reject_missing_token(client, app):
    """
    should respond with ok and response for token
    """
    r = client.get('/api/v1/auth/verify')
    assert r.status_code == 401


def test_redact_download_info(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/download/info/current/Projects', headers=headers)
    assert r.status_code == 200
    assert len(r.json) > 0
    for dir in r.json:
        assert MY_PROJECT in dir['name'] or 'README' in dir['name']


def test_donors_returns_ok(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    params = {'from': 1, 'include': 'facets', 'size': 25}
    r = client.get('/api/v1/donors',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    assert r.json.keys() == [u'pagination', u'hits', u'facets']
    for hit in r.json['hits']:
        assert hit['projectId'] == MY_PROJECT
    if 'projectId' in r.json['facets']:
        for term in r.json['facets']['projectId']['terms']:
            assert term['term'] == MY_PROJECT


def test_donors_facets_only_ok(client, app):
    """
    should respond with ok and response from dcc, when facetsOnly=true
    and filter parameter created by browser is bad
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    params = {'facetsOnly': True, 'include': 'facets', 'size': 10,
              'from': 1, 'filters': '{"donor":{"id":{"is":["ES:undefined"]}}}'}
    r = client.get('/api/v1/donors',
                   query_string=params, headers=headers)
    assert r.status_code == 400


def test_status_returns_ok(client):
    """
    should respond with ok and response from dcc
    """
    r = client.get('/api/version')
    assert r.status_code == 200
    assert r.json.keys() == ['indexCommit', 'indexName', 'api',
                             'portal', 'portalCommit']


def test_files_returns_ok(client, app):
    """
    should respond with ok and response from dcc
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {"file": {"repoName": {"is": ["Collaboratory - Toronto"]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters, 'from': 1, 'include': 'facets', 'size': 25}
    r = client.get('/api/v1/repository/files',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    assert r.json.keys() == [u'hits', u'termFacets', u'pagination']
    for hit in r.json['hits']:
        for donor in hit['donors']:
            assert donor['projectCode'] == MY_PROJECT


def test_files_returns_unauthorized_for_no_token(client, app):
    """
    should respond with ok and response from dcc
    """
    filters = {"file": {"repoName": {"is": ["Collaboratory - Toronto"]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters, 'from': 1, 'include': 'facets', 'size': 25}
    r = client.get('/api/v1/repository/files', query_string=params)
    assert r.status_code == 401


def test_files_returns_unauthorized_for_bad_projects(client, app):
    """
    should respond with 401 if project codes don't match
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {"file": {"repoName": {"is": ["Collaboratory - Toronto"]}, "projectCode": {"is": ["X", "Y"]}}}  # NOQA
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters, 'from': 1, 'include': 'facets', 'size': 25}
    r = client.get('/api/v1/repository/files',
                   query_string=params, headers=headers)
    assert r.status_code == 401


def test_projects_returns_empty_list_if_unauthenticated(client, app):
    """ /api/v1/projects """
    r = client.get('/api/v1/projects')
    assert r.status_code == 200
    assert len(r.json['hits']) == 0


def test_projects_returns_list_if_authenticated(client, app):
    """ /api/v1/projects """
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/projects', headers=headers)
    assert r.status_code == 200
    assert len(r.json['hits']) == 1


def test_projects_returns_list_if_project_specified(client, app):
    """ /api/v1/projects """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {"project": {"id": {"is": [MY_PROJECT]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters}
    r = client.get('/api/v1/projects', headers=headers, query_string=params)
    assert r.status_code == 200
    assert len(r.json['hits']) == 1


def test_projects_returns_list_if_not_project_specified(client, app):
    """ /api/v1/projects """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {"project": {"id": {"not": []}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters}
    r = client.get('/api/v1/projects', headers=headers, query_string=params)
    assert r.status_code == 200
    assert len(r.json['hits']) == 1


def test_gene_project_donor_counts(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/ui/search/gene-project-donor-counts/ENSG00000005339??filters=%7B%22mutation%22:%7B%22functionalImpact%22:%7B%22is%22:%5B%22High%22%5D%7D%7D%7D', headers=headers)  # NOQA
    assert r.status_code == 200
    assert r.json['ENSG00000005339']
    assert r.json['ENSG00000005339']['terms'][0]['term'] == MY_PROJECT


def test_donor_mutation_counts(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/ui/search/projects/donor-mutation-counts', headers=headers)  # NOQA
    assert r.status_code == 200
    assert r.json[MY_PROJECT]
    assert len(r.json.keys()) == 1


def test_projects_history(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/projects/history', headers=headers)
    assert r.status_code == 200
    for group in r.json:
        assert group['group'] == MY_PROJECT


def test_projects_genes(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/projects/{}/genes'.format(MY_PROJECT), headers=headers)  # NOQA
    assert r.status_code == 200


def test_projects_genes_bad_project(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/projects/{}/genes'.format('NOT_A_PROJECT'), headers=headers)  # NOQA
    assert r.status_code == 401


def _login_bearer_token(client, app):
    global global_id_token
    return 'Bearer {}'.format(global_id_token)
