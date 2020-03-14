import logging
import os

class LoggerWrapper(logging.Logger):
    def __init__(self, name, level):
        super().__init__(name, level)

    def findCaller(self, stack_info=False, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = logging.currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            # 这里多找一次，因为代码中对 logging 做了一次封装
            f = f.f_back.f_back
        orig_f = f
        while f and stacklevel > 1:
            f = f.f_back
            stacklevel -= 1
        if not f:
            f = orig_f
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == logging._srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        return rv


class LoggingWrapper():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            formatter = logging.Formatter(
                '%(asctime)s %(filename)s[line:%(lineno)d] %(message)s')

            def _init_logger_(logger, level, file_name, formatter):
                fh_info = logging.FileHandler(file_name)
                fh_info.setLevel(level)
                fh_info.setFormatter(formatter)
                logger.addHandler(fh_info)

            # 初始化 info logger
            cls._info_logger = LoggerWrapper("info_log", logging.INFO)
            _init_logger_(cls._info_logger, logging.INFO,
                          "info.log", formatter)

            # 初始化 debug logger
            cls._debug_logger = LoggerWrapper("debug_log", logging.DEBUG)
            _init_logger_(cls._debug_logger, logging.DEBUG,
                          "debug.log", formatter)

            # 初始化 error logger
            cls._error_logger = LoggerWrapper("error_log", logging.ERROR)
            _init_logger_(cls._error_logger, logging.ERROR,
                          "error.log", formatter)

        return cls._instance


def log_info(log_content):
    LoggingWrapper()._info_logger.info(log_content)


def log_debug(log_content):
    LoggingWrapper()._debug_logger.debug(log_content)


def log_error(log_content):
    LoggingWrapper()._error_logger.error(log_content)
