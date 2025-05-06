import datetime
import logging
import json
import urllib.parse
from sqlalchemy.orm import Query, MappedColumn

from arxiv_admin_api import datetime_to_epoch

logger = logging.getLogger(__name__)

class MuiDataGridFilter:
    def __init__(self, filter: str):
        self.datagrid_filter = None
        if filter:
            try:
                self.datagrid_filter = json.loads(urllib.parse.unquote(filter))
                logger.debug(f"datagrid_filter={self.datagrid_filter!r}")
            except Exception:
                logger.warning(f"datagrid_filter={filter}")
                pass

    @property
    def field_name(self) -> str | None:
        return self.datagrid_filter.get("field")

    @property
    def value(self) -> str | None:
        return self.datagrid_filter.get("value")

    def to_query(self, query: Query, field: MappedColumn) -> Query:
        op_name = self.datagrid_filter.get("operator")
        value = self.datagrid_filter.get("value")
        match op_name:
            case "contains":
                query = query.filter(field.contains(value))
            case "doesNotContain":
                query = query.filter(field.icontains(value))
            case "startsWith":
                query = query.filter(field.startswith(value))
            case "endsWith":
                query = query.filter(field.endswith(value))
            case "equals":
                query = query.filter(field == value)
            case "doesNotEqual":
                query = query.filter(field != value)
            case "is empty":
                query = query.filter(field == "")
            case "is not empty":
                query = query.filter(field != "")
            case "isAnyOf":
                pass
            case "between":
                if isinstance(value, list) and len(value) == 2:
                    defaults = [datetime.datetime(year=datetime.MINYEAR, month=1, day=1, hour=0, minute=0, second=0),
                                datetime.datetime(year=datetime.MAXYEAR, month=1, day=1, hour=0, minute=0, second=0)]
                    values = [datetime_to_epoch(datetime.datetime.fromisoformat(element), defaults[idx]) if element else datetime_to_epoch(None, defaults[idx]) for idx, element in enumerate(value)]
                    query = query.filter(field.between(values[0], values[1]))
        return query