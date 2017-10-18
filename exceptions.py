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
