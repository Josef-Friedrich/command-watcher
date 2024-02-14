from stdout_stderr_capturing import Capturing

import command_watcher


class TestLogging:
    def setup_method(self) -> None:
        logger, handler = command_watcher.log.setup_logging()
        self.logger = logger
        self.handler = handler

    def test_initialisation(self) -> None:
        assert len(self.logger.name) == 36

    def test_log_stdout(self) -> None:
        self.logger.stdout("stdout")
        assert len(self.handler.buffer) == 1
        assert self.handler.buffer[0].msg == "stdout"
        assert self.handler.buffer[0].levelname == "STDOUT"

    def test_log_stderr(self) -> None:
        self.logger.stderr("stderr")
        assert len(self.handler.buffer) == 1
        assert self.handler.buffer[0].msg == "stderr"
        assert self.handler.buffer[0].levelname == "STDERR"

    def test_property_stdout(self) -> None:
        self.logger.stdout("line 1")
        self.logger.stdout("line 2")
        self.logger.stderr("stderr")
        assert self.handler.stdout == "line 1\nline 2"

    def test_property_stderr(self) -> None:
        self.logger.stderr("line 1")
        self.logger.stderr("line 2")
        self.logger.stdout("stdout")
        assert self.handler.stderr == "line 1\nline 2"

    def test_property_all_records(self) -> None:
        self.logger.stderr("stderr")
        self.logger.stdout("stdout")
        self.logger.error("error")
        self.logger.debug("debug")
        assert "stderr" in self.handler.all_records
        assert "stdout" in self.handler.all_records
        assert "error" in self.handler.all_records
        assert "debug" in self.handler.all_records


class TestColorizedPrint:
    def setup_method(self) -> None:
        self.logger, _ = command_watcher.log.setup_logging()

    def test_critical(self) -> None:
        with Capturing(stream="stderr") as output:
            self.logger.critical("CRITICAL 50")
        assert (
            output[0][20:] == "\x1b[1m\x1b[7m\x1b[31m CRITICAL "
            "\x1b[0m \x1b[1m\x1b[31mCRITICAL 50\x1b[0m"
        )

    def test_error(self) -> None:
        with Capturing(stream="stderr") as output:
            self.logger.error("ERROR 40")
        assert (
            output[0][20:] == "\x1b[7m\x1b[31m ERROR    \x1b[0m \x1b[31mERROR 40\x1b[0m"
        )

    def test_stderr(self) -> None:
        with Capturing(stream="stderr") as output:
            self.logger.stderr("STDERR 35")
        assert (
            output[0][20:] == "\x1b[2m\x1b[7m\x1b[31m STDERR   "
            "\x1b[0m \x1b[2m\x1b[31mSTDERR 35\x1b[0m"
        )

    def test_warning(self) -> None:
        with Capturing() as output:
            self.logger.warning("WARNING 30")
        assert (
            output[0][20:]
            == "\x1b[7m\x1b[33m WARNING  \x1b[0m \x1b[33mWARNING 30\x1b[0m"
        )

    def test_info(self) -> None:
        with Capturing() as output:
            self.logger.info("INFO 20")
        assert (
            output[0][20:] == "\x1b[7m\x1b[32m INFO     \x1b[0m \x1b[32mINFO 20\x1b[0m"
        )

    def test_debug(self) -> None:
        with Capturing() as output:
            self.logger.debug("DEBUG 10")
        assert (
            output[0][20:] == "\x1b[7m\x1b[37m DEBUG    \x1b[0m \x1b[37mDEBUG 10\x1b[0m"
        )

    def test_stdout(self) -> None:
        with Capturing() as output:
            self.logger.stdout("STDOUT 5")
        assert (
            output[0][20:] == "\x1b[2m\x1b[7m\x1b[37m STDOUT   \x1b[0m "
            "\x1b[2m\x1b[37mSTDOUT 5\x1b[0m"
        )

    def test_noset(self) -> None:
        with Capturing() as output:
            self.logger.log(1, "NOTSET 0")
        assert (
            output[0][20:] == "\x1b[7m\x1b[30m Level 1  \x1b[0m \x1b[30mNOTSET 0\x1b[0m"
        )
