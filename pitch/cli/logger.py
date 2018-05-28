import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

handler.setFormatter(
    logging.Formatter(
        '%(asctime)s process=%(process)d '
        'thread=%(thread)d name=%(name)s '
        'level=%(levelname)s %(message)s'
    )
)
