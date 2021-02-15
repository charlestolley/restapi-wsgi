# Overview
There are a lot of web frameworks for Python: Django, CherryPy, Flask, and a bunch more that I'm not familiar with. However, if you are just looking to create a JSON-based REST API, these frameworks seem like overkill, and are not really convenient for designing anything other than dynamic web pages. This framework is meant to act as a minimally-invasive adapter for the Web Server Gateway Interface (WSGI), which is the Python standard for interacting with web servers. My original intention was simply to familiarize myself with the details of WSGI, and create a basic framework that I could keep in my back pocket to use on future projects, but I see no reason not to publish it as an open-source project. As of this writing, I have not used it for any serious projects, so it is altogether possible that it is missing major features. As such, I welcome constructive feedback about how it falls short, and suggestions for improvements.

This framework is written for Python 3; I do not intend to support Python 2. I personally use Linux for basically everything, and I know nothing about programming in Windows. I don't see any reason this framework would not work in Windows, and I am not opposed to making it Windows-friendly, but to date I have not tried it in Windows.

### Usage
The module-level `__init__.py` file only defines a handful of types: `API`, `HttpError`, `HttpRequest`, and `HttpResponse`.

Unlike many popular frameworks, which provide built-in web servers, if only for debugging use, this framework requires you to bring your own web server. The `API` class implements the client-side WSGI specification, meaning it should be compatible with most of the popular web servers: Apache using mod\_wsgi, Gunicorn, CherryPy, Nginx with uWSGI, and, again, probably a bunch more that I'm not familiar with. Each of these has its own documentation on how to set up a WSGI server. The example given later will demonstrate how to run the API framework with a CherryPy web server.

#### Defining Endpoints
The `API` class only has two functions that are intended for public use: `endpoint()`, and `wsgi()`. The latter allows you to register other WSGI applications as a sub-tree of your resource (URI) structure, and is called simply by providing the path string and the application object.

    application = restapi.API()
    application.wsgi("/path/for/other/application", other_application)

The `endpoint()` function has a similar signature, but instead of providing a WSGI application, the second argument is a class to handle all requests for that path. When the `API` receives a request, it will create an instance of the appropriate endpoint class, and then call the method corresponding to the type of request. Only four HTTP methods are currently allowed: GET, POST, PUT, and DELETE. For each method an endpoint class wishes to support, it should define a method of the same name, but in lowercase. For example, if an endpoint class wishes to support the HTTP GET method, it should define a function called `get()`. Each of these methods should expect a single argument (aside from `self`), which will be an `HttpRequest` object. The return value should be a JSON-encodable object (assuming you do not override the `API`'s encoder), in which case the response code will be given as 200, or else you can return an `HttpResponse` object, which allows you to use any response code, and/or return custom HTTP headers. Don't try to return `Content-Length` or `Content-Type`; those are handled by the `API`.

The `HttpError` class allows you to return error messages using Python's built-in exception mechanism. You can provide a status code, as well as an optional message. If you don't provide a message, the default message for the status code will be used. For example, if someone asks your server to brew it some coffee, just give 'em one of these:

    raise HttpError(418, "I'm a teapot")

The response will look like this

    HTTP/1.1 418
    Content-Length:44
    Content-Type: application/json
    # other headers from your web server

    {"message":"I'm a teapot","status_code":418}

If your code throws an exception somewhere and you don't handle it, it will trigger a 500 Internal Server Error response, and log a stack trace (if you have the Python `logging` module enabled).

The API does support the use of path variables by enclosing the variable name in angle brackets like so:

    application.endpoint("/resources/<id>", Resource)

Path variables are used as keyword arguments to the constructor of the endpoint class. The values are always given as strings. For the example above, the `Resource` class would look something like this:

    class Resource:
        def __init__ (self, id):
            self.id = id

        # other methods and stuff

As mentioned previously, the methods of the endpoint class (e.g. the `get()` method, for an HTTP GET) should expect a single argument of type `HttpRequest`. The `HttpRequest` class is a simple container for the request body (if any), the request headers, and the query string. The body (attribute name `body`) is either the JSON object (assuming you do not override the `API`'s decoder) provided in the request body, or `None`.  The headers (attribute name `headers`) are held in a `dict`. Note that, owing to the way the WSGI interface handles headers, any capitalization used by the client will be clobbered, and all headers will use a `Caplitalized-Dashed` format. This is only the case for incoming headers, meaning you may use whatever capitalization you like for the headers you provide to the `HttpResponse` object. The query string (attribute name `query`) is just the portion of the URL after the question mark, and is not handled or decoded in any special way.

#### Customization
The `API` object has three additional attributes that you may customize as needed. The first is the `handler` attribute, which formats an `HttpError` into an `HttpResponse` You may replace the default handler with your own object. The only requirement for this object is to provide a `handle()` function that accepts a single argument (which will be an `HttpError` object), and returns an `HttpResponse` object. The attributes of `HttpError` are called `code` and `message`. The `HttpResponse` constructor looks like this:

    class HttpResponse:
        __init__ (self, body, code=200, headers={}):
            # implementation

You may also replace the `encoder` and `decoder` attributes. The encoder is used for converting the response body object into a string. It has two requirements: it must have a `content_type` attribute with a valid `Content-Type` string value, and it must define an `encode()` function, which takes a single argument (the object to encode), and returns a string. The decoder must also define a `content_type` attribute, as well as a `decode()` function. This function takes a string as its only argument, and either returns the decoded object, or raises a 400 error. `decode()` will only be called with a non-empty string as the argument, as the `API` automatically uses `None` to represent an empty request body.

Perhaps you will notice that this encoder-decoder setup only allows one content type. That's correct. As mentioned before, I have not used my own framework for any real projects, so I don't yet know whether this shortcoming is of any real consequence. I welcome feedback from anyone who views this as a major handicap.

#### Example API with CherryPy Server
###### Server

    import restapi

    class Hello:
        def __init__ (self, first="World", last=None):
            self.first = first
            self.last = last

        def get (self, request):
            if self.last is not None:
                name = " ".join((self.first.capitalize(), self.last.capitalize()))
            else:
                name = self.first

            return {"message": "Hello {}!".format(name)}

    class Collection:
        def post (self, request):
            # save to a database or something
            # ...
            return restapi.HttpResponse(request.body, 201)

    if __name__ == '__main__':
        application = restapi.API()
        application.endpoint("/hello/world", Hello)
        application.endpoint("/hello/<first>/<last>", Hello)
        application.endpoint("/items", Collection)

        import cherrypy
        cherrypy.tree.graft(application, "/")
        cherrypy.engine.start()
        cherrypy.engine.block()

###### Client

    if __name__ == '__main__':
        import requests
        print(requests.get("http://localhost:8080/hello/world").json())
        print(requests.get("http://localhost:8080/hello/full/name").json())

        r = requests.post("http://localhost:8080/items", json={"type": "item", "id": 4})
        print(r.status_code)
        print(r.json())

###### Output

    {'message': 'Hello World!'}
    {'message': 'Hello Full Name!'}
    201
    {'type': 'item', 'id': 4}
