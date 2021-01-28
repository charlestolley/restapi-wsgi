class HTTPError (BaseException):
    def __init__ (self, code=500, message=""):
        self.code = code
        self.message = message
