import logging

from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFORMAT = "%(log_color)s[Master HamsterKombat Bot]%(reset)s[%(log_color)s%(levelname)s%(reset)s] %(asctime)s %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(
    LOGFORMAT, "%Y-%m-%d %H:%M:%S"
)  # Specify the date/time format
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger("pythonConfig")
log.setLevel(LOG_LEVEL)
log.addHandler(stream)
