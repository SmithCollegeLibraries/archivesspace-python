import requests
from string import Template
import json

# Custom Error classes
class ConnectionError(Exception):
    pass

class aspaceRepo(object):
    def __init__(self, protocol, domain, port, username, password):
        self.protocol = protocol
        self.domain = domain
        self.port = port
        self.username = username
        self.password = password
        self.sessionId = None

    def getHost(self):
        """Returns the host string containing the protocol domain name and port."""
        hostTemplate = Template('$protocol://$domain:$port')
        return hostTemplate.substitute(protocol = self.protocol, domain = self.domain, port = self.port)

    def requestPost(self, path, data):
        """Do a POST request to ArchivesSpace and return the JSON response"""

        # If we're logged in, set the session hash in the header & JSONify the data
        if self.sessionId is not None:
            sessionHeader = { 'X-ArchivesSpace-Session' : self.sessionId }
            data = json.dumps(data)
        else:
            sessionHeader = ""

        # Send the request
        try:
            r = requests.post(self.getHost() + path, data = data, headers = sessionHeader)
        except requests.exceptions.ConnectionError:
            print('ERROR: Unable to connect to ArchivesSpace. Check the host information.')
            raise ConnectionError
        else:
            if r.status_code == 403:
                print("ERROR: Forbidden -- check your credentials.")
                print(r.text)
            elif r.status_code == 400:
                print("ERROR: Bad Request -- Your request sucks.")
                print(r.text)
            elif r.status_code == 200:
                return r.json()
            else:
                print("ERROR: " + str(r.status_code))
                print(r.text)

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
        try:
            jsonResponse = self.requestPost(path, { "password" : self.password })
        except ConnectionError:
            print("ERROR: Couldn't authenticate.")
        else:
            self.connection = jsonResponse
            self.sessionId = jsonResponse['session']

    def repositoriesPost(self, repo_code, name):
        """Create a repository
        >>> from aspy import aspaceRepo
        >>> repo = aspaceRepo('http', 'localhost', '8089', 'admin', 'admin')
        >>> repo.connect()
        >>> response = repo.repositoriesPost('FOOBAR5', 'Test repository made by aspy')
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
        
        jsonResponse = self.requestPost("/subjects", json.dumps(data))
        return(jsonResponse)

if __name__ == "__main__":
    import doctest
    print("Running tests...")
    doctest.testmod(optionflags=doctest.ELLIPSIS)
