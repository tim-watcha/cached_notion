import logging
import coloredlogs


def setup_logger(name, level=logging.DEBUG):
    # Create a standard logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a custom ColoredFormatter
    formatter = coloredlogs.ColoredFormatter(
        fmt='%(asctime)s - %(levelname)s - File "%(pathname)s", line %(lineno)d -\n%(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        level_styles={
            'debug': {'color': 'cyan'},
            'info': {'color': 'green'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'color': 'red', 'bold': True},
        },
        field_styles={
            'asctime': {'color': 'blue'},
            'levelname': {'bold': True},
        }
    )

    # Apply the custom formatter to the logger
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)  # Set handler level to DEBUG
    logger.addHandler(handler)

    logger.propagate = False  # Prevent log messages from being propagated to the root logger

    return logger
