import logging
from pythonjsonlogger import jsonlogger
from asgi_correlation_id import CorrelationIdFilter

def setup_logger():
    logHandler = logging.StreamHandler()
    logHandler.addFilter(CorrelationIdFilter())
    formatter = jsonlogger.JsonFormatter('%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s %(message)s',
                                         rename_fields={'levelname': 'level', 'asctime': 'timestamp'})
    logHandler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
