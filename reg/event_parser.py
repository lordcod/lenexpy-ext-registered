from datetime import date, time
import random
from typing import List, Optional, Tuple
from loguru import logger
from reg.athlete_parser import BaseData
from reg.exceptions import IncorrectAge, IncorrectDistance
from reg.issues import IssueCollector
from reg.row_types import Row, RowValidate
from lenexpy.models.lenex import Lenex
from lenexpy.models.agegroup import AgeGroup
from lenexpy.models.event import Event
from lenexpy.models.athelete import Athlete
from lenexpy.models.entry import Entry, Status as EntryStatus
from lenexpy.models.heat import Heat, StatusHeat
from lenexpy.ext.basetime import BaseTime

bt = BaseTime.null()
bt.data = {('LCM', 'M', 50, 'FREE'): 20.91, ('LCM', 'M', 100, 'FREE'): 46.86, ('LCM', 'M', 200, 'FREE'): 102, ('LCM', 'M', 400, 'FREE'): 220.07, ('LCM', 'M', 800, 'FREE'): 452.12, ('LCM', 'M', 1500, 'FREE'): 871.02, ('LCM', 'M', 50, 'BACK'): 23.55, ('LCM', 'M', 100, 'BACK'): 51.6, ('LCM', 'M', 200, 'BACK'): 111.92, ('LCM', 'M', 50, 'BREAST'): 25.95, ('LCM', 'M', 100, 'BREAST'): 56.88, ('LCM', 'M', 200, 'BREAST'): 125.48, ('LCM', 'M', 50, 'FLY'): 22.27, ('LCM', 'M', 100, 'FLY'): 49.45, ('LCM', 'M', 200, 'FLY'): 110.34, ('LCM', 'M', 200, 'MEDLEY'): 114, ('LCM', 'M', 400, 'MEDLEY'): 242.5, ('LCM', 'F', 50, 'FREE'): 23.61, ('LCM', 'F', 100, 'FREE'): 51.71, ('LCM', 'F', 200, 'FREE'): 112.85, ('LCM', 'F', 400, 'FREE'): 235.38, ('LCM', 'F', 800, 'FREE'): 484.79, ('LCM', 'F', 1500, 'FREE'): 920.48, ('LCM', 'F', 50, 'BACK'): 26.86, ('LCM', 'F', 100, 'BACK'): 57.33, ('LCM', 'F', 200, 'BACK'): 123.14, ('LCM', 'F', 50, 'BREAST'): 29.16, ('LCM', 'F', 100, 'BREAST'): 64.13, ('LCM', 'F', 200, 'BREAST'): 137.55, ('LCM', 'F', 50, 'FLY'): 24.43, ('LCM', 'F', 100, 'FLY'): 55.48, ('LCM', 'F', 200, 'FLY'): 121.81, ('LCM', 'F', 200, 'MEDLEY'): 126.12, ('LCM', 'F', 400, 'MEDLEY'): 265.87, ('SCM', 'M', 50, 'FREE'): 20.16,
           ('SCM', 'M', 100, 'FREE'): 44.84, ('SCM', 'M', 200, 'FREE'): 99.37, ('SCM', 'M', 400, 'FREE'): 212.25, ('SCM', 'M', 800, 'FREE'): 440.46, ('SCM', 'M', 1500, 'FREE'): 846.88, ('SCM', 'M', 50, 'BACK'): 22.11, ('SCM', 'M', 100, 'BACK'): 48.33, ('SCM', 'M', 200, 'BACK'): 105.63, ('SCM', 'M', 50, 'BREAST'): 24.95, ('SCM', 'M', 100, 'BREAST'): 55.28, ('SCM', 'M', 200, 'BREAST'): 120.16, ('SCM', 'M', 50, 'FLY'): 21.75, ('SCM', 'M', 100, 'FLY'): 47.78, ('SCM', 'M', 200, 'FLY'): 106.85, ('SCM', 'M', 200, 'MEDLEY'): 109.63, ('SCM', 'M', 400, 'MEDLEY'): 234.81, ('SCM', 'M', 100, 'MEDLEY'): 49.28, ('SCM', 'F', 50, 'FREE'): 22.93, ('SCM', 'F', 100, 'FREE'): 50.25, ('SCM', 'F', 200, 'FREE'): 110.31, ('SCM', 'F', 400, 'FREE'): 231.3, ('SCM', 'F', 800, 'FREE'): 477.42, ('SCM', 'F', 1500, 'FREE'): 908.24, ('SCM', 'F', 50, 'BACK'): 25.25, ('SCM', 'F', 100, 'BACK'): 54.89, ('SCM', 'F', 200, 'BACK'): 118.94, ('SCM', 'F', 50, 'BREAST'): 28.37, ('SCM', 'F', 100, 'BREAST'): 62.36, ('SCM', 'F', 200, 'BREAST'): 134.57, ('SCM', 'F', 50, 'FLY'): 24.38, ('SCM', 'F', 100, 'FLY'): 54.05, ('SCM', 'F', 200, 'FLY'): 119.61, ('SCM', 'F', 200, 'MEDLEY'): 121.86, ('SCM', 'F', 400, 'MEDLEY'): 258.94, ('SCM', 'F', 100, 'MEDLEY'): 56.51}


def get_only_time(entrytime: time):
    return (
        entrytime.hour*60*60
        + entrytime.minute * 60
        + entrytime.second
        + entrytime.microsecond / 1000000
    )


def sum_age_groups(agegroups: List[AgeGroup]):
    if not agegroups:
        return -1, -1
    amax, amin = None, None
    for group in agegroups:
        if amax is None or ((group.agemax > amax or group.agemax == -1) and amax != -1):
            amax = group.agemax
        if amin is None or ((group.agemin < amin or group.agemin == -1) and amin != -1):
            amin = group.agemin
    return amin, amax


def get_swimstyles(lenex: Lenex):
    events = {}
    for session in lenex.meet.sessions:
        for event in session.events:
            key = (event.gender,
                   event.swimstyle.stroke,
                   event.swimstyle.distance)
            events.setdefault(key, [])
            events[key].append((
                sum_age_groups(event.agegroups),
                event
            ))
    return events


def get_age(athlete: Athlete) -> int:
    return date.today().year-athlete.birthdate.year


def check_age(age: int, minage: int, maxage: int):
    if minage == -1 and maxage == -1:
        return True
    if age <= maxage and minage == -1:
        return True
    if age >= minage and maxage == -1:
        return True
    return minage <= age <= maxage


heats = {}


class RowParser:
    def __init__(
        self,
        row: Row,
        i: int,
        lenex: Lenex,
        config: dict,
        basedata: BaseData,
        collector: IssueCollector | None = None
    ):
        self.row = row
        self.i = i
        self.lenex = lenex
        self.config = config
        self.basedata = basedata
        self.events = get_swimstyles(lenex)
        self.collector = collector

    def _serialize_row(self):
        """Return plain dict of row fields for UI-friendly formatting."""
        data = {}
        for name, item in type(self.row).__dict__.items():
            if not isinstance(item, RowValidate):
                continue
            value = getattr(self.row, name, None)
            data[name] = value
        return data

    def _add_issue(self, category: str, message: str, *, level: str = "warning", extra: dict | None = None):
        if self.collector is None:
            return
        self.collector.add(
            category=category,
            message=message,
            level=level,
            row_index=self.i,
            row_repr=repr(self.row),
            row_data=self._serialize_row(),
            extra=extra or {},
        )

    def parse(self):
        self.athlete = self.basedata.get(self.row)

        self.stroke = self.config['reversed_styles'][self.row.stroke.strip(
        ).lower()]
        event, status = self.find_event()

        self.entrytime = self.validate_entrytime()

        if self.row.heat and self.row.lane:
            key = (event, self.athlete.gender, self.row.heat)
            if not (heatid := heats.get(key)):
                heatid = random.randint(1000, 10_000)
                heats[key] = heatid
                heat = Heat(
                    heatid=heatid,
                    number=self.row.heat,
                    order=self.row.heat,
                    status=StatusHeat.SEEDED
                )
                if not event.heats:
                    event.heats = []
                event.heats.append(heat)
        else:
            heatid = None

        entry = Entry(
            eventid=event.eventid,
            entrytime=self.entrytime,
            status=status
        )
        if heatid and self.row.lane:
            entry.heatid = heatid
            entry.lane = self.row.lane

        self.athlete.entries.append(entry)

    def find_event(self) -> Tuple[Event, Optional[EntryStatus]]:
        try:
            events = self.events[(self.athlete.gender,
                                  self.stroke, self.row.distance)]
        except KeyError:
            message = f"No distances found by parameters {self.athlete.gender}, {self.stroke}, {self.row.distance}"
            self._add_issue("incorrect_distance", message, level="error")
            raise IncorrectDistance(message)

        if len(events) == 0:
            message = f"No distances found by parameters {self.athlete.gender}, {self.stroke}, {self.row.distance}"
            self._add_issue("incorrect_distance", message, level="error")
            raise IncorrectDistance(message)

        for (min, max), e in events:
            if check_age(get_age(self.athlete), min, max):
                return e, None

        if not self.config.get('exh', True):
            message = 'The EXH is disabled and the age is not appropriate'
            self._add_issue("age_exh", message, level="error")
            raise IncorrectAge(message)

        event = events[0]
        if len(events) > 1:
            logger.warning(
                f'[{self.i}]: Было найдено несколько одинаковых дистанций для EXH')

        logger.warning(
            f'[{self.i}]: {self.athlete.firstname} {self.athlete.lastname} {get_age(self.athlete)}, участвует в забеге со статусом EXH, потому что он не подходит для возраста ({event[0][0]}-{event[0][1]})')
        self._add_issue(
            "age_exh",
            f"{self.athlete.firstname} {self.athlete.lastname} {get_age(self.athlete)}: статус EXH (возраст {event[0][0]}-{event[0][1]})",
            extra={"age": get_age(self.athlete), "allowed": f"{event[0][0]}-{event[0][1]}"},
        )
        return event[1], EntryStatus.EXH

    def validate_entrytime(self):
        if self.row.entrytime.isoformat() == '00:00:00':
            return self.row.entrytime
        if not self.config['points']['enabled']:
            return self.row.entrytime

        point = bt.get_point(
            self.lenex.meet.course,
            self.athlete.gender,
            self.row.distance,
            self.stroke,
            get_only_time(self.row.entrytime)
        )
        if self.config['points']['max'] > point > self.config['points']['min']:
            return self.row.entrytime
        logger.warning(
            f'[{self.i}]: Нарушение политики очков ({point:.5f};{self.row.entrytime})')
        self._add_issue(
            "points_policy",
            f'Нарушение политики очков ({point:.5f};{self.row.entrytime})',
            extra={"points": round(point, 5), "entrytime": str(self.row.entrytime)},
        )
        return time()
