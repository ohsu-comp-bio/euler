
from swift.common.utils import get_logger
from swift.proxy.controllers.base import get_container_info
from swift.proxy.controllers.base import get_account_info, get_object_info
from swift.common.swob import Request, Response
import traceback


class Euler(object):
    """
    Middleware that writes file create/update event to kafka->dcc->bmeg
    """

    def __init__(self, app, conf, logger=None):
        self.app = app

        if logger:
            self.logger = logger
        else:
            self.logger = get_logger(conf, log_route='euler')

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
            self.logger.debug("env: {}".format(env))
            self.logger.debug("container_info: {}".format(container_info))

            account_info = get_account_info(
                env, self.app, swift_source='Euler')
            self.logger.debug("account_info: {}".format(account_info))

            object_info = get_object_info(
                env, self.app)
            self.logger.debug("object_info: {}".format(object_info))
        except:  # catch *all* exceptions
            tb = traceback.format_exc()
            self.logger.debug("traceback: {}".format(tb))

        finally:
            # unaltered upstream response
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
