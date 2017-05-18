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
import manifest
import re
import uuid

assert 'PROXY_TARGET' in os.environ
PROXY_TARGET = os.environ['PROXY_TARGET']
NOT_FOUND = 404

# for _snake_case
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def _snake_case(name):
    """ camel case to snake case """
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def _is_sequence(arg):
    """ true if list """
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def _safe_set(t, tk, s, sk=None, make_snake=False):
    """ _safe_set(dest,'k1',source,'k2') # if k2 is source, set it.
       if k2 points to a single element vector, make it a scalar  """
    if not sk:
        sk = tk
    if s and sk in s:
        val = s[sk]
        if _is_sequence(val) and len(val) == 1:
            val = val[0]
        if make_snake:
            tk = _snake_case(tk)
        t[tk] = val


def datasets_get_one(id):
    url = _remote_url(url='/api/v1/entityset/{}?includeItems=true'.format(id))
    r = requests.get(url)
    entityset = r.json()
    """
    {
    "count": 0,
    "description": "foo description",
    "timestamp": 1493854922369,
    "subtype": "NORMAL",
    "state": "FINISHED",
    "version": 2,
    "items": [],
    "type": "FILE",
    "id": "fb0a58ec-8c8f-4246-a6e0-cb082780d190",
    "name": "foo name"
    }
    """
    file_ids = []
    attributes = {'attr': {'file_ids': {'values': file_ids}}}
    for item in entityset['items']:
        file_ids.append({"stringValue": item})
    dataset = {
        'id': entityset['id'],
        'name': entityset['name'],
        'description': entityset['description'],
        'attributes': attributes
    }
    return make_response(dumps(dataset))


def datasets_post():
    """
    facade create a dcc.entityset from a ga4gh.dataset
    """
    dataset = request.get_json()
    app.logger.debug(dataset)
    """
    {
      "attributes": {
        "attr": {
          "file_ids": {
            "values": [
              {
                "stringValue": "1"
              },
              {
                "stringValue": "2"
              }
            ]
          }
        }
      },
      "description": "foo description",
      "id": "foo",
      "name": "foo name"
    }
    """
    if 'attributes' in dataset and 'attr' in dataset['attributes']:
        attributes = dataset['attributes']['attr']
    file_ids = []
    if 'file_ids' in attributes:
        for attribute in attributes['file_ids']['values']:
            app.logger.debug(attribute.__class__)
            app.logger.debug(attribute)
            if 'stringValue' in attribute:
                file_ids.append(attribute['stringValue'])
    """
    https://localhost/api/v1/entityset/external
    {"filters":{"file":{"id":{"is":["FIffb3540a357a4c23611364d4cafa5d57","FIff8902a9dfebdb600b6b9e3ecfd7e999"]}}},"size":2,"type":"FILE","name":"test2","description":"","sortBy":"affectedDonorCountFiltered","sortOrder":"DESCENDING"}
    """
    entityset = {
      "filters": {
        "file": {
          "id": {
            "is": file_ids
          }
        }
      },
      "size": len(file_ids),
      "type": "FILE",
      "name": dataset['name'],
      "description": dataset['description'],
      "sortBy": "id",
      "sortOrder": "DESCENDING"
    }
    url = _remote_url(url='/api/v1/entityset/external')
    app.logger.debug(dumps(entityset))
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=dumps(entityset), headers=headers)
    return make_response(dumps({'id': r.json()['id']}))


def data_object_post():
    """
    facade:Implement ga4gh::data_objects POST using dcc backend
    * use api to fetch dependencies
    * however, the api does not have a way to create a file in repo
    therefore, create document directly in ES
    """

    data_object = request.get_json()
    app.logger.debug(data_object)

    # create a file centric document
    object_id = str(uuid.uuid4())
    file_centric = {
      "id": 'FI{}'.format(object_id.replace('-', '')),
      "object_id": object_id,
      "file_copies": [],
      "study": []
    }

    if 'submitted_id' in data_object:
        file_centric['submitted_id'] = data_object['submitted_id']

    info = data_object.get('info', None)
    _safe_set(file_centric, "analysisMethod", info, make_snake=True)
    _safe_set(file_centric, "referenceGenome", info, make_snake=True)
    _safe_set(file_centric, "study", info, make_snake=True)
    _safe_set(file_centric, "dataCategorization", info, make_snake=True)

    # fetch donors
    donor_keys = [
          "donorId",
          "otherIdentifiers",
          "primarySite",
          "projectCode",
          "sampleId",
          "specimenId",
          "specimenType",
          "study",
          "submittedDonorId",
          "submittedSampleId",
          "submittedSpecimenId"
        ]

    donors = []
    project_code = None
    sample_id = None
    for link in data_object.get('links', []):
        if link['rel'] == 'sample':
            sample_id = link['id']
    for link in data_object.get('links', []):
        if not link['rel'] == 'individual':
            continue
        url = _remote_url(url='/api/v1/donors/{}?include=specimen'
                              .format(link['id']))
        rsp = requests.get(url, allow_redirects=False)
        donor = rsp.json()
        app.logger.debug(donor)
        app.logger.debug(donor.keys())
        project_code = donor["projectId"]
        file_donor = {'donor_id': donor['id'],
                      'project_code': project_code,
                      "other_identifiers": {
                          "tcga_participant_barcode": None,
                          "tcga_sample_barcode": [],
                          "tcga_aliquot_barcode": []
                        }
                      }
        for key in donor.keys():
            if key in donor_keys:
                file_donor[_snake_case(key)] = donor[key]
        for specimen in donor['specimen']:
            for sample in specimen['samples']:
                if sample['id'] == sample_id:
                    file_donor['specimen_id'] = [specimen['id']]
                    file_donor['sample_id'] = [sample_id]
                    file_donor['study'] = sample['study']
                    file_centric['study'].append(sample['study'])
        donors.append(file_donor)
    file_centric['donors'] = donors

    for link in data_object.get('links', []):
        if not link['rel'] == 'project':
            continue
        project_code = link['id']

    url = _remote_url(url='/api/v1/projects/{}'
                          .format(project_code))
    rsp = requests.get(url, allow_redirects=False)
    app.logger.debug(url)
    app.logger.debug(rsp.json())
    repository_id = rsp.json()['repository'][0].lower()
    if repository_id == 'dbsnp':  # TODO dbsnp is not a repo id
        repository_id = 'cghub'

    url = _remote_url(url='/api/v1/repositories/{}'
                          .format(repository_id))
    rsp = requests.get(url, allow_redirects=False)
    repository = rsp.json()
    app.logger.debug(url)
    app.logger.debug(rsp.json())

    file_copy = {}

    file_centric['access'] = 'controlled'  # TODO - how to vary access level
    _safe_set(file_copy, "repoBaseUrl", repository, "baseUrl", make_snake=True)
    _safe_set(file_copy, "repoCode", repository, "code", make_snake=True)
    _safe_set(file_copy, "repoCountry", repository, "country", make_snake=True)
    _safe_set(file_copy, "repoDataPath", repository, "dataPath", make_snake=True)
    _safe_set(file_copy, "repoMetadataPath", repository, "metadataPath", make_snake=True)

    _safe_set(file_copy, "fileName", data_object, "file_name", make_snake=True)
    _safe_set(file_copy, "fileFormat", data_object, "mime_type", make_snake=True)
    _safe_set(file_copy, "fileMd5sum", data_object, "md5sum", make_snake=True)
    _safe_set(file_copy, "fileSize", data_object, "file_size", make_snake=True)
    _safe_set(file_copy, "lastModified", data_object, "created", make_snake=True)

    file_centric['file_copies'] = [file_copy]
    file_copy['repo_data_bundle_id'] = 'None'
    # we now have a document ready to write to the index
    app.logger.debug(file_centric)
    elastic_host = os.environ.get("ELASTIC_HOST", "dms-development")
    elastic_port = os.environ.get("ELASTIC_PORT", "8900")
    elastic_index = os.environ.get("ELASTIC_INDEX", "icgc-repository")
    elastic_host = "dms-development"
    elastic_port = "8900"

    url = 'http://{}:{}/{}/file-centric/{}'.format(
        elastic_host,
        elastic_port,
        elastic_index,
        file_centric['id']
    )

    r = requests.post(url, data=dumps(file_centric))
    app.logger.debug(url)
    app.logger.debug(r.status_code)
    app.logger.debug(r.text)

    url = 'http://{}:{}/{}/file-text/{}'.format(
        elastic_host,
        elastic_port,
        elastic_index,
        file_centric['id']
    )
    r = requests.post(url, data=dumps(
        {
          "type": "file",
          "id": file_centric['id'],
          "object_id": file_centric['object_id'],
          "file_name": [
            file_copy['file_name']
          ],
          "data_type": file_copy.get('file_format', ''),
          "donor_id": [
            donor['id']
          ],
          "project_code": [
            project_code
          ]
          # ,  "data_bundle_id": "82c009ee-0ec8-4811-bf7c-78b55a7b2fba"
        }
    ))
    app.logger.debug(url)
    app.logger.debug(r.status_code)
    app.logger.debug(r.text)

    return make_response(dumps(file_centric))


def data_object_get(id):
    """
    facade:Implement ga4gh::data_objects get using dcc backend
    use api to fetch
    """
    no_hits = dumps({})
    app.logger.debug(request.get_json())
    file_parameters = {}
    file_parameters['filters'] = {"file": {"id": {"is": [id]}}}
    url = _remote_url(params=file_parameters,
                      url='/api/v1/repository/files')
    rsp = requests.get(url, allow_redirects=False)
    app.logger.debug(rsp.text)
    if 'hits' in rsp.json() and len(rsp.json()['hits']) > 0:
        # create ga4gh data objects
        data_objects = []
        for hit in rsp.json()['hits']:
            data_objects.append(_make_data_object(hit))
        response = make_response(dumps(data_objects[0]))
        return response
    else:
        return make_response(no_hits, NOT_FOUND)


def data_object_search():
    """
    facade:Implement ga4gh::data_objects search using dcc backend
    use api to search & fetch
    """
    app.logger.debug(request.get_json())
    # ListDataObjectsRequest
    list_request = request.get_json()
    # &from=1&size=10&sort=id&order=desc
    default_size = 100
    # for no finds
    no_hits = dumps({'dataobjects': []})
    # file fetch parameters
    file_parameters = {'from': 1, 'size': default_size}
    if 'name_prefix' in list_request:
        # use the keyword api to find file ids
        # https://dcc.icgc.org/api/v1/keywords?from=1&q=41495b&size=5&type=file
        url = _remote_url(params={'from': 1,
                                  'q': list_request['name_prefix'],
                                  'type': 'file',
                                  'size': default_size},
                          url='/api/v1/keywords')
        rsp = requests.get(url, allow_redirects=False)
        app.logger.debug(rsp.text)
        # create a filter from the search results
        if 'hits' in rsp.json() and len(rsp.json()['hits']) > 0:
            ids = []
            for hit in rsp.json()['hits']:
                ids.append(hit['id'])
            file_parameters['filters'] = {"file": {"id": {"is": ids}}}
            # {"file":{"id":{"is":["FI9994","FI9974"]}}}
        else:
            return make_response(no_hits, NOT_FOUND)

    # use the filter to find the files
    # https://dcc.icgc.org/api/v1/repository/files?filters={"file":{"id":{"is":["FI9994","FI9974"]}}}&from=1&size=10&sort=id&order=desc
    url = _remote_url(params=file_parameters,
                      url='/api/v1/repository/files')
    rsp = requests.get(url, allow_redirects=False)
    app.logger.debug(url)
    app.logger.debug(rsp.text)
    if 'hits' in rsp.json() and len(rsp.json()['hits']) > 0:
        # create ga4gh data objects
        data_objects = []
        for hit in rsp.json()['hits']:
            data_objects.append(_make_data_object(hit))
        response = make_response(dumps(data_objects))
        return response
    else:
        return make_response(no_hits, NOT_FOUND)


def _make_data_object(hit):
    """ given a dcc repository file, create a ga4gh data object """
    do = {}
    repo_info = hit['fileCopies'][0]
    do['id'] = hit['id']

    _safe_set(do, 'file_name', repo_info, 'fileName')
    _safe_set(do, 'file_size', repo_info, 'fileSize')
    _safe_set(do, 'updated', repo_info, 'lastModified')
    _safe_set(do, 'md5sum', repo_info, 'fileMd5sum')
    _safe_set(do, 'mimeType', repo_info, 'fileFormat')
    _safe_set(do, 'dataset_id', repo_info, 'repoDataBundleId')
    do['urls'] = []
    for repo_info in hit['fileCopies']:
        app.logger.debug(repo_info)
        url = '{}{}{}'.format(
            repo_info.get('repoBaseUrl', ''),
            repo_info.get('repoDataPath', ''),
            repo_info.get('fileName', '')
        )
        do['urls'].append(url.replace('//', '/'))

    if 'analysisMethod' in hit and 'analysisType' in hit['analysisMethod']:
        provenance = {'operation': hit['analysisMethod']['software']}
        do['provenance'] = provenance

    links = []
    for donor in hit['donors']:
        links.append(
            {'rel': 'individual',
             'url': _remote_url(url='/api/v1/donors/{}'.format(donor['donorId'])),  # NOQA
             'mime_type': 'application/json'
             })
    links.append(
        {'rel': 'project',
         'url': _remote_url(url='/api/v1/projects/{}'.format(hit['donors'][0]['projectCode'])),  # NOQA
         'mime_type': 'application/json'
         })
    for repo_info in hit['fileCopies']:
        links.append(
            {'rel': 'repository',
             'url': _remote_url(url='/api/v1/repositories/{}'.format(repo_info['repoCode'])),  # NOQA
             'mime_type': 'application/json'
            })
    do['links'] = links

    info = {}
    for k in hit['donors'][0]:
        # skip fields already mapped
        if k in ['projectCode', 'donorId', 'analysisMethod']:
            continue
        info[k] = hit['donors'][0][k]
    for k in hit:
        # skip fields already mapped
        if k in ['donors', 'fileCopies', 'id']:
            continue
        info[k] = hit[k]
    do['info'] = info
    return do


def get_any(url):
    """
    Catch-All URL GET: Stream Proxy with Requests
    """
    remote_url = _remote_url()
    # Note: /api/browser/gene and /api/browser/mutation take differnet paths
    # through the client (h2 add Authentication header)
    # see dcc-portal-ui/app/vendor/scripts/genome-viewer/icgc-gene-adapter.js
    whitelist_paths = ['/api/version', '/api/v1/releases/current',
                       '/api/browser/gene', '/api/browser/mutation']
    auth_required = request.path not in whitelist_paths
    # if no whitelist_projects, abort
    _whitelist_projects(auth_required)
    req = requests.get(remote_url, stream=True)
    app.logger.debug('GET {} {}'.format(remote_url, req.status_code))
    # interesting example here ...
    # see http://www.programcreek.com/python/example/58918
    #        /flask.stream_with_context exec_query
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


def post_any(url):
    """
    Catch-All URL POST: Stream Proxy with Requests
    """
    remote_url = _remote_url()
    headers = {'Content-Type': 'application/json'}
    req = requests.post(remote_url, stream=True,
                        data=request.data, headers=headers,
                        allow_redirects=True)
    app.logger.debug('POST {} {}'.format(remote_url, req.status_code))
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'],
                    status=req.status_code)


def get_download():
    """ get the download redirect """
    remote_url = _remote_url()
    # if no whitelist_projects, abort
    _whitelist_projects(True)
    req = requests.get(remote_url, allow_redirects=False)
    # for testing without changes to portal-server
    # req.headers['Location'] = req.headers['Location'].replace('localhost:9090', 'local.compbio.ohsu.edu')  # NOQA
    # req.headers['Location'] = req.headers['Location'].replace('http:', 'https:')  # NOQA
    return make_response(("", req.status_code, req.headers.items()))


def post_analysis_enrichment():
    """ post to /analysis/enrichment """
    remote_url = _remote_url()
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/x-www-form-urlencoded'}
    app.logger.debug(request.form)
    req = requests.post(remote_url, stream=True,
                        data=request.form, headers=headers,
                        allow_redirects=True)
    app.logger.debug('POST {} {}'.format(remote_url, req.status_code))
    return Response(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'],
                    status=req.status_code)


def get_manifests():
    """ intercept exacloud repository, otherwise, pass to target """
    # create mutable dict
    params = _ensure_filters()
    # if this is exacloud, we create manifest
    if 'repos' in params and 'exacloud' in params.get('repos'):
        # must have project access
        def _check_projects(project_codes):
            whitelist_projects = _whitelist_projects(True)
            _abort_if_unauthorized(project_codes, whitelist_projects)
        return manifest.create(params, PROXY_TARGET, _check_projects)
    # otherwise, call PROXY_TARGET
    _whitelist_projects(True)
    return _call_proxy_target(params)


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
    url = _remote_url(params)
    app.logger.debug(url)
    remote_response = requests.get(url)
    # redact the response
    app.logger.debug(dumps(remote_response.json()))
    d = remote_response.json()
    if (
        'termFacets' in d and 'projectCode' in d['termFacets'] and
        'terms' in d['termFacets']['projectCode']
    ):
        # redact project list
        projects = d['termFacets']['projectCode']
        projects['terms'] = filter_(projects['terms'],
                                    lambda term: term['term']
                                    in whitelist_projects)
    # formulate response with redacted projects and original content type
    response = make_response(dumps(d))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    response.status_code = remote_response.status_code
    return response


def get_files_summary():
    """ apply project filter to files request
    /api/v1/repository/files/summary """
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
    if 'facets' in d and 'projectId' in d['facets']:
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
    response.status_code = remote_response.status_code
    return response


def get_genes(url):
    """ apply project filter to genes request /api/v1/genes  """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutatble dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)


def get_genes_count(url):
    """ apply project filter to genes request /api/v1/genes/count  """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutatble dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)


def get_genes_mutations_counts(url, geneIds):
    """
    apply project filter to /api/v1/genes/<path:geneIds>/mutations/counts
    """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutable dict
    params = _ensure_filters()
    # if no project_codes are passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)


def get_genesets_genes_counts(url, geneSetIds):
    """
    apply project filter to request /api/v1/geneset/{geneSetId}/genes/counts
    """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutatble dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call the remote
    url = url + geneSetIds + '/genes/counts'
    remote_response = requests.get(_remote_url(params))
    d = remote_response.json()
    response = make_response(dumps(d))
    response.headers['Content-Type'] = remote_response.headers['content-type']
    response.status_code = remote_response.status_code
    return response


def get_mutations(url):
    """ apply project filter to mutations request /api/v1/mutations """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutatble dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)


def get_occurrences(url):
    """ apply project filter to occurrences request /api/v1/occurrences """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    # create mutable dict
    params = _ensure_filters()
    # if no project_codes passed, set it to whitelist
    params, project_codes = _ensure_donor_project_ids(params,
                                                      whitelist_projects)
    # unauthorized if project_codes not subset of whitelist
    _abort_if_unauthorized(project_codes, whitelist_projects)
    # call PROXY_TARGET
    return _call_proxy_target(params)


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


def get_download_info_current_summary(release):
    """ get the download redirect """
    # if no whitelist_projects, abort
    whitelist_projects = _whitelist_projects(True)
    summary_project = None
    if "SUMMARY_PROJECT_NAME" in os.environ:
        summary_project = os.environ["SUMMARY_PROJECT_NAME"]
        intersection = list(set([summary_project])
                            .intersection(whitelist_projects))
        if len(intersection) > 0:
            # call PROXY_TARGET
            return _call_proxy_target()
    # return 200, with dummy file entry
    na = [{'name': 'Not authorized', 'type': 'f', 'size': 0}]
    response = make_response(dumps(na))
    response.headers['Content-Type'] = 'application/json'
    return response


# Private util functions ########################################

def _ensure_project_codes(params, whitelist_projects):
    """ set project code filter, returns project codes and updated params """
    project_codes = deep_get(params, 'filters.project.id.is')
    if project_codes:
        intersection = list(set(project_codes)
                            .intersection(whitelist_projects))
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
        return _remote_url_params(params, url)
    if url:  # pragma nocoverage
        return "{}{}".format(PROXY_TARGET, url)
    return "{}{}".format(PROXY_TARGET, request.full_path)


def _remote_url_params(params, url=None):
    """
    format a url for the configured remote host, using passed param dict
    """
    if 'filters' in params:
        filters = params['filters']
        params['filters'] = dumps(filters)
    query = urllib.urlencode(params)
    if not url:
        url = request.path
    url = "{}{}?{}".format(PROXY_TARGET, url, query)
    app.logger.debug('url {}'.format(url))
    return url
