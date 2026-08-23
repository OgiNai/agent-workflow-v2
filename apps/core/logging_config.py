LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "": {  # root logger
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console_handler"],
        },
    },
    "handlers": {
        "console_handler": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "INFO",
            "formatter": "json_formatter",
        },
    },
    "filters": {},
    "formatters": {
        "json_formatter": {
            "()": "apps.observability.logging.JsonFormatter",
        },
    },
}
