import requests
from string import Template

class aspaceRepo(object):
    def __init__(self, protocol, domain, port, username, password):
        self.protocol = protocol
        self.domain = domain
        self.port = port
        self.username = username
        self.password = password

    def getHost(self):
        """Returns the host string containing the protocol domain name and port."""
        hostTemplate = Template('$protocol://$domain:$port')
        return hostTemplate.substitute(protocol = self.protocol, domain = self.domain, port = self.port)

    def requestPost(self, path, data):
        """Do a POST request to ArchivesSpace and return the json response"""
        try:
            r = requests.post(self.getHost() + path, data = data)
        except requests.exceptions.ConnectionError:
            print('ERROR: Unable to connect to ArchivesSpace. Check the host information.')
        else:
            if r.status_code == 403:
                print("ERROR: Forbidden, check your credentials.")
            elif r.status_code == 200:
                return r.json()
            else:
                print("ERROR: " + r.status_code)

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
        jsonResponse = self.requestPost(path, { "password" : self.password })
        self.connection = jsonResponse
        self.sessionId = jsonResponse['session']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
