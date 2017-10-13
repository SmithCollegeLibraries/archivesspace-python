import requests
from string import Template
import json
import logging

# Custom Error classes
class ConnectionError(Exception):
    pass

class aspaceRepo(object):
    """Base class for establishing a session with an ArchivesSpace repository,
    and doing API queries against it.
    
    >>> from aspy import aspaceRepo
    >>> repo = aspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
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

    def requestPost(self, path, data):
        """Do a POST request to ArchivesSpace and return the JSON response"""

        # Send the request
        try:
            r = self.session.post(self.getHost() + path, data = json.dumps(data))
        except requests.exceptions.ConnectionError:
            logging.error('Unable to connect to ArchivesSpace. Check the host information.')
            raise ConnectionError
        else:
            if r.status_code == 403:
                logging.error("Forbidden -- check your credentials.")
                logging.error(r.text)
            elif r.status_code == 400:
                logging.error("Bad Request -- Your request sucks.")
                logging.error(r.text)
            elif r.status_code == 200:
                return r.json()
            else:
                logging.error(str(r.status_code))
                logging.error(r.text)

    def connect(self):
        """Start a sessions with ArchivesSpace. This must be done before anything else.
        >>> from aspy import aspaceRepo
        >>> repo = aspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
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
        except ConnectionError:
            logging.error("Couldn't authenticate.")
        else:
            self.connection = response.json() # Save connection details as python data
            self.sessionId = self.connection['session']
            self.session.headers.update({ 'X-ArchivesSpace-Session' : self.sessionId })

    def repositoriesPost(self, repo_code, name):
        """Create a repository
        >>> from aspy import aspaceRepo
        >>> repo = aspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
        >>> repo.connect()
        >>> response = repo.repositoriesPost('FOOBAR1', 'Test repository made by aspy')
        >>> response['uri']
        '/repositories/...'
        """
        jsonResponse = self.requestPost("/repositories", {"jsonmodel_type":"repository", "repo_code": repo_code, "name": name})
        return(jsonResponse)

    def subjectsPost(self):
        data = { "jsonmodel_type":"subject",
                "external_ids":[],
                "publish":True,
                "used_within_repositories":[],
                "used_within_published_repositories":[],
                "terms":[{ "jsonmodel_type":"term",
                "term":"Term 132",
                "term_type":"geographic",
                "vocabulary":"/vocabularies/156"}],
                "external_documents":[],
                "vocabulary":"/vocabularies/157",
                "authority_id":"http://www.example-596.com",
                "scope_note":"M911GA46",
                "source":"gmgpc"}
        
        jsonResponse = self.requestPost("/subjects", data)
        return(jsonResponse)

if __name__ == "__main__":
    import doctest
    print("Running tests...")
    doctest.testmod(optionflags=doctest.ELLIPSIS)
