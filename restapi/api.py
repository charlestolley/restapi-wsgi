import json
import logging
import sys

from .error import HttpError
from .http import CODES
from .node import Node
from .request import HttpRequest
from .response import HttpResponse
from .utils import LazySplit
from .wsgi import Application

log = logging.getLogger(__name__)

CHAR = "/"
METHODS = set(["DELETE", "GET", "POST", "PUT"])

class DefaultDecoder:
    def __init__ (self):
        self.content_type = "application/json"

    def decode (self, body):
        try:
            return json.loads(body)
        except json.decoder.JSONDecodeError:
            raise HttpError(400, "Invalid request body")

class DefaultEncoder:
    def __init__ (self):
        self.content_type = "application/json"

    def encode (self, obj):
        return json.dumps(obj, separators=(",",":"))

class DefaultHandler:
    def handle (self, exception):
        return HttpResponse (
            {
                "message": exception.message,
                "status_code": exception.code,
            },
            exception.code
        )

class API:
    def __init__ (self):
        self.decoder = DefaultDecoder()
        self.encoder = DefaultEncoder()
        self.handler = DefaultHandler()
        self.root = Node()

    def __call__ (self, environ, start_response):
        try:
            try:
                return self.call(environ, start_response)

            except HttpError as e:
                log.info("{}: {}".format(e.__class__.__name__, e.message))
                return self.respond(start_response, self.handler.handle(e))

        except:
            log.exception("Caught Exception while handling HttpError")
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
                raise HttpError(400, "Unknown HTTP Method")

            endpoint = None
            args = []

            node = self
            path = environ.get("PATH_INFO", "")
            for start, end in LazySplit(path, CHAR):
                if isinstance(node, Application):
                    split = start - len(CHAR)

                    try:
                        environ["SCRIPT_NAME"] += path[:split]
                    except KeyError:
                        environ["SCRIPT_NAME"] = path[:split]

                    environ["PATH_INFO"] = path[split:]
                    return node(environ, start_response)

                node = node.get(path[start:end])
                if node is None:
                    break
                elif hasattr(node, "value"):
                    args.append(node.value)
            else:
                endpoint = node.endpoint

            if endpoint is None:
                raise HttpError(404)

            resource = endpoint(*args)

            try:
                process = getattr(resource, method.lower())
            except AttributeError:
                raise HttpError(405)

            headers = {}
            for var in environ:
                if not var.startswith("HTTP_"):
                    continue

                words = [word.capitalize() for word in var.split("_")[1:]]
                header = "-".join(words)
                headers[header] = environ[var]

            kwargs = {}

            try:
                kwargs["query"] = environ["QUERY_STRING"]
            except KeyError:
                pass

            stream = environ["wsgi.input"]
            char = stream.read(1)

            if char:
                content_type = environ.get("CONTENT_TYPE")
                if content_type and content_type != self.decoder.content_type:
                    raise HttpError(400, "Unsupported Content-Type")

                kwargs["body"] = self.decoder.decode(char + stream.read())

            request = HttpRequest(headers=headers, **kwargs)
            return self.respond(start_response, process(request))

        except Exception as e:
            log.exception("Unhandled " + e.__class__.__name__)
            raise HttpError(500)

    def respond (self, start_response, response):
        if not isinstance(response, HttpResponse):
            response = HttpResponse(response)

        try:
            status = "{} {}".format(response.code, CODES[response.code])
        except KeyError:
            status = str(response.code)

        headers = list(response.headers.items())
        body = self.encoder.encode(response.body).encode("latin-1")
        headers.append(("Content-Length", str(len(body))))

        try:
            headers.append(("Content-Type", self.encoder.content_type))
        except AttributeError:
            pass

        start_response(status, headers, exc_info=sys.exc_info())
        return [body]

    def endpoint (self, path, endpoint):
        node = self
        for start, end in LazySplit(path, CHAR):
            segment = path[start:end]
            child = node.get(segment)

            if child is None:
                child = node.add(segment)

            node = child

        node.endpoint = endpoint

    def wsgi (self, path, app):
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
