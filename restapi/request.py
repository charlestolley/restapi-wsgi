class HttpRequest:
    def __init__ (self, query="", headers={}, body=None):
        self.body = body
        self.headers = headers
        self.query = query
