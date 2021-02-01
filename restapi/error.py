from .http import CODES

class HttpError (BaseException):
    def __init__ (self, code=500, message=None):
        if message is None:
            message = CODES.get(code, "")

        self.code = code
        self.message = message
