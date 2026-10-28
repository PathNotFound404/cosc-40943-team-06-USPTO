"""The base of every component's exceptions (architecture 8.2.1)."""


class AppError(Exception):
    """A failure the user must act on.

    `message` is plain English and is shown to the user as it is, so it never
    contains a stack trace, a record, or office action text.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
