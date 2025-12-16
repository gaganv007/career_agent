from setup.logger_config import setup_logging


def test_setup_logging_returns_configured_logger(tmp_path, monkeypatch):
    """
    Unit test for logger_config.setup_logging().

    Goal:
      - Call setup_logging() once
      - Verify we get a logger named 'AgentLogger'
      - Verify it has at least one file handler and one console/stream handler

    This should exercise the remaining lines in logger_config.py.
    """

    # If your setup_logging() takes optional log_dir/log_file, you can pass tmp_path here.
    # If it has no params, just call setup_logging() directly.
    # Example assuming no required args:
    logger = setup_logging()

    # Basic sanity checks
    assert logger.name == "AgentLogger"

    # There should be at least one handler
    assert len(logger.handlers) >= 1

    # Check that we have at least one FileHandler and one non-file handler (console)
    has_file_handler = any(
        getattr(h, "baseFilename", None) is not None for h in logger.handlers
    )
    has_stream_handler = any(
        h.__class__.__name__.endswith("StreamHandler") for h in logger.handlers
    )

    assert has_file_handler
    assert has_stream_handler
