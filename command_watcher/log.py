import logging
import sys
import time
import uuid
from logging.handlers import BufferingHandler
from typing import Any, List, Optional, Tuple, cast

import termcolor

# Logging #####################################################################

# CRITICAL 50
# ERROR 40
# -> STDERR 35
# WARNING 30
# INFO 20
# DEBUG 10
# --> STDOUT 5
# NOTSET 0
STDERR = 35
logging.addLevelName(STDERR, 'STDERR')
STDOUT = 5
logging.addLevelName(STDOUT, 'STDOUT')

LOGFMT = '%(asctime)s_%(msecs)03d %(levelname)s %(message)s'
DATEFMT = '%Y%m%d_%H%M%S'


class LoggingHandler(BufferingHandler):
    """Store of all logging records in the memory. Print all records on emit.
    """

    _master_logger:  Optional[logging.Logger]

    def __init__(self, master_logger: Optional[logging.Logger] = None):
        BufferingHandler.__init__(self, capacity=1000000)
        self._master_logger = master_logger

    @staticmethod
    def _print(record: logging.LogRecord) -> None:
        """
        :param logging.LogRecord record: A record object.
        """
        level = record.levelname
        # CRITICAL 50
        # ERROR 40
        # -> STDERR 35
        # WARNING 30
        # INFO 20
        # DEBUG 10
        # --> STDOUT 5
        # NOTSET 0
        attr = None
        if level == 'CRITICAL':
            color = 'red'
            attr = 'bold'
        elif level == 'ERROR':
            color = 'red'
        elif level == 'STDERR':
            color = 'red'
            attr = 'dark'
        elif level == 'WARNING':
            color = 'yellow'
        elif level == 'INFO':
            color = 'green'
        elif level == 'DEBUG':
            color = 'white'
        elif level == 'STDOUT':
            color = 'white'
            attr = 'dark'
        elif level == 'NOTSET':
            color = 'grey'
        else:
            color = 'grey'

        if attr:
            reverse = ['reverse', attr]
            normal = [attr]
        else:
            reverse = ['reverse']
            normal = []

        if record.levelno >= STDERR:
            stream = sys.stderr
        else:
            stream = sys.stdout

        created = '{}_{:03d}'.format(
            time.strftime(DATEFMT, time.localtime(record.created)),
            int(record.msecs),
        )

        print('{} {} {}'.format(
            created,
            termcolor.colored(' {:<8} '.format(level), color, attrs=reverse),
            termcolor.colored(record.msg, color, attrs=normal),
        ), file=stream)

    def emit(self, record: logging.LogRecord) -> None:
        """
        :param record: A record object.
        """
        self.buffer.append(record)
        if not self._master_logger:
            self._print(record)
        else:
            self._master_logger.log(record.levelno, record.msg)
        if self.shouldFlush(record):
            self.flush()

    @property
    def stdout(self) -> str:
        messages: List[str] = []
        for record in self.buffer:
            if record.levelname == 'STDOUT':
                messages.append(record.msg)
        return '\n'.join(messages)

    @property
    def stderr(self) -> str:
        messages: List[str] = []
        for record in self.buffer:
            if record.levelname == 'STDERR':
                messages.append(record.msg)
        return '\n'.join(messages)

    @property
    def all_records(self) -> str:
        """All log messages joined by line breaks."""
        messages: List[str] = []
        for record in self.buffer:
            messages.append(self.format(record))
        return '\n'.join(messages)


class ExtendedLogger(logging.Logger):

    def stdout(self, line: object, *args: Any, **kws: Any) -> None: ...
    def stderr(self, line: object, *args: Any, **kws: Any) -> None: ...


def _log_stdout(self: ExtendedLogger, message: object, *args: Any,
                **kws: Any) -> None:
    # Yes, logger takes its '*args' as 'args'.
    self._log(STDOUT, message, args, **kws)


extendedLogger: ExtendedLogger = cast(ExtendedLogger, logging.Logger)


extendedLogger.stdout = _log_stdout  # type: ignore


def _log_stderr(self: ExtendedLogger, message: object, *args: Any,
                **kws: Any) -> None:
    # Yes, logger takes its '*args' as 'args'.
    self._log(STDERR, message, args, **kws)


logging.Logger.stderr = _log_stderr  # type: ignore


def setup_logging(master_logger: Optional[logging.Logger] = None) -> \
        Tuple[ExtendedLogger, LoggingHandler]:
    """Setup a fresh logger for each watch action.

    :param master_logger: Forward all log messages to a master logger."""
    logger = logging.getLogger(name=str(uuid.uuid1()))
    formatter = logging.Formatter(fmt=LOGFMT, datefmt=DATEFMT)
    handler = LoggingHandler(master_logger=master_logger)
    handler.setFormatter(formatter)
    # Show all log messages: use 1 instead of 0: because:
    # From the documentation:
    # When a logger is created, the level is set to NOTSET (which causes all
    # messages to be processed when the logger is the root logger, or
    # delegation to the parent when the logger is a non-root logger). Note that
    # the root logger is created with level WARNING.
    logger.setLevel(1)
    logger.addHandler(handler)
    return (cast(ExtendedLogger, logger), handler)
