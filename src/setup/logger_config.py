import logging
import logging.handlers
from pathlib import Path


class AgentLogger:

    def __init__(
        self,
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file: str = "agent.log",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "runtime.log"

        self.logger = logging.getLogger("AgentLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        self.logger.handlers.clear()

        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s\n%(filename)s @ %(funcName)s:%(lineno)d\n%(message)s"
        )
        simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

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
