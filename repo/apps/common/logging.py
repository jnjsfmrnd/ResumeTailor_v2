from __future__ import annotations


def build_logging_config(*, production: bool = False) -> dict:
    formatter_name = "structured" if production else "verbose"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
            "structured": {
                "format": "%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter_name,
            }
        },
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "apps.metrics": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }