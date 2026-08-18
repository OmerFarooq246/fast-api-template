class ApplicationError(Exception):
    """Base class for expected errors that may be safely shown to clients."""

    code = "application_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ResourceNotFoundError(ApplicationError):
    code = "resource_not_found"

    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(f"{resource} {identifier!r} was not found")


class ResourceConflictError(ApplicationError):
    code = "resource_conflict"


class AuthenticationError(ApplicationError):
    code = "authentication_failed"


class AuthorizationError(ApplicationError):
    code = "authorization_failed"


class PersistenceError(ApplicationError):
    code = "persistence_error"

    def __init__(self, resource: str, operation: str) -> None:
        super().__init__(f"Unable to {operation} {resource}")
