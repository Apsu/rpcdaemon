import logging

# Thin wrapper (not so) cleverly straddling logging.Logger namespace
class Logger():
    def __init__(
            self,
            name='logger',
            level='INFO',
            format='%(asctime)s  %(name)-10s %(levelname)-8s %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            path='logger.log',
            handler=None
    ):
        # Call super
        self.logger = logging.Logger(name, level)
        self.handler = handler if handler else logging.FileHandler(path)
        self.handler.setFormatter(logging.Formatter(format, datefmt))
        self.logger.addHandler(self.handler)
