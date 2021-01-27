import json
import logging
import sys

from .node import Node
from .utils import LazySplit

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
            node = self.root
            path = environ["PATH_INFO"]
            for start, end in LazySplit(path, CHAR):
                node = node.get(path[start:end])
                if node is None:
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
        node = self.root
        for start, end in LazySplit(path, CHAR):
            segment = path[start:end]
            child = node.get(segment)

            if child is None:
                child = node.add(segment)

            node = child

        node.endpoint = endpoint
