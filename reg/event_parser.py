from datetime import date, time
import random
from typing import List, Optional, Tuple
from loguru import logger
from reg.athlete_parser import BaseData
from reg.exceptions import IncorrectAge, IncorrectDistance
from reg.row_types import Row
from lenexpy.models.lenex import Lenex
from lenexpy.models.agegroup import AgeGroup
from lenexpy.models.event import Event
from lenexpy.models.athelete import Athlete
from lenexpy.models.entry import Entry
from lenexpy.models.heat import Heat
from lenexpy.ext.basetime import BaseTime

bt = BaseTime('FINA_Points_Table_Base_Times.xlsx')


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
        basedata: BaseData
    ):
        self.row = row
        self.i = i
        self.lenex = lenex
        self.config = config
        self.basedata = basedata
        self.events = get_swimstyles(lenex)

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
                heat = Heat(heatid=heatid, number=self.row.heat,
                            order=self.row.heat, status="SEEDED")
                if not event.heats:
                    event.heats = []
                event.heats.append(heat)
        else:
            heatid = None

        entry = Entry(
            event.eventid,
            self.entrytime,
            status=status
        )
        if heatid and self.row.lane:
            entry.heatid = heatid
            entry.lane = self.row.lane

        self.athlete.entries.append(entry)

    def find_event(self) -> Tuple[Event, Optional[str]]:
        try:
            events = self.events[(self.athlete.gender,
                                  self.stroke, self.row.distance)]
        except KeyError:
            raise IncorrectDistance(', '.join((self.athlete.gender,
                                               self.stroke,
                                               str(self.row.distance))))

        if len(events) == 0:
            raise IncorrectDistance(', '.join((self.athlete.gender,
                                               self.stroke,
                                               str(self.row.distance))))

        for (min, max), e in events:
            if check_age(get_age(self.athlete), min, max):
                return e, None

        if not self.config.get('exh', True):
            raise IncorrectAge(
                'The EXH is disabled and the age is not appropriate')

        event = events[0]
        if len(events) > 1:
            logger.warning(
                f'[{self.i}]: Было найдено несколько одинаковых дистанций для EXH')

        logger.warning(
            f'[{self.i}]: {self.athlete.firstname} {self.athlete.lastname} {get_age(self.athlete)}, участвует в забеге со статусом EXH, потому что он не подходит для возраста ({event[0][0]}-{event[0][1]})')
        return event[1], 'EXH'

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
        return time()
