#!/usr/bin/env python

import os
import bioschemas

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', '')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')
MONGO_DBNAME = os.environ.get('MONGO_DBNAME', 'test')

DEBUG = 'API_DEBUG' in os.environ
# Enable reads (GET), inserts (POST) and DELETE for resources/collections
# (if you omit this line, the API will default to ['GET'] and provide
# read-only access to the endpoint).
RESOURCE_METHODS = ['GET', 'POST', 'DELETE']

# Enable reads (GET), edits (PATCH) and deletes of individual items
# (defaults to read-only item access).
ITEM_METHODS = ['GET', 'PATCH', 'DELETE']

# We enable standard client cache directives for all resources exposed by the
# API. We can always override these global settings later.
CACHE_CONTROL = 'max-age=20'
CACHE_EXPIRES = 20

# make query parameters conform to GDC
# https://gdc-docs.nci.nih.gov/API/Users_Guide/Search_and_Retrieval/#components-of-a-request
# Default value for QUERY_MAX_RESULTS. Defaults to 25.
PAGINATION_DEFAULT = 10
# Key for the filters query parameter. Defaults to where.
QUERY_WHERE = 'filters'
# Key for the projections query parameter. Defaults to projection.
QUERY_PROJECTION = 'fields'


# not used
HATEOAS = False

# conform with GDC
API_VERSION = 'v0'

# important - we don't need to overly specify schemas
ALLOW_UNKNOWN = True

"""
Notes:
* Essentially a URI
* C(R)UD is routed to mongo collection 'file'
* (R)Search is routed to flask route aggregated_resource (no 'GET')
"""
file = {
    'description':
        """
        A set of related records (either written or electronic) kept together.
        (NCIt C42883).
        """,
    'schema': bioschemas.cerberus_schema('Resource'),
    'datasource': {
        'source': 'file',
    },
    'resource_methods': ['POST', 'DELETE', 'GET']
}


# TODO Remove after adding token to tests
PUBLIC_METHODS = ['GET', 'POST', 'PATCH', 'DELETE']
PUBLIC_ITEM_METHODS = ['GET', 'POST', 'PATCH', 'DELETE']

#
SCHEMA_ENDPOINT = 'schemas'

# not used
XML = False

# The DOMAIN dict explains which resources will be available and how they will
# be accessible to the API consumer.
DOMAIN = {
    'files': file,
}
