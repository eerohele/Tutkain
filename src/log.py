import logging


log = logging.getLogger(__package__)


def start_logging(debug=False):
    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        fmt="[%(name)s] [%(threadName)s] %(asctime)s.%(msecs)03d %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    log.addHandler(handler)

    log.setLevel(logging.DEBUG if debug else logging.INFO)


def stop_logging():
    log.handlers = []
