import logging


def verbose(*messages):
    print(">>", " ".join(messages))

def setup_logger(level=20):
    """
        When running "bin/instance run ...", the logger level is 30 (warn).
        It is possible to set it to 20 (info) or 10 (debug).
    """
    if level == 30:
        return

    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logging.root.handlers:
        if handler.level == 30 and handler.formatter is not None:
            handler.level = level
            break