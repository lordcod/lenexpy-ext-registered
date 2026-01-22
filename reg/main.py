from lenexpy import fromfile
from lenexpy.models.lenex import Lenex
from loguru import logger
import openpyxl
from reg.athlete_parser import BaseData
from reg.event_parser import RowParser
from reg.row_types import Row, RowValidate
import sys
from lenexpy.ext.basetime import BaseTime

sys.tracebacklimit = 2


class TranslatorLenex:
    def __init__(
        self,
        lxf_file: str,
        xlsx_file: str,
        config: dict,
        **kwargs
    ):
        self.__dict__.update(kwargs)
        self.lxf_file = lxf_file
        self.xlsx_file = xlsx_file
        self.config = config
        self.basedata = BaseData(config)

    def parse(self) -> Lenex:
        lenex = fromfile(self.lxf_file)
        workbook = openpyxl.load_workbook(self.xlsx_file)
        sheet = workbook.active

        logger.info(
            f'Обработка началась {lenex.meet.name}')

        RowValidate._init_config(self.config['location'])
        for i, r in enumerate(sheet.iter_rows(min_row=2), start=1):
            values = [v.value for v in r]
            if values[1] is None:
                continue

            if self.config.get('debug'):
                logger.debug(f'Обработка {i} строк: {values}')

            try:
                row = Row._init_row(sheet, values,  i)
                RowParser(row, i, lenex, self.config, self.basedata).parse()
            except Exception as exc:
                logger.exception(
                    f"Строка {i} пропущена из-за ошибки: [{type(exc).__name__}] {exc}")

        lenex.meet.clubs = list(self.basedata.clubs.values())

        logger.info(
            f'[BaseData] Clubs: {len(self.basedata.clubs)} '
            f'Athletes: {len(self.basedata.athletes)} '
            f'Entries: {sum([len(athl.entries) for athl in self.basedata.athletes.values()])}'
        )
        logger.info(
            f'[Lenex] Clubs: {len(lenex.meet.clubs)} '
            f'Athletes: {sum(len(c.athletes) for c in lenex.meet.clubs)} '
            f'Entries: {sum([len(a.entries) for c in lenex.meet.clubs for a in c.athletes])}'
        )

        for athl in self.basedata.athletes.values():
            events = []
            for ent in athl.entries:
                if ent.eventid in events:
                    logger.warning(
                        f'Дублированные записи: {athl.firstname} {athl.lastname}')
                events.append(ent.eventid)

        return lenex
