from ast import Return
import contextlib
from datetime import time
import re
from typing import Callable, Optional
from loguru import logger


class _MISSINGSlient():
    def __bool__(self):
        return False


MISSING = _MISSINGSlient()


def sint(val):
    return int(val) if val else 0


def parse_entrytime(et: str, index: int):
    if et is MISSING:
        return time()

    et = et.strip()
    if not et or et.lower() == 'nt':
        return time()
    match = re.fullmatch(
        r'((?P<hour>\d{2}):)?(?P<min>\d{2}):(?P<sec>\d{2})[:.](?P<hsec>\d{2})', et)
    if not match:
        logger.warning(
            f'[{index}]: Игнорирование времени из-за сбоя обработки ({et})')
        return time()
    try:
        return time(
            sint(match.group('hour')),
            sint(match.group('min')),
            sint(match.group('sec')),
            sint(match.group('hsec'))*10_000
        )
    except Exception as err:
        logger.warning(
            f'[{index}]: Игнорирование времени из-за сбоя обработки ({err};{et})')
        return time()


class RowValidate:
    name: str
    parser: Callable = lambda _, v: v
    n: int
    __is_index: bool = False
    __rows = []

    def __init__(
        self,
        name: str,
        parser: Callable = None,
        silent: bool = False
    ):
        self.name = name
        self.silent = silent
        if parser is not None:
            if hasattr(parser, '__annotations__') and 'index' in parser.__annotations__:
                self.__is_index = True
            self.parser = parser
        self.__rows.append(self)

    def _parse_value(self, value, index):
        kwargs = {}
        if self.__is_index:
            kwargs['index'] = index
        return self.parser(value, **kwargs)

    @classmethod
    def _init_config(cls, config: dict[str, int]):
        for row in cls.__rows:
            row.n = config[row.name]


class Row:
    lastname: str = RowValidate('lastname')
    firstname: str = RowValidate('firstname')
    gender: str = RowValidate('gender')
    license: Optional[str] = RowValidate(
        'license', lambda item: item or None, True)
    birthday: str = RowValidate('birthday')
    club: str = RowValidate('club')
    stroke: str = RowValidate('stroke')
    distance: int = RowValidate('distance', int)
    entrytime: time = RowValidate('entrytime', parse_entrytime, True)
    middlename: Optional[str] = RowValidate(
        'middlename', lambda item: item or None, True)
    lane: Optional[int] = RowValidate(
        'lane', lambda item: int(item) if item else None, True)
    heat: Optional[int] = RowValidate(
        'heat', lambda item: int(item) if item else None, True)

    parsers = {
        str: lambda _, v: v
    }

    @classmethod
    def _init_row(cls, sheet, row, index):
        self = cls()
        row = list(row)

        for i, v in enumerate(row):
            if isinstance(v, str) and v.startswith('='):
                with contextlib.suppress(Exception):
                    row[i] = sheet[v.removeprefix('=')].value

        for name, item in cls.__dict__.items():
            if not isinstance(item, RowValidate):
                continue
            if item.n == -1:
                setattr(
                    self, name, MISSING if not item.silent else item._parse_value(MISSING, index))
            else:
                setattr(self, name, item._parse_value(row[item.n], index))
        return self

    def __repr__(self):
        values = []
        for name, item in type(self).__dict__.items():
            if not isinstance(item, RowValidate):
                continue
            values.append(f'{name}={repr(getattr(self, name))}')
        return f"<Row {' '.join(values)}>"
