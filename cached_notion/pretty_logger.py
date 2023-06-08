import logging
from pprint import PrettyPrinter

import coloredlogs


class PrettyLogger(logging.Logger):

    def pretty(self, *args, **kwargs):
        # Create a pretty-printer with the desired indentation
        pretty_printer = PrettyPrinter(width=160, compact=True)

        # Format the message, args, and kwargs
        formatted_msg = [pretty_printer.pformat(arg) for arg in args]

        def format_value(key, value):
            indent = " " * len(f"{key}: ")
            formatted = pretty_printer.pformat(value)
            formatted = formatted.replace("\n", "\n" + indent)
            return f"{key}: {formatted}"

        formatted_msg.extend([format_value(key, value) for key, value in kwargs.items()])

        # Join the formatted parts and log the message
        log_msg = "\n".join(formatted_msg)
        self.debug(log_msg, stacklevel=2)


def setup_logger(name, level=logging.DEBUG):
    # Register the custom logger class
    logging.setLoggerClass(PrettyLogger)

    # Create a logger with the specified name and level
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
