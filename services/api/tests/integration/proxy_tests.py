#!/usr/bin/env python
"""
Test proxy
"""
import urllib
import json
import os
# import pytest

# assumes OS_USERNAME has access to only one project
MY_PROJECT = 'BRCA-UK'
MY_GENESET = 'GS1'
MY_GENE = 'ENSG00000141510'
# this file needs to exist in BRCA-UK
FILE_ID = "FIffb3540a357a4c23611364d4cafa5d57"  # "FI661960"


def test_get_download_summary_ok(client, app):
    """
    should respond with ok /api/v1/download/info/current/Summary
    """
    headers = {'Authorization': _login_bearer_token(client, app),
               'Content-Type': 'application/json'}
    os.environ["SUMMARY_PROJECT_NAME"] = MY_PROJECT
    r = client.get('/api/v1/download/info/current/Summary', headers=headers)
    assert r.status_code == 200


def test_get_download_summary_not_auth(client, app):
    """
    should respond with ok /api/v1/download/info/current/Summary
    """
    headers = {'Authorization': _login_bearer_token(client, app),
               'Content-Type': 'application/json'}
    os.environ["SUMMARY_PROJECT_NAME"] = 'FOOBAR'
    r = client.get('/api/v1/download/info/current/Summary', headers=headers)
    assert r.status_code == 401


def test_should_logout_ok(client, app):
    """
    should respond with ok /api/v1/auth/logout
    """
    headers = {'Authorization': _login_bearer_token(client, app),
               'Content-Type': 'application/json'}
    r = client.post('/api/v1/auth/logout', headers=headers)
    assert r.status_code == 200


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


def test_post_analysis_enrichment(client, app):
    """
    should respond with ok and response from dcc
    """
    headers = {'Authorization': _login_bearer_token(client, app),
               'Accept': 'application/json',
               'Content-Type': 'application/x-www-form-urlencoded'}
    form = dict([('sort', u'affectedDonorCountFiltered'),
                 ('params', u'{"maxGeneSetCount":50,"fdr":0.05,"universe":"REACTOME_PATHWAYS","maxGeneCount":50}'),  # NOQA
                 ('order', u'DESC'),
                 ('filters', u'{"gene":{"id":{"is":["ES:2d097244-2aac-4ae5-a428-7bff28adad46"]}}}')])  # NOQA
    r = client.post('/api/v1/analysis/enrichment', headers=headers,
                    data=form)
    assert r.status_code == 202


def test_post_analysis_enrichment_no_data(client, app):
    """
    should respond with ok and response from dcc
    """
    headers = {'Authorization': _login_bearer_token(client, app),
               'Accept': 'application/json',
               'Content-Type': 'application/x-www-form-urlencoded'}
    r = client.post('/api/v1/analysis/enrichment', headers=headers)
    assert r.status_code == 400


def test_post_analysis_enrichment_no_header(client, app):
    """
    should respond with ok and response from dcc
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.post('/api/v1/analysis/enrichment', headers=headers)
    assert r.status_code == 400


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


def test_genes_returns_ok(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    params = {'from': 1, 'include': 'facets', 'size': 25}
    filters = {"donor": {"projectId": {"is": ["BRCA-UK"]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params_filtered = {'from': 1, 'include': 'facets', 'size': 25,
                       'filters': filters}
    r = client.get('/api/v1/genes',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    assert r.json.keys() == [u'pagination', u'hits', u'facets']
    r_filtered = client.get('/api/v1/genes',
                            query_string=params_filtered, headers=headers)
    assert r_filtered.status_code == 200
    for i in range(len(r.json['hits'])):
        assert r.json['hits'][i] == r_filtered.json['hits'][i]


def test_genes_count_returns_ok(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {"gene": {"hasPathway": 'true'}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters}
    filters = {"gene": {"hasPathway": 'true'},
               "donor": {"projectId": {"is": [MY_PROJECT]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params_filtered = {'filters': filters}
    r = client.get('/api/v1/genes/count',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    r = int(r.json)
    r_filtered = client.get('/api/v1/genes/count',
                            query_string=params_filtered, headers=headers)
    assert r_filtered.status_code == 200
    r_filtered = int(r_filtered.json)
    assert r == r_filtered


def test_genes_mutations_counts(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters}
    filters = {"donor": {"projectId": {"is": [MY_PROJECT]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params_filtered = {'filters': filters}
    r = client.get('/api/v1/genes/{}/mutations/counts'.format(MY_GENE),
                   query_string=params, headers=headers)
    assert r.status_code == 200
    r_json = r.json
    r_filtered = client.get('/api/v1/genes/{}/mutations/counts'.format(MY_GENE),  # NOQA
                            query_string=params_filtered, headers=headers)
    assert r_filtered.status_code == 200
    assert r_json == r_filtered.json


def test_genesets_genes_counts(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/genesets/{}/genes/counts'.format(MY_GENESET), headers=headers)  # NOQA
    assert r.status_code == 200
    assert r.json[MY_GENESET] != 0


def test_bad_genesets_genes_counts(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    r = client.get('/api/v1/genesets/{}/genes/counts'.format('NOT_A_GENESET'), headers=headers)  # NOQA
    assert r.status_code == 200
    assert r.json['NOT_A_GENESET'] == 0


def test_mutations_returns_ok(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    params = {'from': 1, 'include': 'facets', 'size': 25}
    filters = {"donor": {"projectId": {"is": ["BRCA-UK"]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params_filtered = {'from': 1, 'include': 'facets', 'size': 25,
                       'filters': filters}
    r = client.get('/api/v1/mutations',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    assert r.json.keys() == [u'pagination', u'hits', u'facets']
    r_filtered = client.get('/api/v1/mutations',
                            query_string=params_filtered, headers=headers)
    assert r_filtered.status_code == 200
    for i in range(len(r.json['hits'])):
        assert r.json['hits'][i] == r_filtered.json['hits'][i]


def test_occurrences(client, app):
    """
    should respond with ok and response from dcc, with MY_PROJECT in results
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters}
    filters = {"donor": {"projectId": {"is": [MY_PROJECT]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params_filtered = {'filters': filters}
    r = client.get('/api/v1/occurrences',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    r_json = r.json
    r_filtered = client.get('/api/v1/occurrences',
                            query_string=params_filtered, headers=headers)
    assert r_filtered.status_code == 200
    assert r_json == r_filtered.json


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


def test_files_summary(client, app):
    """
    should respond with ok and response from dcc
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {"file": {"projectCode": {"is": ["BRCA-UK"]}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'from': 1, 'include': 'facets', 'size': 25}
    params_filtered = {'filters': filters, 'from': 1, 'include': 'facets',
                       'size': 25}
    r = client.get('/api/v1/repository/files/summary',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    assert r.json.keys() == [u'projectCount', u'totalFileSize', u'donorCount',
                             u'primarySiteCount', u'fileCount']
    r_filtered = client.get('/api/v1/repository/files/summary',
                            query_string=params_filtered, headers=headers)
    assert r_filtered.status_code == 200
    assert r_filtered.json.keys() == [u'projectCount', u'totalFileSize',
                                      u'donorCount', u'primarySiteCount',
                                      u'fileCount']
    for key in r.json.keys():
        assert r.json[key] == r_filtered.json[key]


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
    app.logger.debug(r.json)
    app.logger.debug(r.json['hits'])
    for hit in r.json['hits']:
        for donor in hit['donors']:
            assert donor['projectCode'] == MY_PROJECT
    assert r.json.keys() == [u'hits', u'termFacets', u'pagination']


def test_files_redacts_projects(client, app):
    """
    should respond with ok and response from dcc
    """
    headers = {'Authorization': _login_bearer_token(client, app)}
    filters = {}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters, 'from': 1, 'include': 'facets', 'size': 25}
    r = client.get('/api/v1/repository/files',
                   query_string=params, headers=headers)
    assert r.status_code == 200
    assert r.json.keys() == [u'hits', u'termFacets', u'pagination']
    app.logger.debug(r.json['termFacets']['projectCode'])
    for term in r.json['termFacets']['projectCode']['terms']:
        assert term['term'] == MY_PROJECT


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
    filters = {"mutation": {"functionalImpact": {"is": "High"}}}
    filters = urllib.quote_plus(json.dumps(filters))
    params = {'filters': filters}
    r = client.get('/api/v1/ui/search/gene-project-donor-counts/ENSG00000005339??',  # NOQA
                   query_string=params, headers=headers)  # NOQA
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


def test_get_manifests(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    url = '/api/v1/manifests?repos=collaboratory&format=tarball&filters={"file":{"id":{"is":"'+FILE_ID+'"}}}'  # NOQA
    r = client.get(url, headers=headers)
    assert r.status_code == 200


# @pytest.mark.skip(reason="no way of currently testing this")
def test_get_manifests_exacloud(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    # this file is actually in the BRCA repo,
    # (since the test user has access to that dir)
    # we've overridden the repo to force an exacloud response
    url = '/api/v1/manifests?repos=exacloud&format=tarball&filters={"file":{"id":{"is":"'+FILE_ID+'"}}}'  # NOQA
    r = client.get(url, headers=headers)
    assert r.status_code == 200
    # should only have one file
    assert r.data.count('scp $SCP_OPTS') == 1


def test_get_manifests_exacloud_nofind(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    # this file is actually in the BRCA repo,
    # (since the test user has access to that dir)
    # we've overridden the repo to force an exacloud response
    url = '/api/v1/manifests?repos=exacloud&format=tarball&filters={"file":{"id":{"is":"DUMMYFILEID"}}}'  # NOQA
    r = client.get(url, headers=headers)
    assert r.status_code == 400


def test_get_manifests_noauth(client, app):
    headers = {}
    url = '/api/v1/manifests?repos=collaboratory&format=tarball&filters={"file":{"id":{"is":"'+FILE_ID+'"}}}'  # NOQA
    r = client.get(url, headers=headers)
    assert r.status_code == 401


def test_get_dowload(client, app):
    headers = {'Authorization': _login_bearer_token(client, app)}
    url = '/api/v1/download?fn=/README.txt'
    r = client.get(url, headers=headers)
    assert r.status_code == 307
    assert r.headers['Location']


def test_get_dowload_no_auth(client, app):
    url = '/api/v1/download?fn=/README.txt'
    r = client.get(url)
    assert r.status_code == 401


def _login_bearer_token(client, app):
    global global_id_token
    return 'Bearer {}'.format(global_id_token)
