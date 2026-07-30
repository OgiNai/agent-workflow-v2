LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "": {  # root logger
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["file_handler"],
        },
    },
    "handlers": {
        "file_handler": {
            "class": "logging.FileHandler",
            "filename": "output.log",
            "mode": "w",
            "level": "DEBUG",
            "formatter": "default_formatter",
        },
    },
    "filters": {
    },
    "formatters": {
        "default_formatter": {
            "format": "%(asctime)s-%(levelname)s-%(name)s::%(module)s|%(lineno)s:: %(message)s",
        },
    },
}