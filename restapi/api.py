import json
import logging
import sys

log = logging.getLogger(__name__)

class Tree:
    def __init__ (self):
        self.root = {}

    def add (self, endpoint, path):
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        node = self.root

        start = 1
        while True:
            end = path.find("/", start)
            if end < 0:
                node[path[start:]] = endpoint
                break
            else:
                node = node.setdefault(path[start:end], {})
                start = end + 1

    def find (self, path):
        node = self.root
        for segment in path.split("/")[1:]:
            if isinstance(node, dict):
                try:
                    node = node[segment]
                except KeyError:
                    return
            else:
                return

        if not isinstance(node, dict):
            return node

CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
}

METHODS = set(["GET"])

class API:
    def __init__ (self):
        self.tree = Tree()

    def __call__ (self, environ, start_response):
        try:
            method = environ["REQUEST_METHOD"]
            if method not in METHODS:
                start_response("400 Bad Request", [])
                return [b'']

            endpoint = self.tree.find(environ["PATH_INFO"])
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
        self.tree.add(endpoint, path)
