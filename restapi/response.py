class HttpResponse:
    def __init__ (self, body, code=200, headers={}):
        self.body = body
        self.code = code
        self.headers = headers
