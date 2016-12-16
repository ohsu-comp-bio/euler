#!/usr/bin/env python

"""
utilities to support eve
"""

from publisher import publish


def on_inserted(resource_name, items):
    publish(resource_name, items)
