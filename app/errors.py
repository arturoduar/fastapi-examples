"""Domain errors; main.py maps them to HTTP responses with exception handlers."""


class NotFoundError(Exception):
    def __init__(self, what: str, key):
        super().__init__(f"{what} {key!r} not found")


class DuplicateError(Exception):
    def __init__(self, what: str, key):
        super().__init__(f"{what} {key!r} already exists")
