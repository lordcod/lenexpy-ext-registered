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
    if isinstance(et, time):
        return et

    et = et.strip()
    if not et or et.lower() == 'nt':
        return time()
    match = re.fullmatch(
        r'((?P<hour>\d{1,2}):)?(?P<min>\d{2}):(?P<sec>\d{1,2})[:.,](?P<hsec>\d{2})', et)
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


def validate_name_event(name):
    if not isinstance(name, str):
        raise ValueError('Type is not str')
    match = re.fullmatch(r'(\d+)(.+)', name)
    distance, code = match.groups()
    return int(distance), code


def parse_events(item: str, index: int):
    splits = item.split()
    events = []
    i = 0
    while i < len(splits):
        try:
            name, entrytime = splits[i], splits[i+1]
        except IndexError:
            name, entrytime = splits[i], time()
        distance, code = validate_name_event(name)

        try:
            validate_name_event(entrytime)
        except Exception:
            if isinstance(entrytime, str):
                entrytime = entrytime.strip('()')
            entrytime = parse_entrytime(entrytime, index)
            i += 2
        else:
            entrytime = time()
            i += 1

        events.append((distance, code, entrytime))
    return events


def parse_splits(i):
    def wrap(item: str):
        try:
            return item.split()[i]
        except IndexError:
            return
    return wrap


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


def parse_coachname(value: str):
    if not value:
        return []

    def filter_func(i):
        return i.strip() not in ('...', '')

    return list(set(
        map(str.strip,
            filter(filter_func,
                   value.split('  ')))
    ))


class Row:
    lastname: str = RowValidate('lastname', parse_splits(0))
    firstname: str = RowValidate('firstname', parse_splits(1))
    middlename: Optional[str] = RowValidate(
        'middlename', parse_splits(2))
    gender: str = RowValidate('gender', parse_splits(1))
    license: Optional[str] = RowValidate(
        'license', lambda item: item or None, True)
    birthday: str = RowValidate('birthday', parse_splits(0))
    club: str = RowValidate('club')
    event: list = RowValidate('event', parse_events)
    coachname: list[str] = RowValidate('coachname', parse_coachname)

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


if __name__ == '__main__':
    config = {
        "lastname": 0,
        "firstname": 1,
        "middlename": 2,
        "birthday": 5,
        "gender": 3,
        "club": 8,
        "license": 4,
        "stroke": 9,
        "distance": 10,
        "entrytime": 12,
        "lane": -1,
        "heat": -1
    }
    values = {}
    for name, item in Row.__dict__.items():
        if not isinstance(item, RowValidate):
            continue
        values[name] = config.get(name, -1)
    print(values)
