class Application:
    """Node-like wrapper for a WSGI application"""

    def __init__ (self, app):
        self.app = app

    def __call__ (self, environ, start_response):
        return self.app(environ, start_response)

    def add (self, name, child=None):
        msg = "Attempted to add \"{}\" to WSGI application path".format(name)
        raise ValueError(msg)

    @property
    def endpoint (self):
        return None

    def get (self, name):
        return None
