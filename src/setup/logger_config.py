import logging
import logging.handlers
from pathlib import Path


class AgentLogger:
    def __init__(
        self,
        log_dir: str,
        console_level: int,
        file_level: int,
        max_bytes: int,
        backup_count: int,
        log_file: str = "runtime.log",
    ) -> None:

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_file

        self.logger = logging.getLogger("AgentLogger")
        self.logger.setLevel(console_level)
        self.logger.propagate = False

        self.logger.handlers.clear()
        detailed_formatter = logging.Formatter(
            "%(asctime)s: %(funcName)s@%(lineno)d - %(levelname)s\t%(message)s"
        )
        simple_formatter = logging.Formatter("%(asctime)s: %(levelname)s\t%(message)s")

        # File Handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

    def get_log_file_path(self) -> str:
        return str(self.log_file)


def setup_logging(
    log_dir: str = "logs",
    console_level: int = logging.DEBUG,
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
