"""**aspy** is a python module for making queries to ArchivesSpace much easier.

Links to schema and api reference

Compatibility
-------------
As of writing aspy has only been tested with ArchivesSpace 2.1.2 and Python 3.
YMMV with other versions.

Basic usage & setting up a connection to ArchivesSpace
------------------------------------------------------
At the heart of the module is the class `ArchivesSpace`. To set up a connection
create an ArchivesSpace with your login credentials, and run the `connect()`
method.

>>> from aspy import ArchivesSpace
>>> aspace = ArchivesSpace('http', 'localhost', '8089', 'admin', 'admin')
>>> aspace.connect()
>>> print(aspace.connection['user']['username'])
admin


Getting an object
-----------------

TODO

Getting listings and searches
-----------------------------

TODO

Posting an object
-----------------

TODO

Modifying an object
-------------------

TODO

"""
import requests
from string import Template
import json
import logging
import pprint
# Custom Error classes
class ConnectionError(Exception):
    pass
class BadRequestType(Exception):
    pass
class NotPaginated(Exception):
    pass
class AspaceBadRequest(Exception):
    pass
class AspaceForbidden(Exception):
    pass
class AspaceNotFound(Exception):
    pass
class AspaceError(Exception):
    pass

def logResponse(response):
    logging.error(json.dumps(response.json(), indent=4))

def checkStatusCodes(response):
    if response.status_code == 403:
        logging.error("Forbidden -- check your credentials.")
        logResponse(response)
        raise AspaceForbidden
    elif response.status_code == 400:
        logging.error("Bad Request -- I'm sorry Dave, I'm afraid I can't do that.")
        logResponse(response)
        raise AspaceBadRequest
    elif response.status_code == 404:
        logging.error("Not Found.")
        raise AspaceNotFound
    elif response.status_code == 500:
        logging.error("500 Internal Server Error")
        raise AspaceError
    elif response.status_code == 200:
        return response.json()
    else:
        logging.error(str(response.status_code))
        logResponse(response)
        raise AspaceError

def _unionRequestData(defaultData, kwargs):
    """Merge default request data and any data passed to the method into one
    unified set of data values to pass to ASpace for the request. Passed data
    overrides default data. Passed data is assumed to be in the form of a kwarg.
    
    >>> _unionRequestData({"foo": "bar"}, {"data": {"hello": "world"}})
    {'foo': 'bar', 'hello': 'world'}
    >>> _unionRequestData({"foo": "bar"}, {"data": {"foo": "world"}})
    {'foo': 'world'}
    >>> 
    """

    data = {}

    passedData = ""
    try:
        passedData = kwargs['data']
    except:
        pass

    # Merge
    data.update(defaultData)
    data.update(passedData)
    return data

class ArchivesSpace(object):
    """Base class for establishing a session with an ArchivesSpace repository,
    and doing API queries against it.
    
    >>> from aspy import ArchivesSpace
    >>> aspace = ArchivesSpace('http', 'localhost', '8089', 'admin', 'admin')
    >>> aspace.connect()
    >>> print(aspace.connection['user']['username'])
    admin
    """
    def __init__(self, protocol, domain, port, username, password):
        self.protocol = protocol
        self.domain = domain
        self.port = port
        self.username = username
        self.password = password
        self.session = None

    def _getHost(self):
        """Returns the host string containing the protocol domain name and port."""
        hostTemplate = Template('$protocol://$domain:$port')
        return hostTemplate.substitute(protocol = self.protocol, domain = self.domain, port = self.port)

    def _request(self, path, type, data):
        # Send the request
        try:
            if type == "post":
                data = json.dumps(data) # turn the data into json format for POST requests
                r = self.session.post(self._getHost() + path, data = data)
            elif type == "get":
                r = self.session.get(self._getHost() + path, data = data)
            else:
                raise BadRequestType
            
        except requests.exceptions.ConnectionError:
            logging.error('Unable to connect to ArchivesSpace. Check the host information.')
            raise ConnectionError
        else:
            jsonResponse = checkStatusCodes(r)
            return jsonResponse

    def requestPost(self, path, **kwargs):
        """Do a POST request to ArchivesSpace and return the JSON response"""
        data = ""
        try:
            data = kwargs['data']
        except:
            pass
        return self._request(path, 'post', data)

    def requestGet(self, path, **kwargs):
        """Do a GET request to ArchivesSpace and return the JSON response
        
        >>> from aspy import ArchivesSpace
        >>> aspace = ArchivesSpace('http', 'localhost', '8089', 'admin', 'admin')
        >>> aspace.connect()
        >>> jsonResponse = aspace.requestGet("/users/1")
        >>> jsonResponse['username']
        'admin'
        """
        data = ""
        try:
            data = kwargs['data']
        except:
            pass
        return self._request(path, 'get', data)
        
    def connect(self):
        """Start a sessions with ArchivesSpace. This must be done before anything else.

        >>> from aspy import ArchivesSpace
        >>> aspace = ArchivesSpace('http', 'localhost', '8089', 'admin', 'admin')
        >>> aspace.connect()
        >>> print(aspace.connection['user']['username'])
        admin
        """
        pathTemplate = Template('/users/$username/login')
        path = pathTemplate.substitute(username = self.username)

        # Use the requests Session class to handle the session
        # http://docs.python-requests.org/en/master/user/advanced/#session-objects
        self.session = requests.Session()

        try:
            response = self.session.post(self._getHost() + path, { "password" : self.password })
            jsonResponse = checkStatusCodes(response)
        except ConnectionError:
            logging.error("Couldn't authenticate.")
            exit(1)
        else:
            self.connection = jsonResponse # Save connection details as python data
            self.sessionId = self.connection['session']
            self.session.headers.update({ 'X-ArchivesSpace-Session' : self.sessionId })

    def pagedRequestGet(self, path, **kwargs):
        """Automatically request all the pages to build a complete data set"""

        data = _unionRequestData({"page": "1"}, kwargs)

        # Start a place to add the pages to as they come in
        fullSet = []
        # Get the first page
        response = self.requestGet(path, data=data)
        # Start the big data set
        try:
            fullSet = response['results']
        except Exception:
            raise NotPaginated
        # Then determine how many pages there are
        numPages = response['last_page']
        # Loop through all the pages and append them to a single big data structure
        for page in range(1, numPages):
            data = _unionRequestData({"page": str(page)}, kwargs)
            response = self.requestGet(path, data=data)
            fullSet.extend(response['results'])
        # Return the big data structure
        return fullSet

    def allIdsRequestGet(self, path):
        """Get a list of all of the IDs"""
        response = self.requestGet(path, data={"all_ids": True})
        # Expecting a list of ints, if it's not there's problem
        if all(isinstance(item, int) for item in response):
            return response
        else:
            raise NotPaginated

if __name__ == "__main__":
    import doctest
    print("Running tests...")
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=True)
