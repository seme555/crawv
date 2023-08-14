from __future__ import absolute_import, unicode_literals

import sys
import socket
import warnings
import crawv

from loguru import logger

from crawv.exceptions import CrawvDeprecationWarning
# from crawv.settings import Settings
from crawv.utils.tools import get_project_settings


def set_log_config(formatter: str, settings):
    _log_config = {
        "default": {
            "handlers": [
                {
                    "sink": sys.stdout,
                    "format": formatter,
                    "level": settings.get('LOG_LEVEL', "TRACE")
                }
            ],
            "extra": {
                "host": socket.gethostbyname(socket.gethostname()),
                'log_name': settings.get("BOT_NAME", 'default'),
                'type': 'None'
            },
            "levels": [
                dict(name="TRACE", icon="âœï¸", color="<cyan><bold>"),
                dict(name="DEBUG", icon="â„ï¸", color="<blue><bold>"),
                dict(name="INFO", icon="â™»ï¸", color="<bold>"),
                dict(name="SUCCESS", icon="âœ”ï¸", color="<green><bold>"),
                dict(name="WARNING", icon="âš ï¸", color="<yellow><bold>"),
                dict(name="ERROR", icon="âŒï¸", color="<red><bold>"),
                dict(name="CRITICAL", icon="â˜ ï¸", color="<RED><bold>"),
            ]
        }
    }
    if settings.get('LOG_FILE', False):
        _log_config['default']['handlers'].append({
            "sink": settings.get('LOG_FILENAME', __file__),
            "format": formatter,
            "level": settings.get('LOG_LEVEL', "DEBUG"),
            "rotation": settings.get("LOG_ROTATION", '1 week'),
            "retention": settings.get("LOG_RETENTION", '30 days'),
            'encoding': settings.get("LOG_ENCODING", "utf-8")
        })
    return _log_config


class LogFormatter(object):
    simple_formatter = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> ' \
                       '[<cyan>{name}</cyan>] ' \
                       '<level>{level.icon}{level}</level>: ' \
                       '<level>{message}</level> '

    default_formatter = '<green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> | ' \
                        '[<cyan>{extra[log_name]}</cyan>] <cyan>{module}</cyan>:<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | ' \
                        '<red>{extra[host]}</red> | ' \
                        '<level>{level.icon}{level: <5}</level> | ' \
                        '<level>{level.no}</level> | ' \
                        '<level>{extra[type]}</level> | ' \
                        '<level>{message}</level> '

    kafka_formatter = '{time:YYYY-MM-DD HH:mm:ss,SSS}| ' \
                      '[{extra[log_name]}] {module}:{name}:{function}:{line} | ' \
                      '{extra[host]} | ' \
                      '{process} | ' \
                      '{thread} | ' \
                      '{level: <5} | ' \
                      '{level.no} | ' \
                      '{extra[type]}| ' \
                      '{message} '

