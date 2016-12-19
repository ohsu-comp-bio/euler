#!/usr/bin/env python
"""
Test proxy
"""
import urllib
import json
import os
from json import dumps

# assumes OS_USERNAME has access to only one project
MY_PROJECT = 'BRCA-UK'


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
    app.logger.debug(headers)
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
    print r.json
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
    return 'Bearer {}'.format(global_id_token)
