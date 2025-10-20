import logging
import logging.handlers
from pathlib import Path


class AgentLogger:
    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    detailed_line_1 = "%(asctime)s - %(name)s - %(levelname)s"
    detailed_line_2 = "%(filename)s @ %(funcName)s:%(lineno)d\n%(message)s"
    detailed_formatter = logging.Formatter(f"{detailed_line_1}\n{detailed_line_2}")
    name = "AgentLogger"

    def __init__(
        self,
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file: str = "runtime.log",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_file

        self.logger = logging.getLogger(AgentLogger.name)
        self.logger.setLevel(console_level)
        self.logger.propagate = False

        self.logger.handlers.clear()

        line_1 = "%(asctime)s - %(name)s - %(levelname)s"
        line_2 = "%(filename)s @ %(funcName)s:%(lineno)d\n%(message)s"
        detailed_formatter = logging.Formatter(f"{line_1}\n{line_2}")

        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

    def get_log_file_path(self):
        return str(self.log_file)


def setup_logging(
    log_dir: str = "logs",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:

    agent_logger = AgentLogger(
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )
    return agent_logger.get_logger()