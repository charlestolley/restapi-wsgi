import json
import logging
import sys

from .node import Node
from .utils import LazySplit
from .wsgi import Application

log = logging.getLogger(__name__)

CHAR = "/"
CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
}

METHODS = set(["GET"])

class API:
    def __init__ (self):
        self.root = Node()

    def __call__ (self, environ, start_response):
        try:
            method = environ["REQUEST_METHOD"]
            if method not in METHODS:
                start_response("400 Bad Request", [])
                return [b'']

            endpoint = None
            node = self
            path = environ["PATH_INFO"]
            for start, end in LazySplit(path, CHAR):
                node = node.get(path[start:end])
                if isinstance(node, Application):
                    if end < len(path):
                        environ["SCRIPT_NAME"] += path[:end]
                        environ["PATH_INFO"] = path[end:]
                        return node(environ, start_response)
                    else:
                        break
                elif node is None:
                    break
            else:
                endpoint = node.endpoint

            if endpoint is None:
                start_response("404 Not Found", [])
                return [b'']

            resource = endpoint()
            try:
                func = getattr(resource, method.lower())
            except AttributeError:
                start_response("405 Method Not Allowed", [])
                return [b'']

            response = func()
            if (isinstance(response, tuple) and len(response) == 2 and
                                                isinstance(response[1], int)):
                response, code = response
            else:
                code = 200

            status = str(code)

            try:
                message = CODES[code]
            except KeyError:
                pass
            else:
                status += " " + message

            start_response(status, [])
            return [json.dumps(response).encode("latin-1")]

        except Exception as e:
            log.exception("Unhandled " + e.__class__.__name__)
            start_response("500 Internal Server Error", [], sys.exc_info())
            return [b'']

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
