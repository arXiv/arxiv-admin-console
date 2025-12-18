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
    logger.handlers.clear()
    logger.addHandler(logHandler)
    logger.setLevel(logging.DEBUG)

    # Suppress verbose loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger("hypercorn.access").handlers.clear()
    logging.getLogger("hypercorn.access").propagate = False

    # Suppress httpx client logs (Request/Response logs)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Suppress hypercorn error logs or ensure they use JSON
    logging.getLogger("hypercorn.error").setLevel(logging.WARNING)
