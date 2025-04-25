

class RegisteredError(Exception):
    pass


class IncorrectError(RegisteredError, ValueError):
    pass


class IncorrectDistance(IncorrectError):
    def __init__(self, value: str):
        super().__init__(f'No distances found by parameters {value}')


class IncorrectGender(IncorrectError):
    def __init__(self, value: str):
        super().__init__(f'There is no gender for the value of {value}')


class IncorrectAge(IncorrectError):
    def __init__(self, value: str):
        super().__init__(f'There is no birthday for the value of {value}')


class ParseError(RegisteredError):
    def __init__(self, row: int):
        super().__init__(f'An error occurred in row {row}')
