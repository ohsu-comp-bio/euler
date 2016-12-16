
from swift.common.utils import get_logger
from swift.proxy.controllers.base import get_container_info
from swift.proxy.controllers.base import get_account_info, get_object_info
from swift.common.swob import Request, Response
import traceback
import requests
from json import dumps


class Euler(object):
    """
    Middleware that writes file create/update event to api/v0/files
    for dispersal to ['dcc', 'bmeg', ... ]
    """

    def __init__(self, app, conf, logger=None):
        self.app = app

        if logger:
            self.logger = logger
        else:
            self.logger = get_logger(conf, log_route='euler')

        self.api_url = conf.get('api_url')
        self.logger.debug("euler.api_url: {}".format(self.api_url))

    def __call__(self, env, start_response):
        """
        WSGI entry point.
        Wraps env in swob.Request object and passes it down.

        :param env: WSGI environment dictionary
        :param start_response: WSGI callable
        """

        if not env['REQUEST_METHOD'] in ('PUT', 'COPY', 'POST'):
            return self.app(env, start_response)

        response = None
        try:
            # complete the pipeline
            response = self.app(env, start_response)
            # we want to query the api after the file is stored
            # harvest container, account and object info
            container_info = get_container_info(
                env, self.app, swift_source='Euler')
            account_info = get_account_info(
                env, self.app, swift_source='Euler')
            object_info = get_object_info(env, self.app)
            # post useful data to euler api service
            from_env = ['REQUEST_METHOD', 'keystone.identity',
                        'keystone.token_info', 'PATH_INFO']
            self.logger.debug("euler.env: {}".format(env))
            to_api_env = {}
            for key in from_env:
                to_api_env[key] = env[key]
            to_api = {'type': 'swift_event',
                      'id': object_info['etag'],
                      'env': to_api_env,
                      'container': container_info,
                      'account': account_info,
                      'object': object_info}
            self.logger.debug("euler.to_api: {}".format(to_api))
            auth_token = to_api['env']['keystone.token_info']['token']['auth_token']  # NOQA
            headers = {'X-Auth-Token': auth_token}
            r = requests.post(self.api_url,  json=to_api, headers=headers)
            self.logger.debug("euler.api_response: {} {}".format(r, r.text))

        except:  # catch *all* exceptions
            tb = traceback.format_exc()
            self.logger.debug("euler.traceback: {}".format(tb))

        finally:
            # return unaltered upstream response
            return response


def filter_factory(global_conf, **local_conf):
    """
    paste.deploy app factory for creating WSGI proxy apps.
    """
    conf = global_conf.copy()
    conf.update(local_conf)

    def euler(app):
        return Euler(app, conf)
    return euler
