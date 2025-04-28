from datetime import date, datetime
import random
import re
from typing import TypeVar
from lenexpy.models.athelete import Athlete
from lenexpy.models.club import Club
from reg.exceptions import IncorrectGender
from reg.row_types import Row

T = TypeVar('T')


def randid() -> int:
    return random.randint(1_000_00, 10_000_00-1)


class AthleteParser:
    genders = {  # TODO: Add in cofnig
        'мужской': 'M',
        'женский': 'F',
        'мужчины': 'M',
        'женщины': 'F',
        'девочки': 'F',
        'мальчики': 'M',
        'юноши': 'M',
        'девушки': 'F',
    }

    def parse_bd(format: str, dt: str | datetime) -> date:
        if isinstance(dt, str):
            dt = datetime.strptime(dt, format)
        return dt.date()

    def parse_gender(gender: str) -> str:
        gender = gender.strip().lower()
        if gender not in AthleteParser.genders:
            raise IncorrectGender(gender)
        return AthleteParser.genders.get(gender)

    def _parse_license(config, license) -> str:
        def chg(match: re.Match):
            t = match.string[match.regs[0][0]:match.regs[0][1]]
            return t.lower()
        license = re.sub('[^I]{1}', chg, license)

        for a, b in config['replacement'].items():
            license = license.replace(a, b)
        return license

    def get_license(config: dict, license: str | None) -> str | None:
        if license is None:
            return None

        license = AthleteParser._parse_license(
            config,
            str(license)
        )
        if license in config['licenses']:
            return license


class BaseData:
    clubs: dict[str, Club]
    athletes: dict[str, Athlete]

    def __init__(self, config):
        self.clubs = {}
        self.athletes = {}
        self.config = config

    def _get_key(self, *args) -> T:
        return ';'.join(map(str, args)).lower()

    def get_athlete(self, club: Club, row: Row):
        key = self._get_key(row.firstname, row.lastname, row.middlename,
                            row.gender, row.birthday)

        if key not in self.athletes:
            athlete = Athlete(
                randid(),
                birthdate=AthleteParser.parse_bd(
                    self.config['birthday'], row.birthday),
                gender=AthleteParser.parse_gender(row.gender),
                firstname=row.firstname,
                lastname=row.lastname,
                license=AthleteParser.get_license(self.config, row.license)
            )
            club.athletes.append(athlete)
            self.athletes[key] = athlete
        else:
            athlete = self.athletes[key]

        return athlete

    def get_club(self, row: Row):
        key = self._get_key(row.club)

        if key not in self.clubs:
            club = Club(row.club, athletes=[])
            self.clubs[key] = club
        else:
            club = self.clubs[key]

        return club

    def get(self, row: Row):
        club = self.get_club(row)
        athl = self.get_athlete(club, row)
        return athl
