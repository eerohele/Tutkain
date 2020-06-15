import logging

log = logging.getLogger(__package__)
handler = logging.StreamHandler()

formatter = logging.Formatter(
    fmt='[%(name)s] [%(threadName)s] %(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
log.addHandler(handler)


def enable_debug():
    log.setLevel(logging.DEBUG)
