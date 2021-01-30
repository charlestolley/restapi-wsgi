import json
import logging
import sys

from .error import HTTPError
from .http import CODES
from .node import Node
from .utils import LazySplit
from .wsgi import Application

log = logging.getLogger(__name__)

CHAR = "/"
METHODS = set(["GET"])

def BadRequest (*args, **kwargs):
    return HTTPError(400, *args, **kwargs)

def NotFound (*args, **kwargs):
    return HTTPError(404, *args, **kwargs)

def MethodNotAllowerd (*args, **kwargs):
    return HTTPError(405, *args, **kwargs)

def InternalServerError (*args, **kwargs):
    return HTTPError(500, *args, **kwargs)

class DefaultHandler:
    def handle (self, exception):
        return {
            "message": exception.message,
            "status_code": exception.code,
        }, exception.code

class API:
    def __init__ (self):
        self.handler = DefaultHandler()
        self.root = Node()

    def __call__ (self, environ, start_response):
        try:
            try:
                return self.call(environ, start_response)

            except HTTPError as e:
                log.info("{}: {}".format(e.__class__.__name__, e.message))
                return self.respond(start_response, self.handler.handle(e))

        except:
            log.exception("Caught Exception while handling HTTPError")
            start_response(
                "500 Internal Server Error",
                [],
                exc_info=sys.exc_info()
            )

            return [b'']

    def call (self, environ, start_response):
        try:
            method = environ["REQUEST_METHOD"]
            if method not in METHODS:
                raise BadRequest("Unsupported method: \"{}\"".format(method))

            endpoint = None
            node = self
            path = environ["PATH_INFO"]
            for start, end in LazySplit(path, CHAR):
                if isinstance(node, Application):
                    split = start - len(CHAR)
                    environ["SCRIPT_NAME"] += path[:split]
                    environ["PATH_INFO"] = path[split:]
                    return node(environ, start_response)

                node = node.get(path[start:end])

                if node is None:
                    break
            else:
                endpoint = node.endpoint

            if endpoint is None:
                raise NotFound()

            resource = endpoint()
            try:
                func = getattr(resource, method.lower())
            except AttributeError:
                raise MethodNotAllowed()

            return self.respond(start_response, func())

        except Exception as e:
            log.exception("Unhandled " + e.__class__.__name__)
            raise InternalServerError()

    def respond (self, start_response, args, **kwargs):
        if isinstance(args, tuple):
            return self._respond(start_response, *args, **kwargs)
        else:
            return self._respond(start_response, args, **kwargs)

    def _respond (self, start_response, response, code=200, headers={}):
        start_response(
            "{} {}".format(code, CODES.get(code, "")),
            list(headers.items()),
        )

        return [json.dumps(response).encode("latin-1")]

    def endpoint (self, endpoint, path):
        node = self
        for start, end in LazySplit(path, CHAR):
            segment = path[start:end]
            child = node.get(segment)

            if child is None:
                child = node.add(segment)

            node = child

        node.endpoint = endpoint

    def wsgi (self, app, path):
        node = None
        child = self
        for start, end in LazySplit(path, CHAR):
            if child is None:
                child = node.add(name)

            node = child
            name = path[start:end]
            child = node.get(name)

        if child is not None:
            msg = "Cannot add WSGI application at \"{}\": {}".format(
                path,
                "path already in use by {}".format(
                    self.__class__.__name__
                )
            )

            raise ValueError(msg)

        if not name:
            msg = "Application path may not end in '{}'".format(CHAR)
            raise ValueError(msg)

        node.add(name, Application(app))

    def add (self, name, child=None):
        raise ValueError ("All paths must begin with '{}'".format(CHAR))

    def get (self, name):
        if name == "":
            return self.root
