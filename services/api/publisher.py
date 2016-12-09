#!/usr/bin/env python

from flask import current_app as app

"""
publish item to other sinks [kafka,elastic]
"""


def publish(resource_name, items):
    """ send to downstream sink, return http status and json message"""
    # TODO - add kafka
    app.logger.debug('resource: {} items: {}'.format(resource_name, items))
