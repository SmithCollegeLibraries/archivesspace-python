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

class AspaceRepo(object):
    """Base class for establishing a session with an ArchivesSpace repository,
    and doing API queries against it.
    
    >>> from aspy import AspaceRepo
    >>> repo = AspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
    >>> repo.connect()
    >>> print(repo.connection['user']['username'])
    admin
    """
    def __init__(self, protocol, domain, port, username, password):
        self.protocol = protocol
        self.domain = domain
        self.port = port
        self.username = username
        self.password = password
        self.session = None

    def getHost(self):
        """Returns the host string containing the protocol domain name and port."""
        hostTemplate = Template('$protocol://$domain:$port')
        return hostTemplate.substitute(protocol = self.protocol, domain = self.domain, port = self.port)

    def _request(self, path, type, data):
        # Send the request
        try:
            if type == "post":
                data = json.dumps(data) # turn the data into json format for POST requests
                r = self.session.post(self.getHost() + path, data = data)
            elif type == "get":
                r = self.session.get(self.getHost() + path, data = data)
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
        
        >>> from aspy import AspaceRepo
        >>> repo = AspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
        >>> repo.connect()
        >>> jsonResponse = repo.requestGet("/users/1")
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
        >>> from aspy import AspaceRepo
        >>> repo = AspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
        >>> repo.connect()
        >>> print(repo.connection['user']['username'])
        admin
        """
        pathTemplate = Template('/users/$username/login')
        path = pathTemplate.substitute(username = self.username)

        # Use the requests Session class to handle the session
        # http://docs.python-requests.org/en/master/user/advanced/#session-objects
        self.session = requests.Session()

        try:
            response = self.session.post(self.getHost() + path, { "password" : self.password })
            jsonResponse = checkStatusCodes(response)
        except ConnectionError:
            logging.error("Couldn't authenticate.")
            exit(1)
        else:
            self.connection = jsonResponse # Save connection details as python data
            self.sessionId = self.connection['session']
            self.session.headers.update({ 'X-ArchivesSpace-Session' : self.sessionId })

    def repositoriesPost(self, repo_code, name):
        """Example method to create a repository
        >>> from aspy import AspaceRepo
        >>> repo = AspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
        >>> repo.connect()
        >>> response = repo.repositoriesPost('FOOBAR8', 'Test repository made by aspy')
        >>> response['uri']
        '/repositories/...'
        """
        jsonResponse = self.requestPost("/repositories", data = {"jsonmodel_type":"repository", "repo_code": repo_code, "name": name})
        return(jsonResponse)

    def _getPagedRequest(self, path):
        fullSet = []
        # Get the first page
        response = self.requestGet(path, data={"page": "1"})
        # Start the big data set
        fullSet = response['results']
        # Then determine how many pages there are
        numPages = response['last_page']
        # Loop through all the pages and append them to a single big data structure
        for page in range(1, numPages):
            response = self.requestGet(path, data={"page": str(page)})
            fullSet.extend(response['results'])
        # Return the big data structure
        return fullSet

if __name__ == "__main__":
    import doctest
    print("Running tests...")
    doctest.testmod(optionflags=doctest.ELLIPSIS, verbose=True)
